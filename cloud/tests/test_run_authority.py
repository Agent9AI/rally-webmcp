import copy
import datetime as dt
import hashlib
import json

import pytest

from run_authority import (
    AUTHORITY_SCHEMA,
    CERTIFICATION_SCHEMA,
    MAX_AUTHORITY_AGE,
    RunAuthorityError,
    mint_run_authority,
    verify_run_authority,
)

NOW = dt.datetime(2026, 8, 31, 12, 0, tzinfo=dt.UTC)
SECRET = "authority-signing-secret-material-123456789"


def certified_tools(count=1):
    return [
        [f"tool_{index:03d}", hashlib.sha256(f"schema-{index}".encode()).hexdigest()]
        for index in range(count)
    ]


def grant(connector_id="github", *, tool_count=1):
    tools = certified_tools(tool_count)
    manifest = hashlib.sha256(
        json.dumps(tools, separators=(",", ":")).encode()
    ).hexdigest()
    return {
        "connector_id": connector_id,
        "authorization_generation": hashlib.sha256(connector_id.encode()).hexdigest()[:32],
        "proof_version": CERTIFICATION_SCHEMA,
        "certified_manifest_sha256": manifest,
        "certified_policy_sha256": hashlib.sha256(
            f"policy-{connector_id}".encode()
        ).hexdigest(),
        "certified_tools": tools,
    }


def mint(**overrides):
    values = {
        "run_id": "r-20260831-authority",
        "uid": "google-user-one",
        "workspace_id": "user:google-user-one",
        "grants": [grant()],
        "issued_at": NOW,
        "expires_at": NOW + dt.timedelta(hours=1),
    }
    values.update(overrides)
    return mint_run_authority(SECRET, **values)


