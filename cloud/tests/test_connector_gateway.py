import json
import re
import sys
from contextlib import asynccontextmanager
from copy import deepcopy
from types import SimpleNamespace

import httpx
import pytest

import connector_approvals
import connector_gateway
from connector_gateway import MAX_ARGUMENT_BYTES, ConnectorGatewayError, call_allowed_tool


def hosted_authority(tmp_path):
    signed = {
        "schema": "rally.hosted-run-authority/v1",
        "run_id": "r-hosted",
        "uid": "google-subject-123",
        "workspace_id": "w-123",
        "issued_at": "2026-08-31T12:00:00Z",
        "expires_at": "2026-09-01T12:00:00Z",
        "default_decision": "deny",
        "grants": [
            {
                "connector_id": "bigquery",
                "authorization_generation": "1" * 32,
                "proof_version": "rally.connection-certification/v1",
                "certified_manifest_sha256": "2" * 64,
                "certified_policy_sha256": "3" * 64,
                "certified_tools": [["execute_sql", "4" * 64]],
            }
        ],
        "signature": "5" * 64,
    }
    return {
        "schema_version": "rally.hosted-connector-authority/v1",
        "run_id": "r-hosted",
        "credential_profile": "hosted-123",
        "default_decision": "deny",
        "policy": {
            "require_explicit_tool_allowlist": True,
            "human_approval_tools_enabled": False,
            "record_content": False,
        },
        "connectors": [
            {
                "id": "bigquery",
                "name": "BigQuery",
                "mode": "hosted",
                "tool_policy": {
                    "execute_sql": {
                        "risk": "read",
                        "constraints": {
                            "max_argument_bytes": 64 * 1024,
                            "max_result_bytes": 256 * 1024,
                        },
                    }
                },
            }
        ],
        "hosted_run_authority": signed,
        "relay": {
            "url": "https://control.example.run.app",
            "audience": "https://control.example.run.app",
            "identity_service_account": "runner@example.iam.gserviceaccount.com",
        },
        "receipt_path": str(tmp_path / "receipts.jsonl"),
        "catalog_path": "config/connectors.json",
    }


def relay_client(monkeypatch, handler):
    transport = httpx.MockTransport(handler)
    monkeypatch.setattr(
        connector_gateway,
        "_relay_http_client",
        lambda: httpx.AsyncClient(transport=transport, follow_redirects=False),
    )


@pytest.mark.asyncio
async def test_hosted_tools_are_frozen_and_never_discovered(tmp_path, monkeypatch):
    authority = hosted_authority(tmp_path)
    monkeypatch.setattr(connector_gateway, "load_authority", lambda: authority)

    async def forbidden_discovery(*_args, **_kwargs):
        raise AssertionError("hosted tools must not use provider discovery")

    monkeypatch.setattr(connector_gateway, "discover_tools", forbidden_discovery)
    result = await connector_gateway.gateway_tools("bigquery")
    assert result == {
        "connector_id": "bigquery",
        "tools": [
            {
                "name": "execute_sql",
                "title": None,
                "description": "Certified read-only company-system tool.",
                "input_schema": {"type": "object", "additionalProperties": True},
                "allowed": True,
                "risk": "read",
            }
        ],
    }


