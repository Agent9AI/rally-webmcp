"""Mint and verify the dedicated runner identity used for hosted tool relay."""

from __future__ import annotations

import os
import re
import subprocess
from typing import Any
from urllib.parse import urlsplit

from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token


class RunnerIdentityError(RuntimeError):
    """The hosted runner identity is missing, malformed, or untrusted."""


_SERVICE_ACCOUNT = re.compile(
    r"^[A-Za-z0-9][A-Za-z0-9._-]{0,126}@[A-Za-z0-9.-]{1,190}$"
)
_MAX_TOKEN_BYTES = 24 * 1024


def _audience(value: str | None) -> str:
    if not isinstance(value, str) or not value or len(value) > 2048:
        raise RunnerIdentityError("runner identity is not configured")
    try:
        parsed = urlsplit(value)
    except ValueError:
        raise RunnerIdentityError("runner identity is not configured") from None
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
        or parsed.path not in {"", "/"}
    ):
        raise RunnerIdentityError("runner identity is not configured")
    return value.rstrip("/")


def _service_account(value: str | None) -> str:
    if not isinstance(value, str) or not _SERVICE_ACCOUNT.fullmatch(value):
        raise RunnerIdentityError("runner identity is not configured")
    return value.casefold()


def _token(value: str | None) -> str:
    if (
        not isinstance(value, str)
        or not value
        or len(value.encode("utf-8")) > _MAX_TOKEN_BYTES
        or any(character.isspace() for character in value)
    ):
        raise RunnerIdentityError("runner identity is unavailable")
    return value


def mint_runner_identity_token(
    audience: str,
    service_account: str,
    *,
    override_token: str | None = None,
) -> str:
    """Mint an audience-bound token without ever persisting or printing it."""

    trusted_audience = _audience(audience)
    trusted_account = _service_account(service_account)
    supplied = override_token or os.getenv("RALLY_HOSTED_CONNECTOR_IDENTITY_TOKEN")
    if supplied:
        return _token(supplied)
    try:
        completed = subprocess.run(
            [
                "gcloud",
                "auth",
                "print-identity-token",
                f"--impersonate-service-account={trusted_account}",
                f"--audiences={trusted_audience}",
                "--include-email",
            ],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=25,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        raise RunnerIdentityError("runner identity is unavailable") from None
    if completed.returncode != 0:
        raise RunnerIdentityError("runner identity is unavailable")
    return _token(completed.stdout.strip())


def verify_runner_identity(
    authorization: str | None,
    *,
    audience: str | None = None,
    expected_service_account: str | None = None,
) -> dict[str, Any]:
    """Verify exact audience, issuer, and dedicated service-account ownership."""

    trusted_audience = _audience(audience or os.getenv("RALLY_RUNNER_AUDIENCE"))
    trusted_account = _service_account(
        expected_service_account or os.getenv("RALLY_RUNNER_SERVICE_ACCOUNT")
    )
    if (
        not isinstance(authorization, str)
        or not authorization.startswith("Bearer ")
        or authorization.count(" ") != 1
    ):
        raise RunnerIdentityError("runner authentication required")
    raw_token = _token(authorization.removeprefix("Bearer "))
    try:
        claims = google_id_token.verify_oauth2_token(
            raw_token,
            google_requests.Request(),
            audience=trusted_audience,
        )
    except Exception:  # noqa: BLE001 - every verification/transport failure is denial
        raise RunnerIdentityError("runner identity is invalid") from None
    if (
        not isinstance(claims, dict)
        or claims.get("iss") not in {"accounts.google.com", "https://accounts.google.com"}
        or claims.get("email_verified") is not True
        or str(claims.get("email", "")).casefold() != trusted_account
        or not isinstance(claims.get("sub"), str)
        or not claims["sub"]
    ):
        raise RunnerIdentityError("runner identity is invalid")
    return dict(claims)
