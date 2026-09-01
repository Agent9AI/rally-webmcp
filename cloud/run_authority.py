"""Strict, signed authority snapshots for hosted connector runs."""

from __future__ import annotations

import copy
import datetime as dt
import hashlib
import hmac
import json
import re
from collections.abc import Iterable, Mapping
from typing import Any, Final


class RunAuthorityError(ValueError):
    """A hosted run authority could not be safely minted or verified."""


AUTHORITY_SCHEMA: Final = "rally.hosted-run-authority/v1"
CERTIFICATION_SCHEMA: Final = "rally.connection-certification/v1"
MAX_AUTHORITY_AGE: Final = dt.timedelta(days=35)
MAX_GRANTS: Final = 32
MAX_TOOLS_PER_GRANT: Final = 128

_AUTHORITY_KEYS: Final = {
    "schema",
    "run_id",
    "uid",
    "workspace_id",
    "issued_at",
    "expires_at",
    "default_decision",
    "grants",
    "signature",
}
_UNSIGNED_KEYS: Final = _AUTHORITY_KEYS - {"signature"}
_GRANT_KEYS: Final = {
    "connector_id",
    "authorization_generation",
    "proof_version",
    "certified_manifest_sha256",
    "certified_policy_sha256",
    "certified_tools",
}
_RUN_ID: Final = re.compile(r"^r-[0-9a-z-]{3,77}$")
_UID: Final = re.compile(r"^[A-Za-z0-9._:-]{1,255}$")
_WORKSPACE_ID: Final = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,95}$")
_CONNECTOR_ID: Final = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")
_TOOL_NAME: Final = re.compile(r"^[A-Za-z0-9_.:/-]{1,160}$")
_GENERATION: Final = re.compile(r"^[a-f0-9]{32}$")
_SHA256: Final = re.compile(r"^[a-f0-9]{64}$")
_TIMESTAMP: Final = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


def _invalid() -> RunAuthorityError:
    return RunAuthorityError("invalid hosted run authority")


def _secret_bytes(value: str | bytes) -> bytes:
    if isinstance(value, str):
        encoded = value.encode("utf-8")
    elif isinstance(value, bytes):
        encoded = value
    else:
        raise _invalid()
    if len(encoded) < 32:
        raise RunAuthorityError("run authority signing secret is not configured")
    return encoded


def _utc_seconds(value: dt.datetime) -> dt.datetime:
    if not isinstance(value, dt.datetime) or value.tzinfo is None:
        raise _invalid()
    return value.astimezone(dt.UTC).replace(microsecond=0)


def _timestamp(value: dt.datetime) -> str:
    return _utc_seconds(value).isoformat().replace("+00:00", "Z")


def _parse_timestamp(value: Any) -> dt.datetime:
    if not isinstance(value, str) or not _TIMESTAMP.fullmatch(value):
        raise _invalid()
    try:
        return dt.datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=dt.UTC)
    except ValueError:
        raise _invalid() from None


def _canonical_json(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeEncodeError):
        raise _invalid() from None


def _manifest_sha256(tools: list[list[str]]) -> str:
    return hashlib.sha256(_canonical_json(tools)).hexdigest()


def _normalized_grant(value: Any, *, accept_tuples: bool) -> dict[str, Any]:
    if not isinstance(value, Mapping) or set(value) != _GRANT_KEYS:
        raise _invalid()
    connector_id = value.get("connector_id")
    generation = value.get("authorization_generation")
    proof_version = value.get("proof_version")
    manifest = value.get("certified_manifest_sha256")
    policy = value.get("certified_policy_sha256")
    raw_tools = value.get("certified_tools")
    if (
        not isinstance(connector_id, str)
        or not _CONNECTOR_ID.fullmatch(connector_id)
        or not isinstance(generation, str)
        or not _GENERATION.fullmatch(generation)
        or proof_version != CERTIFICATION_SCHEMA
        or not isinstance(manifest, str)
        or not _SHA256.fullmatch(manifest)
        or not isinstance(policy, str)
        or not _SHA256.fullmatch(policy)
        or not isinstance(raw_tools, (list, tuple) if accept_tuples else list)
        or not 1 <= len(raw_tools) <= MAX_TOOLS_PER_GRANT
    ):
        raise _invalid()

    tools: list[list[str]] = []
    for raw_tool in raw_tools:
        expected_type = (list, tuple) if accept_tuples else list
        if not isinstance(raw_tool, expected_type) or len(raw_tool) != 2:
            raise _invalid()
        name, schema_sha256 = raw_tool
        if (
            not isinstance(name, str)
            or not _TOOL_NAME.fullmatch(name)
            or not isinstance(schema_sha256, str)
            or not _SHA256.fullmatch(schema_sha256)
        ):
            raise _invalid()
        tools.append([name, schema_sha256])
    supplied_tools = copy.deepcopy(tools)
    tools.sort(key=lambda item: item[0])
    if len({name for name, _ in tools}) != len(tools):
        raise _invalid()
    if not accept_tuples and supplied_tools != tools:
        raise _invalid()
    if not hmac.compare_digest(manifest, _manifest_sha256(tools)):
        raise _invalid()
    return {
        "connector_id": connector_id,
        "authorization_generation": generation,
        "proof_version": proof_version,
        "certified_manifest_sha256": manifest,
        "certified_policy_sha256": policy,
        "certified_tools": tools,
    }


