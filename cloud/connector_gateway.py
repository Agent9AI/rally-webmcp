"""Deny-by-default MCP gateway shared by Rally's cross-family workers."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import inspect
import json
import os
import re
import secrets
import subprocess
import time
import urllib.parse
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Any

import httpx
from google.auth import default as google_auth_default
from google.auth import load_credentials_from_file
from google.auth.exceptions import GoogleAuthError
from google.auth.transport.requests import Request as GoogleAuthRequest
from mcp import ClientSession
from mcp.client.auth import OAuthClientProvider, TokenStorage
from mcp.client.streamable_http import streamable_http_client
from mcp.server.fastmcp import FastMCP
from mcp.shared.auth import OAuthClientInformationFull, OAuthClientMetadata, OAuthToken

from connector_approvals import ApprovalError, consume, request_approval
from connector_credentials import (
    ConnectorCredentialError,
    ExternalBearerAuth,
    OAuthClientCredentials,
    OAuthTokenMaterial,
    ProfileKeychainStore,
)


class ConnectorGatewayError(RuntimeError):
    pass


MAX_DISCOVERY_PAGES = 20
MAX_TOOLS = 128
MAX_DISCOVERY_BYTES = 512 * 1024
MAX_TOOL_SCHEMA_BYTES = 64 * 1024
MAX_TOOL_DESCRIPTION_BYTES = 4 * 1024
MAX_ARGUMENT_BYTES = 256 * 1024
MAX_RESULT_BYTES = 1024 * 1024
MAX_RELAY_REQUEST_BYTES = 768 * 1024
MAX_RELAY_RESPONSE_BYTES = 1024 * 1024
MAX_IDENTITY_TOKEN_BYTES = 24 * 1024
TOOL_NAME = re.compile(r"^[A-Za-z0-9_.:/-]{1,160}$")
CONNECTOR_ID = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")
SERVICE_ACCOUNT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,126}@[A-Za-z0-9.-]{1,190}$")
HOSTED_AUTHORITY_SCHEMA = "rally.hosted-connector-authority/v1"


class KeychainTokenStorage(TokenStorage):
    """Keep OAuth material in macOS Keychain, never in Rally config or receipts."""

    def __init__(self, service: str):
        self.service = service

    def _read(self, account: str) -> str | None:
        try:
            result = subprocess.run(
                [
                    "/usr/bin/security",
                    "find-generic-password",
                    "-w",
                    "-s",
                    self.service,
                    "-a",
                    account,
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                timeout=15,
            )
        except (OSError, subprocess.SubprocessError):
            return None
        return result.stdout.strip() or None

    def _write(self, account: str, value: str) -> None:
        try:
            subprocess.run(
                [
                    "/usr/bin/security",
                    "add-generic-password",
                    "-U",
                    "-s",
                    self.service,
                    "-a",
                    account,
                    "-w",
                ],
                check=True,
                input=value + "\n",
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                text=True,
                timeout=15,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            raise ConnectorGatewayError(
                f"could not write OAuth state to macOS Keychain service {self.service}"
            ) from exc

    async def get_tokens(self) -> OAuthToken | None:
        value = await asyncio.to_thread(self._read, "tokens")
        return OAuthToken.model_validate_json(value) if value else None

    async def set_tokens(self, tokens: OAuthToken) -> None:
        await asyncio.to_thread(self._write, "tokens", tokens.model_dump_json())

    async def get_client_info(self) -> OAuthClientInformationFull | None:
        value = await asyncio.to_thread(self._read, "client")
        return OAuthClientInformationFull.model_validate_json(value) if value else None

    async def set_client_info(self, client_info: OAuthClientInformationFull) -> None:
        await asyncio.to_thread(self._write, "client", client_info.model_dump_json())


class RegisteredClientTokenStorage(TokenStorage):
    """Adapt Rally's profile Keychain record to the MCP SDK OAuth store."""

    def __init__(self, service: str, redirect_uri: str, scope: str | None = None):
        self.store = ProfileKeychainStore.from_namespaced_service(service)
        self.redirect_uri = redirect_uri
        self.scope = scope

    async def get_tokens(self) -> OAuthToken | None:
        material = await asyncio.to_thread(self.store.load_tokens)
        if material is None:
            return None
        expires_in = None
        if material.expires_at is not None:
            expires_in = max(0, round(material.expires_at - time.time()))
        return OAuthToken(
            access_token=material.access_token,
            refresh_token=material.refresh_token,
            token_type="Bearer",
            expires_in=expires_in,
            scope=material.scope,
        )

    async def set_tokens(self, tokens: OAuthToken) -> None:
        expires_at = time.time() + tokens.expires_in if tokens.expires_in is not None else None
        await asyncio.to_thread(
            self.store.save_tokens,
            OAuthTokenMaterial(
                access_token=tokens.access_token,
                refresh_token=tokens.refresh_token,
                expires_at=expires_at,
                scope=tokens.scope,
            ),
        )

    async def get_client_info(self) -> OAuthClientInformationFull | None:
        client = await asyncio.to_thread(self.store.load_client)
        if client is None:
            return None
        return OAuthClientInformationFull(
            redirect_uris=[self.redirect_uri],
            token_endpoint_auth_method=("client_secret_post" if client.client_secret else "none"),
            grant_types=["authorization_code", "refresh_token"],
            response_types=["code"],
            scope=self.scope,
            client_name="Rally connector gateway",
            software_id="https://github.com/Agent9AI/rally",
            software_version="0.1.0",
            client_id=client.client_id,
            client_secret=client.client_secret,
        )

    async def set_client_info(self, client_info: OAuthClientInformationFull) -> None:
        if not client_info.client_id:
            raise ConnectorGatewayError("OAuth server returned no client ID")
        await asyncio.to_thread(
            self.store.save_client,
            OAuthClientCredentials(client_info.client_id, client_info.client_secret),
        )