@pytest.mark.asyncio
async def test_hosted_call_uses_oidc_and_exact_bounded_relay_contract(tmp_path, monkeypatch):
    authority = hosted_authority(tmp_path)
    identity_calls = []
    requests = []

    async def fake_identity(audience, service_account):
        identity_calls.append((audience, service_account))
        return "signed.identity.token." + "x" * 32

    async def forbidden_remote(*_args, **_kwargs):
        raise AssertionError("hosted calls must not open a provider session")

    def handler(request):
        requests.append(request)
        body = json.loads(request.content)
        assert set(body) == {"authority", "run_id", "call_id", "tool_name", "arguments"}
        assert body["authority"] == authority["hosted_run_authority"]
        assert body["run_id"] == "r-hosted"
        assert re.fullmatch(r"[0-9a-f]{32}", body["call_id"])
        assert body["tool_name"] == "execute_sql"
        assert body["arguments"] == {"query": "SELECT 1"}
        assert request.headers["authorization"] == "Bearer signed.identity.token." + "x" * 32
        assert request.headers["content-type"] == "application/json"
        return httpx.Response(
            200,
            headers={"content-type": "application/json"},
            json={
                "payload": {"content": [{"type": "text", "text": "one row"}]},
                "receipt": {"execution_id": body["call_id"], "status": "complete"},
            },
        )

    monkeypatch.setattr(connector_gateway, "_mint_relay_identity_token", fake_identity)
    monkeypatch.setattr(connector_gateway, "remote_session", forbidden_remote)
    relay_client(monkeypatch, handler)
    result = await call_allowed_tool(authority, "bigquery", "execute_sql", {"query": "SELECT 1"})
    assert result == {"content": [{"type": "text", "text": "one row"}]}
    assert identity_calls == [
        (
            "https://control.example.run.app",
            "runner@example.iam.gserviceaccount.com",
        )
    ]
    assert len(requests) == 1
    receipt_text = (tmp_path / "receipts.jsonl").read_text()
    assert "signed.identity.token" not in receipt_text
    assert "SELECT 1" not in receipt_text
    assert "relay_receipt_sha256" in receipt_text


@pytest.mark.asyncio
async def test_runner_oidc_helper_receives_exact_audience_and_identity(monkeypatch):
    calls = []

    def mint(audience, service_account):
        calls.append((audience, service_account))
        return "a" * 64

    monkeypatch.setitem(
        sys.modules,
        "runner_oidc",
        SimpleNamespace(mint_runner_identity_token=mint),
    )
    token = await connector_gateway._mint_relay_identity_token(
        "https://control.example.run.app",
        "runner@example.iam.gserviceaccount.com",
    )
    assert token == "a" * 64
    assert calls == [
        (
            "https://control.example.run.app",
            "runner@example.iam.gserviceaccount.com",
        )
    ]


@pytest.mark.asyncio
async def test_hosted_relay_non_success_never_redirects_or_falls_back(tmp_path, monkeypatch):
    authority = hosted_authority(tmp_path)
    requests = []

    async def fake_identity(*_args):
        return "i" * 64

    def handler(request):
        requests.append(request)
        return httpx.Response(
            307,
            headers={
                "location": "https://attacker.invalid/steal",
                "content-type": "application/json",
            },
            json={"payload": {}, "receipt": {}},
        )

    monkeypatch.setattr(connector_gateway, "_mint_relay_identity_token", fake_identity)
    relay_client(monkeypatch, handler)
    with pytest.raises(ConnectorGatewayError, match="returned HTTP 307"):
        await call_allowed_tool(authority, "bigquery", "execute_sql", {})
    assert len(requests) == 1
    assert requests[0].url.host == "control.example.run.app"


@pytest.mark.asyncio
async def test_hosted_relay_rejects_oversized_and_malformed_responses(tmp_path, monkeypatch):
    authority = hosted_authority(tmp_path)

    async def fake_identity(*_args):
        return "i" * 64

    monkeypatch.setattr(connector_gateway, "_mint_relay_identity_token", fake_identity)

    def oversized(_request):
        return httpx.Response(
            200,
            headers={"content-type": "application/json"},
            content=b"x" * (connector_gateway.MAX_RELAY_RESPONSE_BYTES + 1),
        )

    relay_client(monkeypatch, oversized)
    with pytest.raises(ConnectorGatewayError, match="response is too large"):
        await call_allowed_tool(authority, "bigquery", "execute_sql", {})

    malformed_responses = [
        b'{"payload":{},"receipt":{},"extra":true}',
        b'{"payload":{},"payload":{},"receipt":{}}',
        b'{"payload":[],"receipt":{}}',
        b"not-json",
    ]
    for body in malformed_responses:

        def malformed(_request, body=body):
            return httpx.Response(
                200,
                headers={"content-type": "application/json"},
                content=body,
            )

        relay_client(monkeypatch, malformed)
        with pytest.raises(ConnectorGatewayError, match="response is malformed"):
            await call_allowed_tool(authority, "bigquery", "execute_sql", {})


