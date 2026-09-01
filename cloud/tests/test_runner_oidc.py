from types import SimpleNamespace
from unittest.mock import patch

import pytest

import runner_oidc

AUDIENCE = "https://control-plane.example"
ACCOUNT = "rally-runner@example.iam.gserviceaccount.com"


def test_mint_uses_exact_impersonated_identity_and_audience():
    completed = SimpleNamespace(returncode=0, stdout="header.payload.signature\n")
    with patch.object(runner_oidc.subprocess, "run", return_value=completed) as invoked:
        token = runner_oidc.mint_runner_identity_token(AUDIENCE, ACCOUNT)
    assert token == "header.payload.signature"
    command = invoked.call_args.args[0]
    assert f"--impersonate-service-account={ACCOUNT}" in command
    assert f"--audiences={AUDIENCE}" in command
    assert "--include-email" in command
    assert invoked.call_args.kwargs["stderr"] == runner_oidc.subprocess.DEVNULL


def test_mint_accepts_explicit_ephemeral_override_without_shelling_out():
    with patch.object(runner_oidc.subprocess, "run") as invoked:
        token = runner_oidc.mint_runner_identity_token(
            AUDIENCE,
            ACCOUNT,
            override_token="header.payload.signature",
        )
    assert token == "header.payload.signature"
    invoked.assert_not_called()


def test_invalid_audience_and_service_account_fail_before_mint():
    for audience, account in (
        ("http://control-plane.example", ACCOUNT),
        ("https://control-plane.example/path", ACCOUNT),
        (AUDIENCE, "not-an-account"),
    ):
        with pytest.raises(runner_oidc.RunnerIdentityError):
            runner_oidc.mint_runner_identity_token(audience, account)


def test_verify_binds_issuer_email_and_audience(monkeypatch):
    observed = {}

    def verify(token, request, *, audience):
        del request
        observed.update(token=token, audience=audience)
        return {
            "iss": "https://accounts.google.com",
            "email": ACCOUNT,
            "email_verified": True,
            "sub": "123456789",
        }

    monkeypatch.setattr(runner_oidc.google_id_token, "verify_oauth2_token", verify)
    monkeypatch.setattr(runner_oidc.google_requests, "Request", lambda: object())
    monkeypatch.setenv("RALLY_RUNNER_AUDIENCE", AUDIENCE)
    monkeypatch.setenv("RALLY_RUNNER_SERVICE_ACCOUNT", ACCOUNT)

    claims = runner_oidc.verify_runner_identity("Bearer header.payload.signature")
    assert claims["sub"] == "123456789"
    assert observed == {"token": "header.payload.signature", "audience": AUDIENCE}


@pytest.mark.parametrize(
    "claims",
    [
        {"iss": "attacker", "email": ACCOUNT, "email_verified": True, "sub": "1"},
        {"iss": "accounts.google.com", "email": "other@example.com", "email_verified": True, "sub": "1"},
        {"iss": "accounts.google.com", "email": ACCOUNT, "email_verified": False, "sub": "1"},
        {"iss": "accounts.google.com", "email": ACCOUNT, "email_verified": True, "sub": ""},
    ],
)
def test_verify_rejects_wrong_identity_claims(monkeypatch, claims):
    monkeypatch.setattr(
        runner_oidc.google_id_token,
        "verify_oauth2_token",
        lambda *args, **kwargs: claims,
    )
    monkeypatch.setattr(runner_oidc.google_requests, "Request", lambda: object())
    with pytest.raises(runner_oidc.RunnerIdentityError):
        runner_oidc.verify_runner_identity(
            "Bearer header.payload.signature",
            audience=AUDIENCE,
            expected_service_account=ACCOUNT,
        )
