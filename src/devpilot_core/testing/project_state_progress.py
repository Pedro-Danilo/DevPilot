"""Ordering helpers for cumulative POST-H and POST-H-EVAL identifiers.

Historical contracts compare project-state identifiers to prove that the
repository has advanced beyond a previously closed POST-H backlog.  The
POST-H-EVAL namespace starts after the numbered POST-H sequence, so evaluation
identifiers must compare greater than every numbered POST-H identifier while
remaining strict about unsupported formats.
"""
from __future__ import annotations

import re

_NUMBERED_POST_H = re.compile(r"^POST-H-(?P<number>\d{3})(?:-[A-Z0-9]+(?:-[A-Z0-9]+)*)?$")
_EVALUATION_POST_H = re.compile(r"^POST-H-EVAL-(?P<number>\d{3})(?:-[A-Z0-9]+(?:-[A-Z0-9]+)*)?$")
_EVALUATION_RANK_BASE = 10_000


def post_h_progress_rank(value: str) -> int:
    """Return a monotonic rank for supported POST-H project-state identifiers.

    Examples:
        POST-H-034 -> 34
        POST-H-034-CLOSURE -> 34
        POST-H-EVAL-002 -> 10002
        POST-H-EVAL-002-01-A -> 10002

    Evaluation hitos intentionally rank after the numbered POST-H backlog
    sequence because they consume the closed industrial baseline rather than
    reopening or preceding it.
    """
    if not isinstance(value, str):
        raise AssertionError(f"Expected POST-H identifier string, got {type(value).__name__}")

    numbered = _NUMBERED_POST_H.fullmatch(value)
    if numbered is not None:
        return int(numbered.group("number"))

    evaluation = _EVALUATION_POST_H.fullmatch(value)
    if evaluation is not None:
        return _EVALUATION_RANK_BASE + int(evaluation.group("number"))

    raise AssertionError(f"Unsupported POST-H project-state identifier: {value!r}")
