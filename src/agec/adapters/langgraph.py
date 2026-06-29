"""LangGraph-friendly AGEC wrappers."""

from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar, cast

from agec.client import AGEC
from agec.models import Context, ExecutionPath, Intent

from .base import require_allow, resolve_callable_input
from .typing import CallableInput

F = TypeVar("F", bound=Callable[..., Any])


def wrap_langgraph_node(
    node: F,
    *,
    intent: Intent | Callable[[object | None], Intent],
    context: Context | Callable[[object | None], Context],
    execution_path: ExecutionPath | Callable[[object | None], ExecutionPath],
    agec: AGEC | None = None,
) -> F:
    """Wrap a LangGraph node callable with AGEC pre-execution validation.

    ``intent``, ``context`` and ``execution_path`` may be static model objects or
    factories that receive the node state as their only argument.
    """

    @wraps(node)
    def guarded(state: object | None = None, *args: Any, **kwargs: Any) -> Any:
        resolved_intent = cast(Intent, resolve_callable_input(cast(CallableInput, intent), state))
        resolved_context = cast(Context, resolve_callable_input(cast(CallableInput, context), state))
        resolved_path = cast(
            ExecutionPath,
            resolve_callable_input(cast(CallableInput, execution_path), state),
        )
        require_allow(
            agec=agec,
            intent=resolved_intent,
            context=resolved_context,
            execution_path=resolved_path,
        )
        return node(state, *args, **kwargs)

    return guarded  # type: ignore[return-value]
