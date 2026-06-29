"""Example 08: Sales campaign governance.

Scenario:
    A sales agent wants to send the latest approved price list to active
    enterprise customers. Before execution, AGEC validates:

    1. Intent: Why is this action happening?
    2. Context: Is the business context valid right now?
    3. Execution Path: Is the agent following the approved execution path?

Run:
    PYTHONPATH=src python examples/08_sales_campaign.py
"""

from __future__ import annotations

from pathlib import Path

from agec import AGEC, AuditLog, Context, ExecutionPath, GovernanceDecision, Intent

APPROVED_PATHS = {
    "sales_price_campaign_v1": [
        "crm.read_customers",
        "crm.filter_enterprise",
        "crm.filter_active_last_quarter",
        "pricing.retrieve_approved_price_list",
        "email.generate_standard_campaign",
        "email.send_campaign",
    ]
}

AUDIT_FILE = Path("sales_campaign_audit.jsonl")


def print_decision(title: str, decision: GovernanceDecision) -> None:
    """Print a readable governance decision."""
    print(f"\n=== {title} ===")
    print(f"AGEC ID: {decision.agec_id}")
    print(f"Status: {decision.status}")
    print(f"Reason: {decision.reason}")
    print(
        "Scores:",
        {
            "intent": decision.intent_score,
            "context": decision.context_score,
            "path": decision.path_score,
        },
    )
    print(f"Audit ID: {decision.audit_id}")


def _agec() -> AGEC:
    return AGEC(approved_paths=APPROVED_PATHS, audit_log=AUDIT_LOG)


AUDIT_LOG = AuditLog()


def valid_sales_campaign() -> None:
    """A valid sales campaign execution plan."""
    decision = _agec().validate(
        intent=Intent(
            type="send_price_list_to_enterprise_customers",
            source="user_request",
            confidence=0.93,
        ),
        context=Context(
            facts={
                "campaign_status": "active",
                "price_list_status": "approved",
                "price_list_version": "v8",
                "customer_segment": "enterprise_active_last_quarter",
                "recipient_overlap": False,
                "previous_execution_duplicate": False,
            }
        ),
        execution_path=ExecutionPath(
            approved_path_id="sales_price_campaign_v1",
            steps=APPROVED_PATHS["sales_price_campaign_v1"],
        ),
    )
    print_decision("VALID SALES CAMPAIGN", decision)


def blocked_bad_context() -> None:
    """AGEC pauses execution because the price list is not approved."""
    decision = _agec().validate(
        intent=Intent(
            type="send_price_list_to_enterprise_customers",
            source="user_request",
            confidence=0.93,
        ),
        context=Context(
            facts={
                "campaign_status": "active",
                "price_list_status": "pending",
                "price_list_approval": "invalid",
                "price_list_version": "v8_pending",
                "customer_segment": "enterprise_active_last_quarter",
                "recipient_overlap": False,
            }
        ),
        execution_path=ExecutionPath(
            approved_path_id="sales_price_campaign_v1",
            steps=APPROVED_PATHS["sales_price_campaign_v1"],
        ),
    )
    print_decision("BLOCKED: PRICE LIST NOT APPROVED", decision)


def blocked_modified_execution_path() -> None:
    """AGEC blocks execution because the agent added an unapproved churn step."""
    decision = _agec().validate(
        intent=Intent(
            type="send_price_list_to_enterprise_customers",
            source="user_request",
            confidence=0.93,
        ),
        context=Context(
            facts={
                "campaign_status": "active",
                "price_list_status": "approved",
                "price_list_version": "v8",
                "customer_segment": "enterprise_active_last_quarter",
                "recipient_overlap": False,
            }
        ),
        execution_path=ExecutionPath(
            approved_path_id="sales_price_campaign_v1",
            steps=[
                "crm.read_customers",
                "crm.filter_enterprise",
                "crm.filter_active_last_quarter",
                "crm.read_churn_score",
                "pricing.retrieve_approved_price_list",
                "email.generate_discount_campaign",
                "email.send_campaign",
            ],
        ),
    )
    print_decision("BLOCKED: EXECUTION PATH MODIFIED", decision)


def needs_review_ambiguous_intent() -> None:
    """AGEC requests review because the intent confidence is too low."""
    decision = _agec().validate(
        intent=Intent(
            type="send_price_list_to_enterprise_customers",
            source="agent_inference",
            confidence=0.51,
        ),
        context=Context(
            facts={
                "campaign_status": "active",
                "price_list_status": "approved",
                "price_list_version": "v8",
                "customer_segment": "enterprise_active_last_quarter",
                "recipient_overlap": False,
            }
        ),
        execution_path=ExecutionPath(
            approved_path_id="sales_price_campaign_v1",
            steps=APPROVED_PATHS["sales_price_campaign_v1"],
        ),
    )
    print_decision("REVIEW: AMBIGUOUS INTENT", decision)


def main() -> None:
    valid_sales_campaign()
    blocked_bad_context()
    blocked_modified_execution_path()
    needs_review_ambiguous_intent()
    AUDIT_LOG.save_json(AUDIT_FILE, append=True)
    print(f"\nAudit file: {AUDIT_FILE.resolve()}")


if __name__ == "__main__":
    main()
