"""Pre-execution governance decorator for AI agent actions.

Usage::

    from agec import guard

    @guard(
        intent="send_email",
        purpose="customer_support",
        allowed_tools=["gmail.send"],
        legal_basis="consent",
    )
    def send_email() -> str:
        return "Email sent."
"""

from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar

from .core import AGEC, AGECTransitionError, DataPermissions, ExecutionPath, Intent
from .policies import Policy
from .validator import AGECValidator

F = TypeVar("F", bound=Callable[..., Any])


class AGECBlockedError(PermissionError):
    """Raised when the AGEC validator denies execution.

    Attributes:
        reason: Human-readable denial reason from the validator.
        agec: The :class:`~agec.core.AGEC` context that was denied.
    """

    def __init__(self, reason: str, agec: AGEC) -> None:
        super().__init__(reason)
        self.reason = reason
        self.agec = agec


def guard(
    *,
    intent: str,
    purpose: str,
    allowed_tools: list[str],
    legal_basis: str = "consent",
    data_categories: list[str] | None = None,
    minimum_intent_confidence: float = 0.7,
    intent_confidence: float = 1.0,
) -> Callable[[F], F]:
    """Decorator that enforces AGEC governance before function execution.

    The :class:`~agec.policies.Policy` and
    :class:`~agec.validator.AGECValidator` are created **once** at
    decoration time to avoid per-call overhead. A fresh
    :class:`~agec.core.AGEC` context is created on every invocation to
    ensure independent TTL and audit tracking per call.

    Args:
        intent: Intent type string, e.g. ``"send_email"``.
        purpose: Data processing purpose, e.g. ``"customer_support"``.
        allowed_tools: List of tool identifiers permitted by this action.
        legal_basis: GDPR legal basis (default ``"consent"``).
        data_categories: Optional list of personal data categories.
        minimum_intent_confidence: Minimum acceptable confidence score
            (default ``0.7``).
        intent_confidence: Confidence score to assign to this intent
            (default ``1.0``).

    Returns:
        A decorator that wraps the target function with AGEC governance.

    Raises:
        AGECBlockedError: If the validator denies execution.

    Example::

        @guard(intent="send_email", purpose="support",
               allowed_tools=["gmail.send"])
        def send_email() -> str:
            return "Email sent."
    """
    # Build policy once at decoration time — not per call.
    _policy = Policy(
        allowed_intents=[intent],
        allowed_tools=allowed_tools,
        allowed_purposes=[purpose],
        allowed_legal_bases=[legal_basis],
        minimum_intent_confidence=minimum_intent_confidence,
    )
    _validator = AGECValidator(_policy)

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Fresh AGEC context per call (independent TTL & audit ID).
            agec = AGEC(
                intent=Intent(type=intent, confidence=intent_confidence),
                context={"function": func.__name__},
                execution_path=ExecutionPath(
                    path_id=f"{func.__name__}_path",
                    steps=allowed_tools,
                ),
                data_permissions=DataPermissions(
                    purpose=purpose,
                    legal_basis=legal_basis,
                    allowed_operations=["execute"],
                    data_categories=data_categories or [],
                ),
            )
            result = _validator.validate(agec)
            if not result.allowed:
                raise AGECBlockedError(result.reason, agec)

            agec.start_execution()
            try:
                return func(*args, **kwargs)
            finally:
                try:
                    agec.complete()
                except AGECTransitionError:
                    pass  # Guard should not raise on cleanup.

        return wrapper  # type: ignore[return-value]

    return decorator