def test_hosted_policy_is_secret_free_and_rejects_embedded_relay_tokens(tmp_path):
    authority = hosted_authority(tmp_path)
    path = tmp_path / "authority.json"
    path.write_text(json.dumps(authority))
    loaded = connector_gateway.load_authority(str(path))
    public = json.dumps(connector_gateway.public_connector_list(loaded), sort_keys=True)
    assert "signature" not in public
    assert "identity_service_account" not in public
    assert "token" not in public.casefold()
    assert connector_gateway.public_connector_list(loaded)["connectors"][0]["ready"] is True

    contaminated = deepcopy(authority)
    contaminated["relay"]["token"] = "must-never-be-stored"
    path.write_text(json.dumps(contaminated))
    with pytest.raises(ConnectorGatewayError, match="relay configuration is invalid"):
        connector_gateway.load_authority(str(path))


@pytest.mark.asyncio
async def test_denied_tool_never_reaches_remote_and_writes_content_free_receipt(tmp_path):
    receipt_path = tmp_path / "receipts.jsonl"
    authority = {
        "schema_version": "rally.connector-authority/v1",
        "run_id": "r-test",
        "default_decision": "deny",
        "receipt_path": str(receipt_path),
        "connectors": [
            {
                "id": "bigquery",
                "name": "BigQuery",
                "endpoint": "https://should-not-be-called.invalid/mcp",
                "tool_policy": {},
            }
        ],
    }
    with pytest.raises(ConnectorGatewayError, match="not on this run's tool allowlist"):
        await call_allowed_tool(authority, "bigquery", "delete_dataset", {"secret": "value"})
    receipt = json.loads(receipt_path.read_text())
    assert receipt["decision"] == "denied"
    assert receipt["reason"] == "not_allowlisted"
    assert receipt["tool"] == "delete_dataset"
    assert "secret" not in receipt_path.read_text()
    assert "value" not in receipt_path.read_text()


@pytest.mark.asyncio
async def test_oversized_arguments_are_denied_before_remote_connection(tmp_path):
    receipt_path = tmp_path / "receipts.jsonl"
    authority = {
        "schema_version": "rally.connector-authority/v1",
        "run_id": "r-test",
        "default_decision": "deny",
        "receipt_path": str(receipt_path),
        "connectors": [
            {
                "id": "bigquery",
                "name": "BigQuery",
                "endpoint": "https://should-not-be-called.invalid/mcp",
                "tool_policy": {"execute_sql": {"risk": "read"}},
            }
        ],
    }
    with pytest.raises(ConnectorGatewayError, match="arguments violate"):
        await call_allowed_tool(
            authority, "bigquery", "execute_sql", {"query": "x" * MAX_ARGUMENT_BYTES}
        )
    receipt = json.loads(receipt_path.read_text())
    assert receipt["decision"] == "denied"
    assert receipt["reason"] == "arguments_too_large"
    assert "xxxxx" not in receipt_path.read_text()


@pytest.mark.asyncio
async def test_argument_allowlist_is_enforced_before_remote_connection(tmp_path):
    receipt_path = tmp_path / "receipts.jsonl"
    authority = {
        "schema_version": "rally.connector-authority/v1",
        "run_id": "r-test",
        "default_decision": "deny",
        "receipt_path": str(receipt_path),
        "connectors": [
            {
                "id": "n8n",
                "name": "n8n",
                "endpoint": "https://should-not-be-called.invalid/mcp",
                "tool_policy": {
                    "execute_workflow": {
                        "risk": "read",
                        "constraints": {
                            "arguments": {
                                "workflowId": {
                                    "required": True,
                                    "allowed_values": ["wf-approved"],
                                }
                            }
                        },
                    }
                },
            }
        ],
    }
    with pytest.raises(ConnectorGatewayError, match="argument_outside_allowlist"):
        await call_allowed_tool(authority, "n8n", "execute_workflow", {"workflowId": "wf-other"})
    receipt = json.loads(receipt_path.read_text())
    assert receipt["decision"] == "denied"
    assert receipt["reason"] == "argument_outside_allowlist"


