"""Tests for the AGEC SDK v0.1 API."""

from pathlib import Path
from tempfile import TemporaryDirectory

from agec import AGEC, AuditLog, Context, ExecutionPath, Intent, validate


def _intent(confidence: float = 0.91) -> Intent:
    return Intent(
        type="send_price_list",
        source="user_request",
        confidence=confidence,
    )


def _context(**facts: object) -> Context:
    return Context(
        facts=facts
        or {
            "price_list_status": "current",
            "campaign_status": "active",
            "customer_segment": "premium",
        }
    )


def _path(steps: list[str] | None = None, path_id: str | None = "price_campaign_v1") -> ExecutionPath:
    return ExecutionPath(
        steps=steps
        or [
            "crm.read_customers",
            "pricing.get_latest_list",
            "crm.filter_segment",
            "email.send_campaign",
        ],
        approved_path_id=path_id,
    )


def test_valid_intent_context_and_path_are_allowed() -> None:
    decision = AGEC().validate(_intent(), _context(), _path())

    assert decision.status == "allow"
    assert decision.intent_score == 0.91
    assert decision.context_score == 0.88
    assert decision.path_score == 1.0
    assert decision.agec_id.startswith("agec_")
    assert decision.audit_id.startswith("audit_")


def test_convenience_validate_function() -> None:
    decision = validate(_intent(), _context(), _path())
    assert decision.status == "allow"


def test_invalid_intent_halts() -> None:
    decision = AGEC().validate(
        Intent(type="", source="user_request", confidence=0.91),
        _context(),
        _path(),
    )
    assert decision.status == "halt"
    assert "Intent" in decision.reason


def test_ambiguous_intent_requires_review() -> None:
    decision = AGEC().validate(_intent(confidence=0.42), _context(), _path())
    assert decision.status == "review"
    assert decision.intent_score == 0.42


def test_missing_context_requires_review() -> None:
    decision = AGEC().validate(_intent(), Context(), _path())
    assert decision.status == "review"
    assert decision.reason == "Context is missing."


def test_invalid_context_suspends() -> None:
    decision = AGEC().validate(
        _intent(),
        _context(price_list_status="stale"),
        _path(),
    )
    assert decision.status == "suspend"
    assert "price_list_status" in decision.reason


def test_context_hash_mismatch_suspends() -> None:
    decision = AGEC().validate(
        _intent(),
        Context(facts={"price_list_status": "current"}, context_hash="wrong"),
        _path(),
    )
    assert decision.status == "suspend"


def test_unknown_path_requires_reauthorization() -> None:
    decision = AGEC().validate(_intent(), _context(), _path(path_id="unknown"))
    assert decision.status == "reauthorize"


def test_missing_path_id_requires_reauthorization() -> None:
    decision = AGEC().validate(_intent(), _context(), _path(path_id=None))
    assert decision.status == "reauthorize"


def test_modified_path_halts() -> None:
    decision = AGEC().validate(
        _intent(),
        _context(),
        _path(steps=["crm.read_customers", "email.send_campaign"]),
    )
    assert decision.status == "halt"
    assert "modified" in decision.reason


def test_custom_approved_path_can_be_supplied() -> None:
    agec = AGEC(approved_paths={"custom_v1": ["tool.one", "tool.two"]})
    decision = agec.validate(
        Intent(type="custom", source="test", confidence=0.99),
        Context(facts={"ready": True}),
        ExecutionPath(steps=["tool.one", "tool.two"], approved_path_id="custom_v1"),
    )
    assert decision.status == "allow"


def test_audit_log_records_decisions_and_persists_jsonl() -> None:
    log = AuditLog()
    agec = AGEC(audit_log=log)

    decision = agec.validate(_intent(), _context(), _path())

    assert len(log.events) == 1
    assert log.events[0].audit_id == decision.audit_id
    assert log.events[0].event_type == "validation.allow"

    with TemporaryDirectory() as tmp:
        audit_file = Path(tmp) / "audit.jsonl"
        log.save_json(audit_file)
        restored = AuditLog.load_json(audit_file)

    assert restored.events[0].audit_id == decision.audit_id
    assert restored.events[0].metadata["intent"] == "send_price_list"