def load_authority(path: str | None = None) -> dict[str, Any]:
    policy_path = path or os.environ.get("RALLY_CONNECTOR_POLICY", "")
    if not policy_path:
        raise ConnectorGatewayError("RALLY_CONNECTOR_POLICY is not set")
    try:
        with open(policy_path) as handle:
            authority = json.load(handle)
    except (OSError, ValueError) as exc:
        raise ConnectorGatewayError(f"cannot read connector authority: {exc}") from exc
    if not isinstance(authority, dict):
        raise ConnectorGatewayError("unsupported connector authority schema")
    schema = authority.get("schema_version")
    if schema not in {"rally.connector-authority/v1", HOSTED_AUTHORITY_SCHEMA}:
        raise ConnectorGatewayError("unsupported connector authority schema")
    if authority.get("default_decision") != "deny":
        raise ConnectorGatewayError("connector authority must default to deny")
    if schema == HOSTED_AUTHORITY_SCHEMA:
        _validate_hosted_authority(authority)
    return authority


def _is_hosted_authority(authority: dict[str, Any]) -> bool:
    return authority.get("schema_version") == HOSTED_AUTHORITY_SCHEMA


def _validate_relay_url(value: Any, *, label: str) -> str:
    if not isinstance(value, str) or not value or len(value) > 2048:
        raise ConnectorGatewayError(f"hosted connector {label} is invalid")
    try:
        parsed = urllib.parse.urlsplit(value)
    except ValueError as exc:
        raise ConnectorGatewayError(f"hosted connector {label} is invalid") from exc
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path not in {"", "/"}
        or parsed.query
        or parsed.fragment
    ):
        raise ConnectorGatewayError(f"hosted connector {label} is invalid")
    return value.rstrip("/")


