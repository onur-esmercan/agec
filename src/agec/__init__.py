"""AGEC — Authorized Governance Execution Context.

A pre-execution governance layer for AI agents. Every agent action is
validated for intent, semantic context, execution path, and data
processing permissions before the tool call is allowed to run.

Quick start::

    from agec import guard

    @guard(
        intent="send_email",
        purpose="customer_support",
        allowed_tools=["gmail.send"],
    )
    def send_email() -> str:
        return "Email sent."
"""

from .audit import AuditEvent, AuditLog
from .core import AGEC, AGECStatus, AGECTransitionError, DataPermissions, ExecutionPath, Intent
from .guard import AGECBlockedError, guard
from .policies import DEFAULT_LEGAL_BASES, Policy
from .validator import AGECValidator, ValidationResult, validate

__version__ = "0.1.0"

__all__ = [
    "AGEC",
    "AGECStatus",
    "AGECTransitionError",
    "AGECBlockedError",
    "AGECValidator",
    "AuditEvent",
    "AuditLog",
    "DEFAULT_LEGAL_BASES",
    "DataPermissions",
    "ExecutionPath",
    "Intent",
    "Policy",
    "ValidationResult",
    "guard",
    "validate",
]
