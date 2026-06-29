"""LangGraph-style node guard demo using state-aware factories."""

from agec import Context, ExecutionPath, Intent, wrap_langgraph_node


def send_campaign_node(state: dict[str, object]) -> dict[str, object]:
    return {**state, "email_status": "sent"}


def main() -> None:
    guarded_node = wrap_langgraph_node(
        send_campaign_node,
        intent=lambda state: Intent(
            type="send_price_list",
            source=str(state["source"]),  # type: ignore[index]
            confidence=float(state["confidence"]),  # type: ignore[index]
        ),
        context=lambda state: Context(facts=dict(state["facts"])),  # type: ignore[index]
        execution_path=lambda state: ExecutionPath(
            steps=list(state["steps"]),  # type: ignore[index]
            approved_path_id=str(state["approved_path_id"]),  # type: ignore[index]
        ),
    )

    result = guarded_node(
        {
            "source": "user_request",
            "confidence": 0.91,
            "facts": {
                "price_list_status": "current",
                "campaign_status": "active",
                "customer_segment": "premium",
            },
            "steps": [
                "crm.read_customers",
                "pricing.get_latest_list",
                "crm.filter_segment",
                "email.send_campaign",
            ],
            "approved_path_id": "price_campaign_v1",
        }
    )

    print("AGEC LangGraph-style node guard demo")
    print(f"Node result: {result}")


if __name__ == "__main__":
    main()