def _validate_hosted_authority(authority: dict[str, Any]) -> None:
    run_id = authority.get("run_id")
    if not isinstance(run_id, str) or not run_id or len(run_id) > 256:
        raise ConnectorGatewayError("hosted connector authority has an invalid run ID")
    relay = authority.get("relay")
    if not isinstance(relay, dict) or set(relay) != {
        "url",
        "audience",
        "identity_service_account",
    }:
        raise ConnectorGatewayError("hosted connector relay configuration is invalid")
    relay_url = _validate_relay_url(relay.get("url"), label="relay URL")
    audience = _validate_relay_url(relay.get("audience"), label="relay audience")
    if relay_url != audience:
        raise ConnectorGatewayError("hosted connector relay audience is invalid")
    service_account = relay.get("identity_service_account")
    if not isinstance(service_account, str) or not SERVICE_ACCOUNT.fullmatch(service_account):
        raise ConnectorGatewayError("hosted connector relay identity is invalid")

    signed = authority.get("hosted_run_authority")
    if (
        not isinstance(signed, dict)
        or signed.get("schema") != "rally.hosted-run-authority/v1"
        or signed.get("run_id") != run_id
        or signed.get("default_decision") != "deny"
        or not isinstance(signed.get("signature"), str)
        or not re.fullmatch(r"[0-9a-f]{64}", signed["signature"])
        or not isinstance(signed.get("grants"), list)
    ):
        raise ConnectorGatewayError("hosted run authority is invalid")
    signed_grants: dict[str, set[str]] = {}
    for grant in signed["grants"]:
        if not isinstance(grant, dict) or not isinstance(grant.get("connector_id"), str):
            raise ConnectorGatewayError("hosted run authority is invalid")
        connector_id = grant["connector_id"]
        certified_tools = grant.get("certified_tools")
        if (
            connector_id in signed_grants
            or not CONNECTOR_ID.fullmatch(connector_id)
            or not isinstance(certified_tools, list)
        ):
            raise ConnectorGatewayError("hosted run authority is invalid")
        names: set[str] = set()
        for tool in certified_tools:
            if (
                not isinstance(tool, list)
                or len(tool) != 2
                or not isinstance(tool[0], str)
                or not TOOL_NAME.fullmatch(tool[0])
                or not isinstance(tool[1], str)
                or not re.fullmatch(r"[0-9a-f]{64}", tool[1])
                or tool[0] in names
            ):
                raise ConnectorGatewayError("hosted run authority is invalid")
            names.add(tool[0])
        signed_grants[connector_id] = names

    connectors = authority.get("connectors")
    if not isinstance(connectors, list) or len(connectors) > MAX_TOOLS:
        raise ConnectorGatewayError("hosted connector list is invalid")
    seen: set[str] = set()
    for connector in connectors:
        if not isinstance(connector, dict):
            raise ConnectorGatewayError("hosted connector list is invalid")
        connector_id = connector.get("id")
        if (
            not isinstance(connector_id, str)
            or not CONNECTOR_ID.fullmatch(connector_id)
            or connector_id in seen
            or connector.get("mode") != "hosted"
            or any(key in connector for key in ("endpoint", "dispatch", "auth"))
        ):
            raise ConnectorGatewayError("hosted connector list is invalid")
        policy = connector.get("tool_policy")
        if not isinstance(policy, dict) or not policy or len(policy) > MAX_TOOLS:
            raise ConnectorGatewayError("hosted connector tool policy is invalid")
        if connector_id not in signed_grants or set(policy) != signed_grants[connector_id]:
            raise ConnectorGatewayError("hosted connector tool policy is not frozen")
        for tool_name, rule in policy.items():
            if (
                not isinstance(tool_name, str)
                or not TOOL_NAME.fullmatch(tool_name)
                or not isinstance(rule, dict)
                or rule.get("risk") != "read"
            ):
                raise ConnectorGatewayError("hosted connector tool policy is invalid")
            constraints = rule.get("constraints")
            if not isinstance(constraints, dict):
                raise ConnectorGatewayError("hosted connector tool policy is invalid")
            argument_limit = constraints.get("max_argument_bytes")
            result_limit = constraints.get("max_result_bytes")
            if (
                isinstance(argument_limit, bool)
                or not isinstance(argument_limit, int)
                or argument_limit <= 0
                or argument_limit > MAX_ARGUMENT_BYTES
                or isinstance(result_limit, bool)
                or not isinstance(result_limit, int)
                or result_limit <= 0
                or result_limit > MAX_RESULT_BYTES
            ):
                raise ConnectorGatewayError("hosted connector tool policy is invalid")
        seen.add(connector_id)


def connector_by_id(authority: dict[str, Any], connector_id: str) -> dict[str, Any]:
    for connector in authority.get("connectors") or []:
        if connector.get("id") == connector_id:
            return connector
    raise ConnectorGatewayError(f"connector {connector_id} is not enabled for this run")


def _google_headers(auth: dict[str, Any]) -> dict[str, str]:
    try:
        scopes = auth.get("scopes") or ["https://www.googleapis.com/auth/cloud-platform"]
        credential_file = auth.get("credential_file")
        if credential_file:
            credentials, _ = load_credentials_from_file(
                os.path.abspath(os.path.expanduser(credential_file)), scopes=scopes
            )
        else:
            credentials, _ = google_auth_default(scopes=scopes)
        if not credentials.valid:
            credentials.refresh(GoogleAuthRequest())
    except (GoogleAuthError, OSError, ValueError) as exc:
        raise ConnectorGatewayError(
            "Google Application Default Credentials could not be refreshed"
        ) from exc
    if not credentials.token:
        raise ConnectorGatewayError("Google Application Default Credentials returned no token")
    headers = {"Authorization": "Bearer " + credentials.token}
    quota_project = getattr(credentials, "quota_project_id", None)
    if quota_project:
        headers["x-goog-user-project"] = quota_project
    return headers


async def _not_interactive(_: str) -> None:
    raise ConnectorGatewayError(
        "connector OAuth is not authorized; run './bin/rally connectors auth <id>'"
    )


async def _no_callback() -> tuple[str, str | None]:
    raise ConnectorGatewayError("interactive OAuth is disabled inside an agent run")


