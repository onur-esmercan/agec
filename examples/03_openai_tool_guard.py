"""OpenAI-style tool guard demo without making a network call."""

from agec import AGECExecutionBlocked, Context, ExecutionPath, Intent, wrap_openai_tool


def send_email_campaign() -> str:
    return "email sent"


def main() -> None:
    guarded_send = wrap_openai_tool(
        send_email_campaign,
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

    print("AGEC OpenAI-style tool guard demo")
    try:
        result = guarded_send()
    except AGECExecutionBlocked as exc:
        print(f"Decision: {exc.decision.status}")
        print(f"Reason: {exc.decision.reason}")
        print("OpenAI/tool call: blocked before execution")
    else:
        print(f"OpenAI/tool call: {result}")


if __name__ == "__main__":
    main()
