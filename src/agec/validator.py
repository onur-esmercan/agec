"""Deterministic MVP validator for the AGEC SDK."""

from __future__ import annotations

import uuid

from .audit import AuditLog
from .context import validate_context
from .decisions import GovernanceDecision
from .models import Context, ExecutionPath, Intent
from .path import ApprovedPathRegistry

_PRECEDENCE = {
    "allow": 0,
    "review": 1,
    "reauthorize": 2,
    "suspend": 3,
    "halt": 4,
}


class AGECValidator:
    """Validates intent, context, and execution path before execution."""

    def __init__(
        self,
        *,
        path_registry: ApprovedPathRegistry | None = None,
        audit_log: AuditLog | None = None,
        minimum_intent_confidence: float = 0.70,
    ) -> None:
        self.path_registry = path_registry or ApprovedPathRegistry()
        self.audit_log = audit_log or AuditLog()
        self.minimum_intent_confidence = minimum_intent_confidence

    def validate(
        self,
        intent: Intent,
        context: Context,
        execution_path: ExecutionPath,
    ) -> GovernanceDecision:
        """Run the AGEC v0.1 decision table."""
        agec_id = f"agec_{uuid.uuid4().hex[:12]}"

        intent_status, intent_score, intent_reason = self._validate_intent(intent)
        context_status, context_score, context_reason = validate_context(context)
        path_status, path_score, path_reason = self.path_registry.evaluate(execution_path)

        status = max(
            [intent_status, context_status, path_status],
            key=lambda item: _PRECEDENCE[item],
        )
        reason = self._reason_for(status, intent_reason, context_reason, path_reason)

        audit_id = self.audit_log.record(
            agec_id,
            f"validation.{status}",
            reason,
            {
                "intent": intent.type,
                "intent_source": intent.source,
                "approved_path_id": execution_path.approved_path_id,
                "path_hash": execution_path.deterministic_hash(),
                "scores": {
                    "intent": intent_score,
                    "context": context_score,
                    "path": path_score,
                },
            },
        )

        return GovernanceDecision(
            agec_id=agec_id,
            status=status,  # type: ignore[arg-type]
            intent_score=round(intent_score, 2),
            context_score=round(context_score, 2),
            path_score=round(path_score, 2),
            reason=reason,
            audit_id=audit_id,
        )

    def _validate_intent(self, intent: Intent) -> tuple[str, float, str]:
        if not intent.type or not intent.source:
            return "halt", 0.0, "Intent is invalid."
        if intent.confidence < 0.0 or intent.confidence > 1.0:
            return "halt", 0.0, "Intent confidence must be between 0.0 and 1.0."
        if intent.confidence < self.minimum_intent_confidence:
            return "review", intent.confidence, "Intent is ambiguous."
        return "allow", intent.confidence, "Intent validated."

    def _reason_for(
        self,
        status: str,
        intent_reason: str,
        context_reason: str,
        path_reason: str,
    ) -> str:
        if status == "allow":
            return "Intent, context and execution path validated."
        if status == "review":
            return context_reason if context_reason != "Context validated." else intent_reason
        if status in {"reauthorize", "halt"} and path_reason != "Execution path validated.":
            return path_reason
        if status == "suspend":
            return context_reason
        return intent_reason


def validate(
    intent: Intent,
    context: Context,
    execution_path: ExecutionPath,
) -> GovernanceDecision:
    """Convenience function for one-off validation."""
    return AGECValidator().validate(intent, context, execution_path)