def oauth_provider(
    connector: dict[str, Any],
    redirect_uri: str = "http://127.0.0.1:8765/callback",
    redirect_handler: Any = _not_interactive,
    callback_handler: Any = _no_callback,
) -> OAuthClientProvider:
    auth = connector.get("auth") or {}
    service = auth.get("keychain_service")
    if not service:
        raise ConnectorGatewayError("{} has no OAuth Keychain service".format(connector["id"]))
    scope = " ".join(auth.get("scopes") or []) or None
    metadata = OAuthClientMetadata(
        redirect_uris=[redirect_uri],
        token_endpoint_auth_method="none",
        grant_types=["authorization_code", "refresh_token"],
        response_types=["code"],
        client_name="Rally connector gateway",
        software_id="https://github.com/Agent9AI/rally",
        software_version="0.1.0",
        scope=scope,
    )
    storage: TokenStorage
    if auth.get("registration") == "pre_registered":
        storage = RegisteredClientTokenStorage(service, redirect_uri, scope)
    else:
        storage = KeychainTokenStorage(service)
    return OAuthClientProvider(
        connector["endpoint"],
        metadata,
        storage,
        redirect_handler=redirect_handler,
        callback_handler=callback_handler,
    )


@asynccontextmanager
async def remote_session(
    connector: dict[str, Any],
    oauth_handlers: tuple[Any, Any, str] | None = None,
    endpoint_override: str | None = None,
) -> AsyncIterator[ClientSession]:
    endpoint = endpoint_override or connector.get("endpoint")
    if not endpoint:
        raise ConnectorGatewayError(
            "{} needs an endpoint before it can connect".format(connector.get("id", "connector"))
        )
    auth = connector.get("auth") or {}
    auth_type = auth.get("type")
    client_kwargs: dict[str, Any] = {
        "timeout": httpx.Timeout(30.0, read=90.0),
        # Provider endpoints are pinned by the catalog. Following a redirect could
        # forward credentials across the boundary or turn configuration into SSRF.
        "follow_redirects": False,
    }
    if auth_type == "google_adc":
        client_kwargs["headers"] = await asyncio.to_thread(_google_headers, auth)
    elif auth_type == "oauth_2_1":
        oauth_connector = {**connector, "endpoint": endpoint}
        if oauth_handlers:
            redirect_handler, callback_handler, redirect_uri = oauth_handlers
            client_kwargs["auth"] = oauth_provider(
                oauth_connector, redirect_uri, redirect_handler, callback_handler
            )
        else:
            client_kwargs["auth"] = oauth_provider(oauth_connector)
    elif auth_type == "external_bearer":
        service = auth.get("keychain_service")
        if not service:
            raise ConnectorGatewayError(f"{connector['id']} has no credential service")
        store = ProfileKeychainStore.from_namespaced_service(service)
        if connector["id"] == "github":
            toolsets = tuple(auth.get("toolsets") or ())
            client_kwargs["auth"] = (
                ExternalBearerAuth.for_github(store, toolsets=toolsets)
                if toolsets
                else ExternalBearerAuth.for_github(store)
            )
        else:
            client_kwargs["auth"] = ExternalBearerAuth(store)
    else:
        raise ConnectorGatewayError("unsupported auth type for {}".format(connector["id"]))

    try:
        async with (
            httpx.AsyncClient(**client_kwargs) as http_client,
            streamable_http_client(endpoint, http_client=http_client, terminate_on_close=True) as (
                read_stream,
                write_stream,
                _,
            ),
            ClientSession(read_stream, write_stream) as session,
        ):
            await session.initialize()
            yield session
    except (ConnectorCredentialError, ConnectorGatewayError):
        raise
    except Exception as exc:
        raise ConnectorGatewayError(
            "{} connection failed: {}".format(connector["id"], str(exc)[:500])
        ) from exc