@pytest.mark.asyncio
async def test_human_approval_is_exact_single_use_and_precedes_remote_call(tmp_path, monkeypatch):
    receipt_path = tmp_path / "receipts.jsonl"
    approval_path = tmp_path / "approvals.json"
    authority = {
        "schema_version": "rally.connector-authority/v1",
        "run_id": "r-test",
        "default_decision": "deny",
        "receipt_path": str(receipt_path),
        "approval_path": str(approval_path),
        "policy": {"human_approval_tools_enabled": True},
        "connectors": [
            {
                "id": "n8n",
                "name": "n8n",
                "endpoint": "https://tenant.app.n8n.cloud/mcp-server/http",
                "tool_policy": {
                    "execute_workflow": {
                        "risk": "human_approval",
                        "constraints": {
                            "arguments": {
                                "workflowId": {
                                    "required": True,
                                    "allowed_values": ["wf-approved"],
                                }
                            }
                        },
                    }
                },
            }
        ],
    }
    calls = []

    class Result:
        isError = False

        def model_dump(self, **_):
            return {"content": [{"type": "text", "text": "started"}]}

    class Session:
        async def call_tool(self, tool_name, arguments):
            calls.append((tool_name, arguments))
            return Result()

    @asynccontextmanager
    async def fake_remote_session(_connector):
        yield Session()

    monkeypatch.setattr(connector_gateway, "remote_session", fake_remote_session)
    arguments = {"workflowId": "wf-approved"}

    with pytest.raises(ConnectorGatewayError, match="requires human approval"):
        await call_allowed_tool(authority, "n8n", "execute_workflow", arguments)
    assert calls == []
    pending = connector_approvals.list_public(approval_path, status="pending")
    assert len(pending) == 1
    approval_id = pending[0]["approval_id"]
    connector_approvals.approve(approval_path, approval_id, human_identity="human-operator")

    result = await call_allowed_tool(
        authority,
        "n8n",
        "execute_workflow",
        arguments,
        approval_id,
    )
    assert result["content"][0]["text"] == "started"
    assert calls == [("execute_workflow", arguments)]

    with pytest.raises(ConnectorGatewayError, match="approval was refused"):
        await call_allowed_tool(
            authority,
            "n8n",
            "execute_workflow",
            arguments,
            approval_id,
        )
    assert calls == [("execute_workflow", arguments)]
    receipt_text = receipt_path.read_text()
    assert "wf-approved" not in receipt_text
    assert '"decision": "pending_approval"' in receipt_text
    assert '"decision": "allowed"' in receipt_text


@pytest.mark.asyncio
async def test_bundled_provider_dispatch_strips_only_the_pinned_service_prefix(
    tmp_path, monkeypatch
):
    receipt_path = tmp_path / "receipts.jsonl"
    authority = {
        "schema_version": "rally.connector-authority/v1",
        "run_id": "r-test",
        "default_decision": "deny",
        "receipt_path": str(receipt_path),
        "connectors": [
            {
                "id": "google-workspace",
                "name": "Google Workspace",
                "endpoint": "",
                "dispatch": {
                    "strategy": "tool_prefix",
                    "separator": ".",
                    "services": {
                        "gmail": "https://gmailmcp.googleapis.com/mcp/v1",
                        "drive": "https://drivemcp.googleapis.com/mcp/v1",
                    },
                },
                "tool_policy": {"gmail.search_threads": {"risk": "read"}},
            }
        ],
    }
    calls = []

    class Result:
        isError = False

        def model_dump(self, **_):
            return {"content": []}

    class Session:
        async def call_tool(self, tool_name, arguments):
            calls.append((tool_name, arguments))
            return Result()

    @asynccontextmanager
    async def fake_remote_session(connector):
        calls.append(("endpoint", connector["endpoint"]))
        yield Session()

    monkeypatch.setattr(connector_gateway, "remote_session", fake_remote_session)
    await call_allowed_tool(
        authority,
        "google-workspace",
        "gmail.search_threads",
        {"query": "launch"},
    )
    assert calls == [
        ("endpoint", "https://gmailmcp.googleapis.com/mcp/v1"),
        ("search_threads", {"query": "launch"}),
    ]

    with pytest.raises(ConnectorGatewayError, match="not on this run's tool allowlist"):
        await call_allowed_tool(
            authority,
            "google-workspace",
            "drive.search_threads",
            {"query": "launch"},
        )
    assert len(calls) == 2
