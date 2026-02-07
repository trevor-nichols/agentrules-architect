"""Helpers for canonical ExecPlan identity derived from filenames."""

from __future__ import annotations

import re

EXECPLAN_FILENAME_RE = re.compile(
    r"^(?P<id>EP-(?P<date>\d{8})-(?P<sequence>\d{3}))(?=$|[._-])"
)
EXECPLAN_FILENAME_POLICY_RE = re.compile(
    r"^(?P<id>EP-(?P<date>\d{8})-(?P<sequence>\d{3}))(?:[_-][A-Za-z0-9][A-Za-z0-9_-]*)?\.md$"
)


def parse_execplan_filename(filename: str) -> tuple[str, str, int] | None:
    """
    Parse canonical ExecPlan identity from a filename.

    Returns (id, date_token, sequence) when the filename starts with
    EP-YYYYMMDD-NNN and the next character is either:
    - end-of-string
    - '.'
    - '_'
    - '-'

    This parser is intentionally permissive for identity extraction. Use
    ``matches_execplan_filename_policy`` when strict filename-shape validation
    is needed.
    """
    match = EXECPLAN_FILENAME_RE.match(filename)
    if match is None:
        return None
    plan_id = match.group("id")
    date_token = match.group("date")
    sequence = int(match.group("sequence"))
    return plan_id, date_token, sequence


def extract_execplan_id_from_filename(filename: str) -> str | None:
    parsed = parse_execplan_filename(filename)
    if parsed is None:
        return None
    plan_id, _, _ = parsed
    return plan_id


def matches_execplan_filename_policy(filename: str) -> bool:
    """
    Validate filename format policy independently from canonical identity extraction.

    Allowed policy forms:
    - EP-YYYYMMDD-NNN.md
    - EP-YYYYMMDD-NNN_<slug>.md
    - EP-YYYYMMDD-NNN-<slug>.md
    """
    return EXECPLAN_FILENAME_POLICY_RE.fullmatch(filename) is not None
