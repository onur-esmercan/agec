from agec import AGEC, Context, ExecutionPath, Intent


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

print(decision.status)
print(decision.to_dict())