def _normalized_unsigned(value: Any, *, accept_tuples: bool) -> dict[str, Any]:
    if not isinstance(value, Mapping) or set(value) != _UNSIGNED_KEYS:
        raise _invalid()
    run_id = value.get("run_id")
    uid = value.get("uid")
    workspace_id = value.get("workspace_id")
    if (
        value.get("schema") != AUTHORITY_SCHEMA
        or not isinstance(run_id, str)
        or not _RUN_ID.fullmatch(run_id)
        or not isinstance(uid, str)
        or not _UID.fullmatch(uid)
        or not isinstance(workspace_id, str)
        or not _WORKSPACE_ID.fullmatch(workspace_id)
        or value.get("default_decision") != "deny"
    ):
        raise _invalid()

    issued_at = _parse_timestamp(value.get("issued_at"))
    expires_at = _parse_timestamp(value.get("expires_at"))
    if expires_at <= issued_at or expires_at - issued_at > MAX_AUTHORITY_AGE:
        raise _invalid()

    raw_grants = value.get("grants")
    if (
        not isinstance(raw_grants, (list, tuple) if accept_tuples else list)
        or len(raw_grants) > MAX_GRANTS
    ):
        raise _invalid()
    grants = [_normalized_grant(grant, accept_tuples=accept_tuples) for grant in raw_grants]
    supplied_connector_ids = [grant["connector_id"] for grant in grants]
    grants.sort(key=lambda grant: grant["connector_id"])
    if len({grant["connector_id"] for grant in grants}) != len(grants):
        raise _invalid()
    if not accept_tuples and supplied_connector_ids != [
        grant["connector_id"] for grant in grants
    ]:
        raise _invalid()
    return {
        "schema": AUTHORITY_SCHEMA,
        "run_id": run_id,
        "uid": uid,
        "workspace_id": workspace_id,
        "issued_at": _timestamp(issued_at),
        "expires_at": _timestamp(expires_at),
        "default_decision": "deny",
        "grants": grants,
    }


def mint_run_authority(
    signing_secret: str | bytes,
    *,
    run_id: str,
    uid: str,
    workspace_id: str,
    grants: Iterable[Mapping[str, Any]],
    issued_at: dt.datetime | None = None,
    expires_at: dt.datetime | None = None,
) -> dict[str, Any]:
    """Mint a canonical, deny-by-default snapshot without credential material."""

    secret = _secret_bytes(signing_secret)
    issued = _utc_seconds(issued_at or dt.datetime.now(dt.UTC))
    expires = _utc_seconds(expires_at or issued + MAX_AUTHORITY_AGE)
    unsigned = _normalized_unsigned(
        {
            "schema": AUTHORITY_SCHEMA,
            "run_id": run_id,
            "uid": uid,
            "workspace_id": workspace_id,
            "issued_at": _timestamp(issued),
            "expires_at": _timestamp(expires),
            "default_decision": "deny",
            "grants": list(grants),
        },
        accept_tuples=True,
    )
    signature = hmac.new(secret, _canonical_json(unsigned), hashlib.sha256).hexdigest()
    return {**unsigned, "signature": signature}


def verify_run_authority(
    authority: Mapping[str, Any],
    signing_secret: str | bytes,
    *,
    now: dt.datetime | None = None,
    expected_run_id: str | None = None,
    expected_uid: str | None = None,
    expected_workspace_id: str | None = None,
) -> dict[str, Any]:
    """Verify structure, signature, lifetime, and optional caller bindings."""

    secret = _secret_bytes(signing_secret)
    if not isinstance(authority, Mapping) or set(authority) != _AUTHORITY_KEYS:
        raise _invalid()
    signature = authority.get("signature")
    if not isinstance(signature, str) or not _SHA256.fullmatch(signature):
        raise _invalid()
    unsigned = _normalized_unsigned(
        {key: copy.deepcopy(authority[key]) for key in _UNSIGNED_KEYS},
        accept_tuples=False,
    )
    expected_signature = hmac.new(
        secret, _canonical_json(unsigned), hashlib.sha256
    ).hexdigest()
    if not hmac.compare_digest(signature, expected_signature):
        raise _invalid()

    current = _utc_seconds(now or dt.datetime.now(dt.UTC))
    if _parse_timestamp(unsigned["issued_at"]) > current:
        raise _invalid()
    if _parse_timestamp(unsigned["expires_at"]) <= current:
        raise _invalid()
    if expected_run_id is not None and unsigned["run_id"] != expected_run_id:
        raise _invalid()
    if expected_uid is not None and unsigned["uid"] != expected_uid:
        raise _invalid()
    if (
        expected_workspace_id is not None
        and unsigned["workspace_id"] != expected_workspace_id
    ):
        raise _invalid()
    return {**unsigned, "signature": signature}
