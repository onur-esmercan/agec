"""AGEC SDK.

AGEC is a pre-execution governance layer for AI agents. It validates
``Intent + Context + ExecutionPath`` immediately before tool execution.
"""

from .audit import AuditEvent, AuditLog
from .adapters import AGECExecutionBlocked, wrap_langgraph_node, wrap_openai_call, wrap_openai_tool
from .client import AGEC
from .decisions import GovernanceDecision
from .models import Context, ExecutionPath, Intent
from .validator import AGECValidator, validate

__version__ = "0.1.0"

__all__ = [
    "AGEC",
    "AGECExecutionBlocked",
    "AGECValidator",
    "AuditEvent",
    "AuditLog",
    "Context",
    "ExecutionPath",
    "GovernanceDecision",
    "Intent",
    "validate",
    "wrap_langgraph_node",
    "wrap_openai_call",
    "wrap_openai_tool",
]
