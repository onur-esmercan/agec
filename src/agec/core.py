"""Core AGEC data models and lifecycle state machine.

AGEC (Authorized Governance Execution Context) is the central object
passed through the governance pipeline. It captures intent, execution
path, data permissions, and lifecycle state for a single agent action
request.
"""

from __future__ import annotations

import hashlib
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class AGECStatus(str, Enum):
    """Lifecycle states for an :class:`AGEC` context.

    The valid transition graph is::

        INACTIVE → AWAITING_VALIDATION → ACTIVE → EXECUTING → COMPLETED
                                      ↘ SUSPENDED
                                      ↘ CANCELLED   (expired)
    """

    INACTIVE = "inactive"
    AWAITING_VALIDATION = "awaiting_validation"
    ACTIVE = "active"
    EXECUTING = "executing"
    COMPLETED = "completed"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"


# Allowed (from_state, to_state) transitions.
_ALLOWED_TRANSITIONS: frozenset[tuple[AGECStatus, AGECStatus]] = frozenset(
    {
        (AGECStatus.INACTIVE, AGECStatus.AWAITING_VALIDATION),
        (AGECStatus.AWAITING_VALIDATION, AGECStatus.ACTIVE),
        (AGECStatus.AWAITING_VALIDATION, AGECStatus.SUSPENDED),
        (AGECStatus.AWAITING_VALIDATION, AGECStatus.CANCELLED),
        (AGECStatus.ACTIVE, AGECStatus.EXECUTING),
        (AGECStatus.ACTIVE, AGECStatus.SUSPENDED),
        (AGECStatus.ACTIVE, AGECStatus.CANCELLED),
        (AGECStatus.EXECUTING, AGECStatus.COMPLETED),
        (AGECStatus.EXECUTING, AGECStatus.SUSPENDED),
    }
)


class AGECTransitionError(RuntimeError):
    """Raised when an illegal status transition is attempted."""


@dataclass
class Intent:
    """Represents the declared intent of an agent action.

    Attributes:
        type: Intent identifier, e.g. ``"send_email"``.
        source: Origin of the intent (default ``"user"``).
        confidence: Model-assigned confidence score in ``[0.0, 1.0]``.
    """

    type: str
    source: str = "user"
    confidence: float = 1.0


@dataclass
class ExecutionPath:
    """Ordered sequence of tools that will be invoked.

    Attributes:
        path_id: Human-readable identifier for this path.
        steps: Ordered list of tool identifiers to be executed.
    """

    path_id: str
    steps: list[str]

    def deterministic_hash(self) -> str:
        """Return a SHA-256 hex digest of the ordered tool list.

        The hash is deterministic for the same sequence of steps and
        can be stored in audit logs for replay verification.
        """
        raw = "|".join(self.steps)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()


@dataclass
class DataPermissions:
    """Data processing permissions attached to an agent action.

    Attributes:
        purpose: Processing purpose, e.g. ``"customer_support"``.
        legal_basis: GDPR-aligned legal basis for processing.
        allowed_operations: Operations permitted under this context.
        data_categories: Categories of personal data involved.
        retention_seconds: Optional maximum retention window in seconds.
    """

    purpose: str
    legal_basis: str
    allowed_operations: list[str]
    data_categories: list[str] = field(default_factory=list)
    retention_seconds: int | None = None


@dataclass
class AGEC:
    """Authorized Governance Execution Context.

    The central governance object for a single agent action request.
    It captures intent, execution path, data permissions, and lifecycle
    state, and enforces valid status transitions.

    Args:
        intent: The declared intent of the action.
        context: Arbitrary key-value context (e.g. user_id, session_id).
        execution_path: Ordered list of tools to be called.
        data_permissions: Data processing permissions for this action.
        agec_id: Auto-generated UUID; can be overridden for testing.
        created_at: Unix timestamp of creation; auto-set.
        ttl_seconds: Time-to-live in seconds (default 300).
        status: Initial lifecycle state.
    """

    intent: Intent
    context: dict[str, Any]
    execution_path: ExecutionPath
    data_permissions: DataPermissions
    agec_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: float = field(default_factory=time.time)
    ttl_seconds: int = 300
    status: AGECStatus = AGECStatus.AWAITING_VALIDATION

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _transition(self, target: AGECStatus) -> None:
        """Perform a guarded status transition.

        Args:
            target: Desired next state.

        Raises:
            AGECTransitionError: If the transition is not permitted.
        """
        if (self.status, target) not in _ALLOWED_TRANSITIONS:
            raise AGECTransitionError(
                f"Invalid AGEC transition: {self.status.value!r} → {target.value!r}"
            )
        self.status = target

    # ------------------------------------------------------------------
    # Lifecycle API
    # ------------------------------------------------------------------

    def is_expired(self) -> bool:
        """Return ``True`` if the TTL has elapsed since creation."""
        return time.time() > self.created_at + self.ttl_seconds

    def activate(self) -> None:
        """Transition to :attr:`AGECStatus.ACTIVE` after validation."""
        self._transition(AGECStatus.ACTIVE)

    def suspend(self) -> None:
        """Transition to :attr:`AGECStatus.SUSPENDED` on policy failure."""
        self._transition(AGECStatus.SUSPENDED)

    def cancel(self) -> None:
        """Transition to :attr:`AGECStatus.CANCELLED` (e.g. on expiry)."""
        self._transition(AGECStatus.CANCELLED)

    def start_execution(self) -> None:
        """Transition to :attr:`AGECStatus.EXECUTING`.

        Raises:
            AGECTransitionError: If the context is not yet active.
        """
        self._transition(AGECStatus.EXECUTING)

    def complete(self) -> None:
        """Transition to :attr:`AGECStatus.COMPLETED`.

        Raises:
            AGECTransitionError: If the context is not executing.
        """
        self._transition(AGECStatus.COMPLETED)
