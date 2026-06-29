"""Tests for optional AGEC framework adapters."""

import pytest

from agec import (
    AGEC,
    AGECExecutionBlocked,
    Context,
    ExecutionPath,
    Intent,
    wrap_langgraph_node,
    wrap_openai_call,
    wrap_openai_tool,
)


def _intent(confidence: float = 0.91) -> Intent:
    return Intent(type="send_price_list", source="user_request", confidence=confidence)


def _context(**facts: object) -> Context:
    return Context(
        facts=facts
        or {
            "price_list_status": "current",
            "campaign_status": "active",
            "customer_segment": "premium",
        }
    )


def _path(path_id: str | None = "price_campaign_v1") -> ExecutionPath:
    return ExecutionPath(
        steps=[
            "crm.read_customers",
            "pricing.get_latest_list",
            "crm.filter_segment",
            "email.send_campaign",
        ],
        approved_path_id=path_id,
    )


def test_openai_tool_wrapper_allows_valid_execution() -> None:
    def send_campaign() -> str:
        return "sent"

    guarded = wrap_openai_tool(
        send_campaign,
        intent=_intent(),
        context=_context(),
        execution_path=_path(),
    )

    assert guarded() == "sent"


def test_openai_call_wrapper_blocks_non_allow_decision() -> None:
    called = False

    def sdk_call() -> str:
        nonlocal called
        called = True
        return "ok"

    guarded = wrap_openai_call(
        sdk_call,
        intent=_intent(confidence=0.2),
        context=_context(),
        execution_path=_path(),
    )

    with pytest.raises(AGECExecutionBlocked) as exc:
        guarded()

    assert exc.value.decision.status == "review"
    assert called is False


def test_langgraph_node_wrapper_supports_state_factories() -> None:
    def node(state: dict[str, object]) -> dict[str, object]:
        return {**state, "sent": True}

    guarded = wrap_langgraph_node(
        node,
        intent=lambda state: Intent(
            type="send_price_list",
            source=str(state["source"]),  # type: ignore[index]
            confidence=0.91,
        ),
        context=lambda state: Context(facts=dict(state["facts"])),  # type: ignore[index]
        execution_path=lambda _state: _path(),
        agec=AGEC(),
    )

    result = guarded(
        {
            "source": "user_request",
            "facts": {
                "price_list_status": "current",
                "campaign_status": "active",
                "customer_segment": "premium",
            },
        }
    )

    assert result["sent"] is True


def test_langgraph_node_wrapper_blocks_before_node_runs() -> None:
    called = False

    def node(state: dict[str, object]) -> dict[str, object]:
        nonlocal called
        called = True
        return state

    guarded = wrap_langgraph_node(
        node,
        intent=_intent(),
        context=_context(price_list_status="stale"),
        execution_path=_path(),
    )

    with pytest.raises(AGECExecutionBlocked) as exc:
        guarded({})

    assert exc.value.decision.status == "suspend"
    assert called is False
