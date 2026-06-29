"""Public data models for the AGEC SDK."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class Intent:
    """Declared purpose of the next agent execution."""

    type: str
    source: str
    confidence: float


@dataclass(slots=True)
class Context:
    """Runtime facts used to validate whether execution is appropriate."""

    facts: dict[str, Any] = field(default_factory=dict)
    context_hash: str | None = None

    def deterministic_hash(self) -> str:
        """Return a stable hash for the current facts."""
        raw = json.dumps(self.facts, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()


@dataclass(slots=True)
class ExecutionPath:
    """Ordered tool path the agent is about to execute."""

    steps: list[str]
    approved_path_id: str | None = None

    def deterministic_hash(self) -> str:
        """Return a stable hash for the ordered tool list."""
        raw = json.dumps(self.steps, separators=(",", ":"))
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()
