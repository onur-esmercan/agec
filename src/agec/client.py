"""AGEC SDK client."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, TypeVar

from .audit import AuditLog
from .decisions import GovernanceDecision
from .models import Context, ExecutionPath, Intent
from .path import ApprovedPathRegistry
from .validator import AGECValidator

F = TypeVar("F", bound=Callable[..., Any])


class AGEC:
    """Pre-execution governance client.

    AGEC is not an agent framework. It validates intent, context, and the
    planned execution path immediately before tool execution.
    """

    def __init__(
        self,
        *,
        approved_paths: dict[str, list[str]] | None = None,
        audit_log: AuditLog | None = None,
        minimum_intent_confidence: float = 0.70,
    ) -> None:
        self.audit_log = audit_log or AuditLog()
        self.validator = AGECValidator(
            path_registry=ApprovedPathRegistry(approved_paths),
            audit_log=self.audit_log,
            minimum_intent_confidence=minimum_intent_confidence,
        )

    def validate(
        self,
        intent: Intent,
        context: Context,
        execution_path: ExecutionPath,
    ) -> GovernanceDecision:
        """Validate ``Intent + Context + ExecutionPath`` before execution."""
        return self.validator.validate(intent, context, execution_path)

    def wrap_callable(
        self,
        func: F,
        *,
        intent: Intent,
        context: Context,
        execution_path: ExecutionPath,
    ) -> Callable[..., Any]:
        """Return a small OpenAI Agents/LangGraph-friendly guarded callable."""

        def guarded(*args: Any, **kwargs: Any) -> Any:
            decision = self.validate(intent, context, execution_path)
            if decision.status != "allow":
                raise PermissionError(decision.reason)
            return func(*args, **kwargs)

        return guarded

__all__ = ["AGEC"]
