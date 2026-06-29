"""Basic AGEC validation demo."""

from agec import AGEC, Context, ExecutionPath, Intent


def main() -> None:
    agec = AGEC()

    decision = agec.validate(
        intent=Intent(
            type="send_price_list",
            source="user_request",
            confidence=0.91,
        ),
        context=Context(
            facts={
                "price_list_status": "current",
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

    print("AGEC basic validation")
    print(f"Decision: {decision.status}")
    print(f"Reason: {decision.reason}")
    print(f"Audit ID: {decision.audit_id}")


if __name__ == "__main__":
    main()
