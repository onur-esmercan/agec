"""Five-minute CTO demo for AGEC SDK v0.1."""

from agec import (
    AGEC,
    AGECExecutionBlocked,
    AuditLog,
    Context,
    ExecutionPath,
    Intent,
    wrap_openai_tool,
)


def _intent(confidence: float = 0.91) -> Intent:
    return Intent(type="send_price_list", source="user_request", confidence=confidence)


def _context(price_list_status: str = "current") -> Context:
    return Context(
        facts={
            "price_list_status": price_list_status,
            "campaign_status": "active",
            "customer_segment": "premium",
        }
    )


def _path(
    *,
    approved_path_id: str | None = "price_campaign_v1",
    modified: bool = False,
) -> ExecutionPath:
    steps = [
        "crm.read_customers",
        "pricing.get_latest_list",
        "crm.filter_segment",
        "email.send_campaign",
    ]
    if modified:
        steps = ["crm.read_customers", "email.send_campaign"]
    return ExecutionPath(steps=steps, approved_path_id=approved_path_id)


def _print_decision(label: str, decision_status: str, reason: str) -> None:
    print(f"{label}: {decision_status}")
    print(f"  reason: {reason}")


def _send_email_campaign() -> str:
    return "email sent"


def main() -> None:
    audit_log = AuditLog()
    agec = AGEC(audit_log=audit_log)

    print("AGEC SDK v0.1 CTO demo")
    print("Pre-execution governance layer, not an agent framework.")
    print()

    allow = agec.validate(_intent(), _context(), _path())
    _print_decision("1. Valid request", allow.status, allow.reason)

    stale_context = agec.validate(_intent(), _context("stale"), _path())
    _print_decision("2. Stale context", stale_context.status, stale_context.reason)

    modified_path = agec.validate(_intent(), _context(), _path(modified=True))
    _print_decision("3. Modified path", modified_path.status, modified_path.reason)

    unknown_path = agec.validate(_intent(), _context(), _path(approved_path_id="unknown"))
    _print_decision("4. Unknown path", unknown_path.status, unknown_path.reason)

    guarded_tool = wrap_openai_tool(
        _send_email_campaign,
        intent=_intent(),
        context=_context("stale"),
        execution_path=_path(),
        agec=agec,
    )
    try:
        guarded_tool()
    except AGECExecutionBlocked as exc:
        _print_decision("5. OpenAI-style tool guard", exc.decision.status, exc.decision.reason)
        print("  tool execution: blocked")

    print()
    print(f"Audit events recorded: {len(audit_log.events)}")
    print("Statuses: allow / review / suspend / halt / reauthorize")


if __name__ == "__main__":
    main()
