"""AGEC SDK.

AGEC is a pre-execution governance layer for AI agents. It validates
``Intent + Context + ExecutionPath`` immediately before tool execution.
"""

from .audit import AuditEvent, AuditLog
from .client import AGEC
from .decisions import GovernanceDecision
from .models import Context, ExecutionPath, Intent
from .validator import AGECValidator, validate

__version__ = "0.1.0"

__all__ = [
    "AGEC",
    "AGECValidator",
    "AuditEvent",
    "AuditLog",
    "Context",
    "ExecutionPath",
    "GovernanceDecision",
    "Intent",
    "validate",
]
