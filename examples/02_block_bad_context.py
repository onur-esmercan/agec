"""Show AGEC suspending execution when context is stale."""

from agec import AGEC, Context, ExecutionPath, Intent


def main() -> None:
    decision = AGEC().validate(
        intent=Intent(
            type="send_price_list",
            source="user_request",
            confidence=0.91,
        ),
        context=Context(
            facts={
                "price_list_status": "stale",
                "campaign_status": "active",
                "customer_segment": "premium",
            }
        ),
        execution_path=ExecutionPath(
            steps=[
                "crm.read_customers",
                "pricing.get_latest_list",
                "crm.filter_segment",
                "email.send_campaign",
            ],
            approved_path_id="price_campaign_v1",
        ),
    )

    print("AGEC bad context demo")
    print(f"Decision: {decision.status}")
    print(f"Reason: {decision.reason}")
    print("Tool execution: skipped before sending email")


if __name__ == "__main__":
    main()
