"""Context validation helpers."""

from __future__ import annotations

from typing import Any

from .models import Context

_INVALID_VALUES = {"invalid", "stale", "expired", "revoked", "blocked"}


def validate_context(context: Context) -> tuple[str, float, str]:
    """Return ``(status, score, reason)`` for context facts."""
    if not context.facts:
        return "review", 0.0, "Context is missing."

    if context.context_hash and context.context_hash != context.deterministic_hash():
        return "suspend", 0.0, "Context hash does not match the supplied facts."

    invalid_fact = _find_invalid_fact(context.facts)
    if invalid_fact:
        return "suspend", 0.0, f"Context fact is invalid: {invalid_fact}"

    score = min(1.0, 0.70 + (0.06 * len(context.facts)))
    return "allow", round(score, 2), "Context validated."


def _find_invalid_fact(facts: dict[str, Any]) -> str | None:
    for key, value in facts.items():
        if value is None:
            return key
        if isinstance(value, str) and value.strip().lower() in _INVALID_VALUES:
            return key
    return None
