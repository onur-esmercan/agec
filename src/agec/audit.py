"""Audit logging for AGEC governance decisions.

Records every validation allow/deny event with a timestamp and
structured metadata. Events can be persisted to and loaded from
JSON files for replay and compliance auditing.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class AuditEvent:
    """A single governance decision recorded by AGEC.

    Attributes:
        agec_id: UUID of the AGEC context that produced this event.
        event_type: Dot-separated event type, e.g. ``validation.allowed``.
        message: Human-readable description of the outcome.
        metadata: Arbitrary structured data attached to the event.
        timestamp: ISO-8601 UTC timestamp of when the event was recorded.
    """

    agec_id: str
    event_type: str
    message: str
    metadata: dict[str, Any]
    timestamp: str


class AuditLog:
    """Append-only log of :class:`AuditEvent` records.

    Events are stored in memory and can optionally be persisted to a
    newline-delimited JSON file (one JSON object per line) for replay
    and compliance use-cases.

    Example::

        log = AuditLog()
        log.record("abc-123", "validation.allowed", "Passed.", {"intent": "send_email"})
        log.save_json("audit.jsonl")
        restored = AuditLog.load_json("audit.jsonl")
    """

    def __init__(self) -> None:
        self.events: list[AuditEvent] = []

    def record(
        self,
        agec_id: str,
        event_type: str,
        message: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Append a new event to the log.

        Args:
            agec_id: UUID of the originating AGEC context.
            event_type: Dot-separated event identifier.
            message: Human-readable outcome description.
            metadata: Optional structured data to attach.
        """
        self.events.append(
            AuditEvent(
                agec_id=agec_id,
                event_type=event_type,
                message=message,
                metadata=metadata or {},
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
        )

    def to_list(self) -> list[dict[str, Any]]:
        """Return all events as a list of plain dicts."""
        return [asdict(event) for event in self.events]

    def save_json(self, path: str | Path, *, append: bool = False) -> None:
        """Persist events to a newline-delimited JSON file.

        Args:
            path: File path to write to.
            append: If ``True``, append to an existing file instead of
                overwriting it. Useful for long-running processes.
        """
        mode = "a" if append else "w"
        with open(path, mode, encoding="utf-8") as fh:
            for event in self.events:
                fh.write(json.dumps(asdict(event), ensure_ascii=False) + "\n")

    @classmethod
    def load_json(cls, path: str | Path) -> "AuditLog":
        """Load events from a previously saved newline-delimited JSON file.

        Args:
            path: File path to read from.

        Returns:
            A new :class:`AuditLog` pre-populated with the stored events.
        """
        log = cls()
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                data = json.loads(line)
                log.events.append(AuditEvent(**data))
        return log