async def _discover_single_endpoint(
    connector: dict[str, Any], oauth_handlers: tuple[Any, Any, str] | None = None
) -> list[dict[str, Any]]:
    tools: list[dict[str, Any]] = []
    names: set[str] = set()
    aggregate_bytes = 0
    pages = 0
    cursor: str | None = None
    async with remote_session(connector, oauth_handlers) as session:
        while True:
            pages += 1
            if pages > MAX_DISCOVERY_PAGES:
                raise ConnectorGatewayError(
                    "{} exceeded Rally's discovery page limit".format(connector["id"])
                )
            result = await session.list_tools(cursor=cursor)
            for tool in result.tools:
                name = str(tool.name)
                description = str(tool.description or "")
                schema = tool.inputSchema or {}
                if not TOOL_NAME.fullmatch(name):
                    raise ConnectorGatewayError(
                        "{} returned an invalid tool name".format(connector["id"])
                    )
                if name in names:
                    raise ConnectorGatewayError(
                        "{} returned duplicate tool {}".format(connector["id"], name)
                    )
                if len(description.encode()) > MAX_TOOL_DESCRIPTION_BYTES:
                    raise ConnectorGatewayError(
                        "{}.{} description exceeds Rally's limit".format(connector["id"], name)
                    )
                if len(json.dumps(schema, separators=(",", ":")).encode()) > MAX_TOOL_SCHEMA_BYTES:
                    raise ConnectorGatewayError(
                        "{}.{} schema exceeds Rally's limit".format(connector["id"], name)
                    )
                item = {
                    "name": name,
                    "title": tool.title,
                    "description": description,
                    "input_schema": schema,
                }
                aggregate_bytes += len(
                    json.dumps(item, sort_keys=True, default=str, separators=(",", ":")).encode()
                )
                if aggregate_bytes > MAX_DISCOVERY_BYTES:
                    raise ConnectorGatewayError(
                        "{} tool catalog exceeds Rally's size limit".format(connector["id"])
                    )
                names.add(name)
                tools.append(item)
                if len(tools) > MAX_TOOLS:
                    raise ConnectorGatewayError(
                        "{} returned more than {} tools".format(connector["id"], MAX_TOOLS)
                    )
            cursor = result.nextCursor
            if not cursor:
                break
    return tools


async def discover_tools(
    connector: dict[str, Any], oauth_handlers: tuple[Any, Any, str] | None = None
) -> list[dict[str, Any]]:
    """Discover one connector, qualifying tool names for bundled providers."""
    dispatch = connector.get("dispatch") or {}
    if dispatch.get("strategy") != "tool_prefix":
        return await _discover_single_endpoint(connector, oauth_handlers)
    services = dispatch.get("services") or {}
    if not isinstance(services, dict) or not services or len(services) > 16:
        raise ConnectorGatewayError(f"{connector['id']} has an invalid service bundle")
    separator = dispatch.get("separator", ".")
    if separator != ".":
        raise ConnectorGatewayError(f"{connector['id']} has an invalid dispatch separator")
    tools: list[dict[str, Any]] = []
    names: set[str] = set()
    aggregate_bytes = 0
    for service_index, (service, endpoint) in enumerate(services.items()):
        if not TOOL_NAME.fullmatch(str(service)):
            raise ConnectorGatewayError(f"{connector['id']} has an invalid service name")
        target = {**connector, "endpoint": endpoint, "dispatch": {"strategy": "single"}}
        discovered = await _discover_single_endpoint(
            target, oauth_handlers if service_index == 0 else None
        )
        for tool in discovered:
            public_name = f"{service}.{tool['name']}"
            if public_name in names or not TOOL_NAME.fullmatch(public_name):
                raise ConnectorGatewayError(
                    f"{connector['id']} returned an invalid or duplicate bundled tool"
                )
            item = {**tool, "name": public_name}
            aggregate_bytes += len(
                json.dumps(item, sort_keys=True, default=str, separators=(",", ":")).encode()
            )
            if aggregate_bytes > MAX_DISCOVERY_BYTES or len(tools) >= MAX_TOOLS:
                raise ConnectorGatewayError(
                    f"{connector['id']} bundled tool catalog exceeds Rally's limit"
                )
            names.add(public_name)
            tools.append(item)
    return tools


def _dispatch_tool(connector: dict[str, Any], public_tool_name: str) -> tuple[dict[str, Any], str]:
    dispatch = connector.get("dispatch") or {}
    if dispatch.get("strategy") != "tool_prefix":
        return connector, public_tool_name
    service, separator, remote_tool = public_tool_name.partition(".")
    endpoint = (dispatch.get("services") or {}).get(service)
    if separator != "." or not endpoint or not remote_tool:
        raise ConnectorGatewayError(
            f"{connector['id']}.{public_tool_name} has no pinned service route"
        )
    target = {**connector, "endpoint": endpoint, "dispatch": {"strategy": "single"}}
    return target, remote_tool


def _json_hash(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, default=str, separators=(",", ":"))
    return hashlib.sha256(encoded.encode()).hexdigest()


def _constraint_failure(rule: dict[str, Any], arguments: dict[str, Any]) -> str | None:
    constraints = rule.get("constraints") or {}
    for name, constraint in (constraints.get("arguments") or {}).items():
        present = name in arguments
        if constraint.get("required") and not present:
            return "required_argument_missing"
        if not present:
            continue
        value = arguments[name]
        if "allowed_values" in constraint and value not in constraint["allowed_values"]:
            return "argument_outside_allowlist"
        if "max_length" in constraint and (
            not isinstance(value, (str, list, dict)) or len(value) > constraint["max_length"]
        ):
            return "argument_too_long"
    return None


