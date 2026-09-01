"""Compact, reversible references for Rally run identifiers.

The compact form is intended for human-facing surfaces such as email subjects.
It deliberately identifies a *prefix*, not necessarily a unique run; callers
must use :func:`resolve` and handle collisions before acting on one.
"""

from __future__ import annotations

from datetime import datetime
import re
from typing import Iterable


_RUN_ID_RE = re.compile(
    r"r-(?P<date>20\d{6})-(?P<head>[a-z0-9]{1,64})"
    r"(?:-[a-z0-9]{1,64})*",
    re.ASCII | re.IGNORECASE,
)
_PUBLIC_REF_RE = re.compile(
    r"(?P<date>\d{6})-(?P<head>[a-z0-9]{1,64})",
    re.ASCII | re.IGNORECASE,
)


class RunReferenceResolutionError(LookupError):
    """Base class for a syntactically valid reference that cannot resolve."""


class RunReferenceNotFoundError(RunReferenceResolutionError):
    """Raised when no available run matches a reference."""


class AmbiguousRunReferenceError(RunReferenceResolutionError):
    """Raised when more than one available run matches a compact reference."""


def _require_calendar_date(value: str, fmt: str) -> None:
    try:
        datetime.strptime(value, fmt)
    except ValueError as exc:
        raise ValueError("run reference contains an invalid calendar date") from exc


def _parse_run_id(run_id: str) -> re.Match[str]:
    if not isinstance(run_id, str):
        raise TypeError("run_id must be a string")
    match = _RUN_ID_RE.fullmatch(run_id)
    if match is None:
        raise ValueError("invalid Rally run id")
    _require_calendar_date(match.group("date"), "%Y%m%d")
    return match


def public_ref(run_id: str) -> str:
    """Return the canonical uppercase, human-facing reference for ``run_id``.

    Only the first component after the date is exposed. For UUID-backed run
    identifiers this is the first eight hexadecimal characters.
    """

    match = _parse_run_id(run_id)
    return "%s-%s" % (match.group("date")[2:], match.group("head").upper())


def candidate_prefix(ref: str) -> str:
    """Expand a compact reference to its canonical lowercase run-id prefix."""

    if not isinstance(ref, str):
        raise TypeError("ref must be a string")
    match = _PUBLIC_REF_RE.fullmatch(ref)
    if match is None:
        raise ValueError("invalid compact Rally run reference")
    full_date = "20" + match.group("date")
    _require_calendar_date(full_date, "%Y%m%d")
    return "r-%s-%s" % (full_date, match.group("head").lower())


def resolve(ref: str, available_ids: Iterable[str]) -> str:
    """Resolve ``ref`` to exactly one entry from ``available_ids``.

    Full run identifiers use exact, case-insensitive matching. Compact
    references match a component boundary after their expanded prefix. Invalid
    entries in ``available_ids`` are ignored, as they are not Rally run ids.
    """

    if not isinstance(ref, str):
        raise TypeError("ref must be a string")

    full_match = _RUN_ID_RE.fullmatch(ref)
    if full_match is not None:
        _require_calendar_date(full_match.group("date"), "%Y%m%d")
        expected = ref.casefold()

        def matches(run_id: str) -> bool:
            return run_id.casefold() == expected

    else:
        prefix = candidate_prefix(ref).casefold()

        def matches(run_id: str) -> bool:
            folded = run_id.casefold()
            return folded == prefix or folded.startswith(prefix + "-")

    found = []
    seen = set()
    for run_id in available_ids:
        if not isinstance(run_id, str) or run_id in seen:
            continue
        seen.add(run_id)
        try:
            _parse_run_id(run_id)
        except (TypeError, ValueError):
            continue
        if matches(run_id):
            found.append(run_id)

    if not found:
        raise RunReferenceNotFoundError("no Rally run matches %r" % ref)
    if len(found) != 1:
        raise AmbiguousRunReferenceError(
            "%r matches %d Rally runs" % (ref, len(found))
        )
    return found[0]


__all__ = [
    "AmbiguousRunReferenceError",
    "RunReferenceNotFoundError",
    "RunReferenceResolutionError",
    "candidate_prefix",
    "public_ref",
    "resolve",
]
