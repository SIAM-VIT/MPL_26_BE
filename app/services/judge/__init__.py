"""Code-execution sandbox client.

Two interchangeable backends:

  * ``PistonClient`` - runs code via cloud / local Piston execution engine.
  * ``MockJudge``    - runs code locally for development.

Switch with the ``JUDGE_BACKEND`` env var ("piston" | "mock"). Default is "piston".

Submodules:
    base        JudgeJob / JudgeOutcome DTOs + status constants
    execution   local subprocess helpers (mock backend only)
    mock        MockJudge
    piston      PistonClient (HTTP submission)

This package re-exports the public names, so existing imports such as
``from app.services.judge import JudgeJob, get_judge`` keep working.
"""
from app.core.config import settings
from app.services.judge.base import (
    JudgeJob,
    JudgeOutcome,
    PENDING_STATUS_IDS,
    STATUS_ACCEPTED,
    STATUS_WRONG_ANSWER,
    STATUS_TIME_LIMIT,
    STATUS_COMPILATION_ERROR,
    STATUS_INTERNAL_ERROR,
)
from app.services.judge.mock import MockJudge
from app.services.judge.piston import PistonClient

# ─────────────────────────────────────────────────────────────────────────────
# Factory
# ─────────────────────────────────────────────────────────────────────────────

_client = None


def get_judge():
    """Return the configured judge backend (cached)."""
    global _client
    if _client is None:
        backend = settings.JUDGE_BACKEND.lower()
        if backend == "mock":
            _client = MockJudge()
        else:
            _client = PistonClient()
    return _client


def reset_judge() -> None:
    global _client
    _client = None


__all__ = [
    "JudgeJob", "JudgeOutcome",
    "PENDING_STATUS_IDS", "STATUS_ACCEPTED", "STATUS_WRONG_ANSWER",
    "STATUS_TIME_LIMIT", "STATUS_COMPILATION_ERROR", "STATUS_INTERNAL_ERROR",
    "MockJudge", "PistonClient",
    "get_judge", "reset_judge",
]