def _receipt(authority: dict[str, Any], value: dict[str, Any]) -> None:
    path = authority.get("receipt_path")
    if not path:
        return
    record = {
        "at": datetime.now(UTC).isoformat(),
        "run_id": authority.get("run_id"),
        "actor": os.environ.get("RALLY_ACTOR", "unknown"),
        **value,
    }
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")


def public_connector_list(authority: dict[str, Any]) -> dict[str, Any]:
    return {
        "default_decision": authority["default_decision"],
        "connectors": [
            {
                "id": item["id"],
                "name": item["name"],
                "ready": bool(
                    item.get("endpoint")
                    or item.get("dispatch")
                    or (_is_hosted_authority(authority) and item.get("mode") == "hosted")
                ),
                "allowed_tools": sorted(
                    name
                    for name, rule in (item.get("tool_policy") or {}).items()
                    if rule.get("risk") == "read"
                ),
            }
            for item in authority.get("connectors") or []
        ],
    }


def frozen_hosted_tools(connector: dict[str, Any]) -> list[dict[str, Any]]:
    """Expose only tools frozen into a hosted run; never query a provider."""

    policy = connector.get("tool_policy") or {}
    return [
        {
            "name": name,
            "title": None,
            "description": "Certified read-only company-system tool.",
            "input_schema": {"type": "object", "additionalProperties": True},
            "allowed": True,
            "risk": "read",
        }
        for name, rule in sorted(policy.items())
        if isinstance(rule, dict) and rule.get("risk") == "read"
    ]


async def _mint_relay_identity_token(audience: str, service_account: str) -> str:
    try:
        from runner_oidc import mint_runner_identity_token
    except (ImportError, AttributeError) as exc:
        raise ConnectorGatewayError("hosted connector relay identity is unavailable") from exc
    try:
        if inspect.iscoroutinefunction(mint_runner_identity_token):
            token = await mint_runner_identity_token(audience, service_account)
        else:
            token = await asyncio.to_thread(mint_runner_identity_token, audience, service_account)
            if inspect.isawaitable(token):
                token = await token
    except Exception as exc:
        raise ConnectorGatewayError("hosted connector relay identity could not be minted") from exc
    if (
        not isinstance(token, str)
        or not token
        or len(token.encode("utf-8")) > MAX_IDENTITY_TOKEN_BYTES
        or any(character.isspace() for character in token)
    ):
        raise ConnectorGatewayError("hosted connector relay identity is invalid")
    return token


def _relay_http_client() -> httpx.AsyncClient:
    return httpx.AsyncClient(
        timeout=httpx.Timeout(30.0, read=90.0),
        follow_redirects=False,
    )


async def _bounded_response_bytes(response: httpx.Response) -> bytes:
    content_length = response.headers.get("content-length")
    if content_length is not None:
        try:
            declared = int(content_length)
        except ValueError as exc:
            raise ConnectorGatewayError("hosted connector relay response is malformed") from exc
        if declared < 0 or declared > MAX_RELAY_RESPONSE_BYTES:
            raise ConnectorGatewayError("hosted connector relay response is too large")
    body = bytearray()
    async for chunk in response.aiter_bytes():
        body.extend(chunk)
        if len(body) > MAX_RELAY_RESPONSE_BYTES:
            raise ConnectorGatewayError("hosted connector relay response is too large")
    return bytes(body)


def _strict_json_object(data: bytes) -> dict[str, Any]:
    def no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate JSON key")
            result[key] = value
        return result

    try:
        decoded = data.decode("utf-8")
        value = json.loads(decoded, object_pairs_hook=no_duplicates)
    except (UnicodeDecodeError, ValueError) as exc:
        raise ConnectorGatewayError("hosted connector relay response is malformed") from exc
    if not isinstance(value, dict):
        raise ConnectorGatewayError("hosted connector relay response is malformed")
    return value


