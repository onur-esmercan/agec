"""AGEC validation engine.

Runs a deterministic, ordered series of policy checks against an
:class:`~agec.core.AGEC` context and records every decision in an
:class:`~agec.audit.AuditLog`.
"""

from __future__ import annotations

from dataclasses import dataclass

from .audit import AuditLog
from .core import AGEC
from .policies import Policy


@dataclass
class ValidationResult:
    """Outcome of a single validation run.

    Attributes:
        allowed: ``True`` if all policy checks passed.
        reason: Human-readable explanation of the outcome.
    """

    allowed: bool
    reason: str


class AGECValidator:
    """Validates an :class:`~agec.core.AGEC` context against a :class:`~agec.policies.Policy`.

    Checks are evaluated in this order:

    1. Expiry (TTL)
    2. Intent allowlist
    3. Intent confidence threshold
    4. Execution path non-empty
    5. Tool allowlist (per step)
    6. Purpose allowlist
    7. Legal basis allowlist
    8. Blocked data categories

    Every outcome — allow or deny — is recorded in the
    :class:`~agec.audit.AuditLog`.

    Args:
        policy: The :class:`~agec.policies.Policy` to validate against.
        audit_log: Optional existing :class:`~agec.audit.AuditLog` to
            append events to. A new log is created if omitted.
    """

    def __init__(self, policy: Policy, audit_log: AuditLog | None = None) -> None:
        self.policy = policy
        self.audit_log = audit_log or AuditLog()

    def validate(self, agec: AGEC) -> ValidationResult:
        """Run all policy checks against *agec*.

        Args:
            agec: The governance context to validate.

        Returns:
            A :class:`ValidationResult` indicating allow or deny.
        """
        if agec.is_expired():
            agec.cancel()
            return self._deny(agec, "AGEC expired.")

        if not self.policy.is_intent_allowed(agec.intent.type):
            agec.suspend()
            return self._deny(agec, f"Intent not allowed: {agec.intent.type}")

        if agec.intent.confidence < self.policy.minimum_intent_confidence:
            agec.suspend()
            return self._deny(agec, "Intent confidence below threshold.")

        if not agec.execution_path.steps:
            agec.suspend()
            return self._deny(agec, "Execution path is empty.")

        for tool in agec.execution_path.steps:
            if not self.policy.is_tool_allowed(tool):
                agec.suspend()
                return self._deny(agec, f"Tool not allowed: {tool}")

        if not self.policy.is_purpose_allowed(agec.data_permissions.purpose):
            agec.suspend()
            return self._deny(
                agec,
                f"Purpose not allowed: {agec.data_permissions.purpose}",
            )

        if not self.policy.is_legal_basis_allowed(agec.data_permissions.legal_basis):
            agec.suspend()
            return self._deny(
                agec,
                f"Legal basis not allowed: {agec.data_permissions.legal_basis}",
            )

        if self.policy.has_blocked_data_category(agec.data_permissions.data_categories):
            agec.suspend()
            return self._deny(agec, "Blocked data category detected.")

        agec.activate()
        self.audit_log.record(
            agec.agec_id,
            "validation.allowed",
            "AGEC validation passed.",
            {
                "intent": agec.intent.type,
                "path_hash": agec.execution_path.deterministic_hash(),
            },
        )
        return ValidationResult(True, "AGEC validation passed.")

    def _deny(self, agec: AGEC, reason: str) -> ValidationResult:
        """Record a denial event and return a denied :class:`ValidationResult`."""
        self.audit_log.record(
            agec.agec_id,
            "validation.denied",
            reason,
            {
                "intent": agec.intent.type,
                "status": agec.status.value,
            },
        )
        return ValidationResult(False, reason)


def validate(agec: AGEC, policy: Policy) -> ValidationResult:
    """Convenience function: validate *agec* against *policy*.

    Creates a throw-away :class:`AGECValidator` with a fresh
    :class:`~agec.audit.AuditLog`. Prefer constructing a validator
    directly when you need to inspect audit events afterward.

    Args:
        agec: The governance context to validate.
        policy: The policy to validate against.

    Returns:
        A :class:`ValidationResult`.
    """
    return AGECValidator(policy).validate(agec)
