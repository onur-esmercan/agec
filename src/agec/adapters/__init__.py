"""Optional framework adapters for AGEC.

Adapters keep AGEC outside the agent framework itself. They validate the
planned execution immediately before a framework/tool callable runs.
"""

from .base import AGECExecutionBlocked, require_allow
from .langgraph import wrap_langgraph_node
from .openai import wrap_openai_call, wrap_openai_tool

__all__ = [
    "AGECExecutionBlocked",
    "require_allow",
    "wrap_langgraph_node",
    "wrap_openai_call",
    "wrap_openai_tool",
]
