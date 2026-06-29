"""Shared adapter primitives."""

from __future__ import annotations

from .typing import CallableInput
from agec.client import AGEC
from agec.decisions import GovernanceDecision
from agec.models import Context, ExecutionPath, Intent


class AGECExecutionBlocked(PermissionError):
    """Raised when AGEC blocks a pre-execution call."""

    def __init__(self, decision: GovernanceDecision) -> None:
        self.decision = decision
        super().__init__(decision.reason)


def require_allow(
    *,
    agec: AGEC | None,
    intent: Intent,
    context: Context,
    execution_path: ExecutionPath,
) -> GovernanceDecision:
    """Validate execution and raise unless the decision is ``allow``."""
    client = agec or AGEC()
    decision = client.validate(intent, context, execution_path)
    if decision.status != "allow":
        raise AGECExecutionBlocked(decision)
    return decision


def resolve_callable_input(value: CallableInput, state: object | None = None) -> object:
    """Resolve a static value or state-aware factory."""
    if callable(value):
        return value(state)
    return value
