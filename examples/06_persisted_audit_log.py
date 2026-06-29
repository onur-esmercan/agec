"""Persist AGEC audit events so audit IDs can be inspected later."""

from pathlib import Path

from agec import AGEC, AuditLog, Context, ExecutionPath, Intent


def main() -> None:
    audit_file = Path("agec_audit.jsonl")
    audit_log = AuditLog()
    agec = AGEC(audit_log=audit_log)

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

    audit_log.save_json(audit_file, append=True)

    print("AGEC persisted audit log demo")
    print(f"Decision: {decision.status}")
    print(f"Audit ID: {decision.audit_id}")
    print(f"Audit file: {audit_file.resolve()}")
    print("Inspect later with:")
    print("  Get-Content .\\agec_audit.jsonl")


if __name__ == "__main__":
    main()