def test_mint_is_canonical_signed_secret_free_and_round_trips():
    github = grant("github", tool_count=2)
    github["certified_tools"].reverse()
    github["certified_manifest_sha256"] = hashlib.sha256(
        json.dumps(
            sorted(github["certified_tools"]), separators=(",", ":")
        ).encode()
    ).hexdigest()
    authority = mint(grants=[github, grant("atlassian")])

    assert set(authority) == {
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
    assert authority["schema"] == AUTHORITY_SCHEMA
    assert authority["default_decision"] == "deny"
    assert [item["connector_id"] for item in authority["grants"]] == [
        "atlassian",
        "github",
    ]
    assert authority["grants"][1]["certified_tools"] == certified_tools(2)
    assert len(authority["signature"]) == 64
    assert set(authority["signature"]) <= set("0123456789abcdef")
    assert mint(grants=[github, grant("atlassian")]) == authority
    assert verify_run_authority(
        authority,
        SECRET,
        now=NOW,
        expected_run_id="r-20260831-authority",
        expected_uid="google-user-one",
        expected_workspace_id="user:google-user-one",
    ) == authority
    encoded = json.dumps(authority)
    assert SECRET not in encoded
    assert "credential" not in encoded


@pytest.mark.parametrize(
    ("field", "replacement"),
    [
        ("schema", "rally.hosted-run-authority/v2"),
        ("run_id", "r-20260831-other"),
        ("uid", "google-user-two"),
        ("workspace_id", "user:google-user-two"),
        ("issued_at", "2026-08-31T11:59:59Z"),
        ("expires_at", "2026-08-31T13:00:01Z"),
        ("default_decision", "allow"),
    ],
)
def test_verify_rejects_tampered_signed_fields(field, replacement):
    authority = mint()
    authority[field] = replacement

    with pytest.raises(RunAuthorityError, match="invalid hosted run authority"):
        verify_run_authority(authority, SECRET, now=NOW)


def test_verify_rejects_tampered_grant_wrong_secret_and_bad_signature_shape():
    authority = mint()
    authority["grants"][0]["authorization_generation"] = "f" * 32
    with pytest.raises(RunAuthorityError):
        verify_run_authority(authority, SECRET, now=NOW)

    authority = mint()
    with pytest.raises(RunAuthorityError):
        verify_run_authority(authority, "different-signing-secret-material-123456", now=NOW)

    authority["signature"] = "A" * 64
    with pytest.raises(RunAuthorityError):
        verify_run_authority(authority, SECRET, now=NOW)


@pytest.mark.parametrize(
    "expected",
    [
        {"expected_run_id": "r-20260831-other"},
        {"expected_uid": "google-user-two"},
        {"expected_workspace_id": "user:google-user-two"},
    ],
)
def test_verify_rejects_caller_binding_mismatches(expected):
    with pytest.raises(RunAuthorityError):
        verify_run_authority(mint(), SECRET, now=NOW, **expected)


def test_exact_schema_rejects_unknown_missing_and_non_json_container_types():
    authority = mint()
    authority["unexpected"] = True
    with pytest.raises(RunAuthorityError):
        verify_run_authority(authority, SECRET, now=NOW)

    authority = mint()
    del authority["default_decision"]
    with pytest.raises(RunAuthorityError):
        verify_run_authority(authority, SECRET, now=NOW)

    authority = mint()
    authority["grants"] = tuple(authority["grants"])
    with pytest.raises(RunAuthorityError):
        verify_run_authority(authority, SECRET, now=NOW)

    invalid_grant = grant()
    invalid_grant["credential"] = "must-never-appear"
    with pytest.raises(RunAuthorityError):
        mint(grants=[invalid_grant])


def test_verify_rejects_noncanonical_array_order_even_with_original_signature():
    authority = mint(grants=[grant("atlassian"), grant("github", tool_count=2)])
    authority["grants"].reverse()
    with pytest.raises(RunAuthorityError):
        verify_run_authority(authority, SECRET, now=NOW)

    authority = mint(grants=[grant("github", tool_count=2)])
    authority["grants"][0]["certified_tools"].reverse()
    with pytest.raises(RunAuthorityError):
        verify_run_authority(authority, SECRET, now=NOW)


def test_grant_manifest_and_uniqueness_are_strict():
    invalid_manifest = grant()
    invalid_manifest["certified_manifest_sha256"] = "f" * 64
    with pytest.raises(RunAuthorityError):
        mint(grants=[invalid_manifest])

    with pytest.raises(RunAuthorityError):
        mint(grants=[grant(), grant()])

    duplicate_tool = grant()
    duplicate_tool["certified_tools"].append(duplicate_tool["certified_tools"][0])
    duplicate_tool["certified_manifest_sha256"] = hashlib.sha256(
        json.dumps(duplicate_tool["certified_tools"], separators=(",", ":")).encode()
    ).hexdigest()
    with pytest.raises(RunAuthorityError):
        mint(grants=[duplicate_tool])


def test_grant_and_tool_limits_are_enforced():
    thirty_two = [grant(f"connector-{index:02d}") for index in range(32)]
    assert len(mint(grants=thirty_two)["grants"]) == 32
    with pytest.raises(RunAuthorityError):
        mint(grants=[*thirty_two, grant("connector-32")])

    assert len(mint(grants=[grant(tool_count=128)])["grants"][0]["certified_tools"]) == 128
    with pytest.raises(RunAuthorityError):
        mint(grants=[grant(tool_count=129)])


def test_lifetime_is_bounded_and_expiry_is_enforced():
    maximum = mint(expires_at=NOW + MAX_AUTHORITY_AGE)
    assert verify_run_authority(maximum, SECRET, now=NOW) == maximum

    with pytest.raises(RunAuthorityError):
        mint(expires_at=NOW + MAX_AUTHORITY_AGE + dt.timedelta(seconds=1))
    with pytest.raises(RunAuthorityError):
        verify_run_authority(mint(), SECRET, now=NOW + dt.timedelta(hours=1))
    with pytest.raises(RunAuthorityError):
        verify_run_authority(mint(), SECRET, now=NOW - dt.timedelta(seconds=1))


def test_missing_or_short_signing_secret_fails_closed():
    with pytest.raises(RunAuthorityError, match="signing secret is not configured"):
        mint_run_authority(
            "",
            run_id="r-20260831-authority",
            uid="google-user-one",
            workspace_id="user:google-user-one",
            grants=[],
            issued_at=NOW,
        )
    with pytest.raises(RunAuthorityError, match="signing secret is not configured"):
        verify_run_authority(mint(), "short", now=NOW)


def test_verification_does_not_mutate_the_snapshot():
    authority = mint()
    original = copy.deepcopy(authority)

    verify_run_authority(authority, SECRET, now=NOW)

    assert authority == original
