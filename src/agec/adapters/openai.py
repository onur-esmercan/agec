"""OpenAI Agents-friendly AGEC wrappers.

The adapter intentionally avoids importing OpenAI packages. It can wrap any
OpenAI Agents tool function or SDK call right before execution.
"""

from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar

from agec.client import AGEC
from agec.models import Context, ExecutionPath, Intent

from .base import require_allow

F = TypeVar("F", bound=Callable[..., Any])


def wrap_openai_tool(
    tool: F,
    *,
    intent: Intent,
    context: Context,
    execution_path: ExecutionPath,
    agec: AGEC | None = None,
) -> F:
    """Wrap an OpenAI Agents tool callable with AGEC pre-execution validation."""

    @wraps(tool)
    def guarded(*args: Any, **kwargs: Any) -> Any:
        require_allow(
            agec=agec,
            intent=intent,
            context=context,
            execution_path=execution_path,
        )
        return tool(*args, **kwargs)

    return guarded  # type: ignore[return-value]


def wrap_openai_call(
    call: F,
    *,
    intent: Intent,
    context: Context,
    execution_path: ExecutionPath,
    agec: AGEC | None = None,
) -> F:
    """Wrap a low-level OpenAI SDK call with the same guard semantics."""
    return wrap_openai_tool(
        call,
        intent=intent,
        context=context,
        execution_path=execution_path,
        agec=agec,
    )