async def _call_hosted_relay(
    authority: dict[str, Any],
    connector_id: str,
    tool_name: str,
    arguments: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    relay = authority["relay"]
    token = await _mint_relay_identity_token(relay["audience"], relay["identity_service_account"])
    request = {
        "authority": authority["hosted_run_authority"],
        "run_id": authority["run_id"],
        "call_id": secrets.token_hex(16),
        "tool_name": tool_name,
        "arguments": arguments,
    }
    try:
        encoded = json.dumps(
            request, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ConnectorGatewayError("hosted connector relay arguments are invalid") from exc
    if len(encoded) > MAX_RELAY_REQUEST_BYTES:
        raise ConnectorGatewayError("hosted connector relay request is too large")
    endpoint = relay["url"] + "/v1/internal/run-connectors/" + connector_id + ":invoke"
    headers = {
        "Authorization": "Bearer " + token,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    try:
        async with (
            _relay_http_client() as client,
            client.stream("POST", endpoint, content=encoded, headers=headers) as response,
        ):
            body = await _bounded_response_bytes(response)
            status = response.status_code
            content_type = response.headers.get("content-type", "").partition(";")[0].strip()
    except ConnectorGatewayError:
        raise
    except (httpx.HTTPError, OSError) as exc:
        raise ConnectorGatewayError("hosted connector relay request failed") from exc
    if status < 200 or status >= 300:
        raise ConnectorGatewayError(f"hosted connector relay returned HTTP {status}")
    if content_type.casefold() != "application/json":
        raise ConnectorGatewayError("hosted connector relay response is malformed")
    value = _strict_json_object(body)
    if set(value) != {"payload", "receipt"}:
        raise ConnectorGatewayError("hosted connector relay response is malformed")
    payload = value["payload"]
    receipt = value["receipt"]
    if not isinstance(payload, dict) or not isinstance(receipt, dict):
        raise ConnectorGatewayError("hosted connector relay response is malformed")
    return payload, receipt


async def call_allowed_tool(
    authority: dict[str, Any],
    connector_id: str,
    tool_name: str,
    arguments: dict[str, Any] | None = None,
    approval_id: str | None = None,
) -> dict[str, Any]:
    connector = connector_by_id(authority, connector_id)
    rule = (connector.get("tool_policy") or {}).get(tool_name)
    if not rule or rule.get("risk") == "deny":
        _receipt(
            authority,
            {
                "connector_id": connector_id,
                "tool": tool_name,
                "risk": (rule or {}).get("risk", "deny"),
                "decision": "denied",
                "arguments_sha256": _json_hash(arguments or {}),
                "reason": "not_allowlisted",
            },
        )
        raise ConnectorGatewayError(
            f"{connector_id}.{tool_name} is not on this run's tool allowlist"
        )
    if arguments is not None and not isinstance(arguments, dict):
        raise ConnectorGatewayError(f"{connector_id}.{tool_name} arguments must be an object")
    args = arguments or {}
    risk = rule.get("risk")
    started = time.monotonic()
    argument_bytes = len(json.dumps(args, sort_keys=True, default=str).encode())
    constraints = rule.get("constraints") or {}
    argument_limit = min(
        int(constraints.get("max_argument_bytes", MAX_ARGUMENT_BYTES)), MAX_ARGUMENT_BYTES
    )
    constraint_failure = _constraint_failure(rule, args)
    if argument_bytes > argument_limit or constraint_failure:
        reason = constraint_failure or "arguments_too_large"
        _receipt(
            authority,
            {
                "connector_id": connector_id,
                "tool": tool_name,
                "risk": risk,
                "decision": "denied",
                "arguments_sha256": _json_hash(args),
                "argument_bytes": argument_bytes,
                "reason": reason,
            },
        )
        raise ConnectorGatewayError(
            f"{connector_id}.{tool_name} arguments violate Rally policy: {reason}"
        )
    if risk == "verify_first":
        _receipt(
            authority,
            {
                "connector_id": connector_id,
                "tool": tool_name,
                "risk": risk,
                "decision": "denied",
                "arguments_sha256": _json_hash(args),
                "reason": "independent_pre_execution_verifier_unavailable",
            },
        )
        raise ConnectorGatewayError(
            f"{connector_id}.{tool_name} requires independent pre-execution verification"
        )
    approval_receipt: dict[str, Any] | None = None
    if risk == "human_approval":
        approval_path = authority.get("approval_path")
        if not approval_path or not (authority.get("policy") or {}).get(
            "human_approval_tools_enabled"
        ):
            raise ConnectorGatewayError("human approval is not enabled for this run")
        try:
            if approval_id is None:
                pending = request_approval(
                    approval_path,
                    run_id=authority["run_id"],
                    connector_id=connector_id,
                    tool_name=tool_name,
                    arguments=args,
                )
                _receipt(
                    authority,
                    {
                        "connector_id": connector_id,
                        "tool": tool_name,
                        "risk": risk,
                        "decision": "pending_approval",
                        "arguments_sha256": _json_hash(args),
                        "approval_id": pending["approval_id"],
                        "reason": "human_approval_required",
                    },
                )
                raise ConnectorGatewayError(
                    f"{connector_id}.{tool_name} requires human approval "
                    f"{pending['approval_id']} before execution"
                )
            approval_receipt = consume(
                approval_path,
                approval_id,
                run_id=authority["run_id"],
                connector_id=connector_id,
                tool_name=tool_name,
                arguments=args,
            )
        except ApprovalError as exc:
            _receipt(
                authority,
                {
                    "connector_id": connector_id,
                    "tool": tool_name,
                    "risk": risk,
                    "decision": "denied",
                    "arguments_sha256": _json_hash(args),
                    "approval_id": approval_id,
                    "reason": type(exc).__name__,
                },
            )
            raise ConnectorGatewayError(
                f"{connector_id}.{tool_name} approval was refused: {exc}"
            ) from exc
    try:
        if _is_hosted_authority(authority):
            payload, relay_receipt = await _call_hosted_relay(
                authority, connector_id, tool_name, args
            )
            result_is_error = payload.get("isError") is True
        else:
            remote_connector, remote_tool = _dispatch_tool(connector, tool_name)
            async with remote_session(remote_connector) as session:
                result = await session.call_tool(remote_tool, args)
            payload = result.model_dump(mode="json", by_alias=True, exclude_none=True)
            relay_receipt = None
            result_is_error = bool(result.isError)
        result_bytes = len(json.dumps(payload, default=str, separators=(",", ":")).encode())
        result_limit = min(
            int(constraints.get("max_result_bytes", MAX_RESULT_BYTES)), MAX_RESULT_BYTES
        )
        if result_bytes > result_limit:
            raise ConnectorGatewayError(
                f"{connector_id}.{tool_name} result exceeds Rally's size limit"
            )
        _receipt(
            authority,
            {
                "connector_id": connector_id,
                "tool": tool_name,
                "risk": risk,
                "decision": "allowed",
                "arguments_sha256": _json_hash(args),
                "result_sha256": _json_hash(payload),
                "result_is_error": result_is_error,
                "argument_bytes": argument_bytes,
                "result_bytes": result_bytes,
                "duration_ms": round((time.monotonic() - started) * 1000),
                **(
                    {"relay_receipt_sha256": _json_hash(relay_receipt)}
                    if relay_receipt is not None
                    else {}
                ),
                **({"approval_id": approval_receipt["approval_id"]} if approval_receipt else {}),
            },
        )
        return payload
    except Exception as exc:
        _receipt(
            authority,
            {
                "connector_id": connector_id,
                "tool": tool_name,
                "risk": risk,
                "decision": "failed",
                "arguments_sha256": _json_hash(args),
                "error_type": type(exc).__name__,
                "duration_ms": round((time.monotonic() - started) * 1000),
            },
        )
        raise


mcp = FastMCP(
    "Rally connectors",
    instructions=(
        "A run-scoped, deny-by-default gateway. Discover enabled connectors and "
        "their remote tools, then call only tools explicitly allowed by Rally policy."
    ),
)


@mcp.tool(name="rally_connector_list")
def gateway_list() -> dict[str, Any]:
    """List connectors and allowed tools frozen into this Rally run."""
    return public_connector_list(load_authority())


@mcp.tool(name="rally_connector_tools")
async def gateway_tools(connector_id: str) -> dict[str, Any]:
    """List a run-enabled connector's tools without executing one."""
    authority = load_authority()
    connector = connector_by_id(authority, connector_id)
    if _is_hosted_authority(authority):
        return {
            "connector_id": connector_id,
            "tools": frozen_hosted_tools(connector),
        }
    tools = await discover_tools(connector)
    allowed = connector.get("tool_policy") or {}
    return {
        "connector_id": connector_id,
        "tools": [
            {
                **tool,
                "allowed": (allowed.get(tool["name"]) or {}).get("risk") == "read",
                "risk": (allowed.get(tool["name"]) or {}).get("risk", "deny"),
            }
            for tool in tools
        ],
    }


@mcp.tool(name="rally_connector_call")
async def gateway_call(
    connector_id: str,
    tool_name: str,
    arguments: dict[str, Any] | None = None,
    approval_id: str | None = None,
) -> dict[str, Any]:
    """Call an allowlisted tool; gated calls need an exact one-time approval ID."""
    return await call_allowed_tool(
        load_authority(), connector_id, tool_name, arguments, approval_id
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--policy", help="authority file; defaults to RALLY_CONNECTOR_POLICY")
    parser.add_argument(
        "--inspect", action="store_true", help="print secret-free authority summary"
    )
    args = parser.parse_args()
    if args.policy:
        os.environ["RALLY_CONNECTOR_POLICY"] = os.path.abspath(args.policy)
    if args.inspect:
        print(json.dumps(public_connector_list(load_authority()), indent=2))
        return 0
    mcp.run(transport="stdio")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
