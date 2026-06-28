"""Comprehensive test suite for the AGEC SDK."""

import time
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from agec import (
    AGEC,
    AGECBlockedError,
    AGECStatus,
    AGECTransitionError,
    AGECValidator,
    AuditLog,
    DataPermissions,
    ExecutionPath,
    Intent,
    Policy,
    guard,
    validate,
)


def _make_policy(**overrides) -> Policy:
    """Return a minimal valid policy with optional field overrides."""
    defaults = dict(
        allowed_intents=["send_email"],
        allowed_tools=["gmail.send"],
        allowed_purposes=["customer_support"],
        allowed_legal_bases=["consent"],
    )
    defaults.update(overrides)
    return Policy(**defaults)


def _make_agec(**overrides) -> AGEC:
    """Return a minimal valid AGEC context with optional field overrides."""
    defaults = dict(
        intent=Intent(type="send_email", confidence=0.95),
        context={"user_id": "123"},
        execution_path=ExecutionPath(path_id="email_path", steps=["gmail.send"]),
        data_permissions=DataPermissions(
            purpose="customer_support",
            legal_basis="consent",
            allowed_operations=["send"],
            data_categories=["email"],
        ),
    )
    defaults.update(overrides)
    return AGEC(**defaults)


# ---------------------------------------------------------------------------
# Validator — allow scenarios
# ---------------------------------------------------------------------------


class TestValidatorAllows(unittest.TestCase):
    def test_valid_agec_is_allowed(self):
        policy = _make_policy()
        agec = _make_agec()
        result = AGECValidator(policy).validate(agec)
        self.assertTrue(result.allowed)
        self.assertEqual(agec.status, AGECStatus.ACTIVE)

    def test_audit_log_records_allow_event(self):
        policy = _make_policy()
        agec = _make_agec()
        log = AuditLog()
        AGECValidator(policy, audit_log=log).validate(agec)
        self.assertEqual(len(log.events), 1)
        self.assertEqual(log.events[0].event_type, "validation.allowed")

    def test_convenience_validate_function(self):
        result = validate(_make_agec(), _make_policy())
        self.assertTrue(result.allowed)


# ---------------------------------------------------------------------------
# Validator — deny scenarios
# ---------------------------------------------------------------------------


class TestValidatorDenies(unittest.TestCase):
    def test_expired_agec_is_denied(self):
        agec = _make_agec(ttl_seconds=0, created_at=time.time() - 1)
        result = AGECValidator(_make_policy()).validate(agec)
        self.assertFalse(result.allowed)
        self.assertIn("expired", result.reason.lower())
        self.assertEqual(agec.status, AGECStatus.CANCELLED)

    def test_disallowed_intent_is_denied(self):
        policy = _make_policy(allowed_intents=["other_intent"])
        agec = _make_agec()
        result = AGECValidator(policy).validate(agec)
        self.assertFalse(result.allowed)
        self.assertIn("Intent not allowed", result.reason)
        self.assertEqual(agec.status, AGECStatus.SUSPENDED)

    def test_low_confidence_intent_is_denied(self):
        agec = _make_agec(intent=Intent(type="send_email", confidence=0.5))
        policy = _make_policy(minimum_intent_confidence=0.7)
        result = AGECValidator(policy).validate(agec)
        self.assertFalse(result.allowed)
        self.assertIn("confidence", result.reason.lower())

    def test_empty_execution_path_is_denied(self):
        agec = _make_agec(
            execution_path=ExecutionPath(path_id="empty_path", steps=[])
        )
        result = AGECValidator(_make_policy()).validate(agec)
        self.assertFalse(result.allowed)
        self.assertIn("empty", result.reason.lower())

    def test_disallowed_tool_is_denied(self):
        agec = _make_agec(
            execution_path=ExecutionPath(path_id="p", steps=["forbidden.tool"])
        )
        result = AGECValidator(_make_policy()).validate(agec)
        self.assertFalse(result.allowed)
        self.assertIn("Tool not allowed", result.reason)

    def test_disallowed_purpose_is_denied(self):
        policy = _make_policy(allowed_purposes=["internal_use"])
        agec = _make_agec()
        result = AGECValidator(policy).validate(agec)
        self.assertFalse(result.allowed)
        self.assertIn("Purpose not allowed", result.reason)

    def test_disallowed_legal_basis_is_denied(self):
        policy = _make_policy(allowed_legal_bases=["contract"])
        agec = _make_agec()
        result = AGECValidator(policy).validate(agec)
        self.assertFalse(result.allowed)
        self.assertIn("Legal basis not allowed", result.reason)

    def test_blocked_data_category_is_denied(self):
        policy = Policy(
            allowed_intents=["send_email"],
            allowed_tools=["gmail.send"],
            allowed_purposes=["customer_support"],
            allowed_legal_bases=["consent"],
            blocked_data_categories=["biometric"],
        )
        agec = _make_agec(
            data_permissions=DataPermissions(
                purpose="customer_support",
                legal_basis="consent",
                allowed_operations=["send"],
                data_categories=["email", "biometric"],
            )
        )
        result = AGECValidator(policy).validate(agec)
        self.assertFalse(result.allowed)
        self.assertIn("Blocked data category", result.reason)

    def test_deny_is_recorded_in_audit_log(self):
        policy = _make_policy(allowed_intents=["other"])
        agec = _make_agec()
        log = AuditLog()
        AGECValidator(policy, audit_log=log).validate(agec)
        self.assertEqual(len(log.events), 1)
        self.assertEqual(log.events[0].event_type, "validation.denied")


# ---------------------------------------------------------------------------
# Guard decorator
# ---------------------------------------------------------------------------


class TestGuard(unittest.TestCase):
    def test_guard_allows_valid_function(self):
        @guard(
            intent="send_email",
            purpose="customer_support",
            allowed_tools=["gmail.send"],
        )
        def send_email() -> str:
            return "sent"

        self.assertEqual(send_email(), "sent")

    def test_guard_blocks_low_confidence_intent(self):
        @guard(
            intent="transfer_money",
            purpose="approved_payment",
            allowed_tools=["bank.transfer"],
            intent_confidence=0.48,
        )
        def transfer_money() -> str:
            return "transferred"

        with self.assertRaises(AGECBlockedError) as ctx:
            transfer_money()

        self.assertEqual(ctx.exception.reason, "Intent confidence below threshold.")

    def test_guard_blocked_error_carries_agec(self):
        @guard(
            intent="restricted",
            purpose="unknown",
            allowed_tools=["secret.tool"],
            intent_confidence=0.1,
        )
        def restricted_action() -> str:
            return "done"

        with self.assertRaises(AGECBlockedError) as ctx:
            restricted_action()

        self.assertIsNotNone(ctx.exception.agec.agec_id)

    def test_guard_policy_built_once(self):
        """Policy and validator should be shared across calls."""
        call_count = 0

        @guard(
            intent="read_file",
            purpose="analysis",
            allowed_tools=["fs.read"],
        )
        def read_file() -> str:
            nonlocal call_count
            call_count += 1
            return "data"

        read_file()
        read_file()
        self.assertEqual(call_count, 2)


# ---------------------------------------------------------------------------
# Status state machine
# ---------------------------------------------------------------------------


class TestAGECStateMachine(unittest.TestCase):
    def test_valid_lifecycle(self):
        agec = _make_agec()
        agec.activate()
        agec.start_execution()
        agec.complete()
        self.assertEqual(agec.status, AGECStatus.COMPLETED)

    def test_invalid_transition_raises(self):
        agec = _make_agec()
        with self.assertRaises(AGECTransitionError):
            agec.complete()  # AWAITING_VALIDATION → COMPLETED not allowed

    def test_cannot_execute_without_activation(self):
        agec = _make_agec()
        with self.assertRaises(AGECTransitionError):
            agec.start_execution()


# ---------------------------------------------------------------------------
# AuditLog persistence
# ---------------------------------------------------------------------------


class TestAuditLogPersistence(unittest.TestCase):
    def test_save_and_load_json(self):
        log = AuditLog()
        log.record("id-1", "validation.allowed", "Passed.", {"intent": "send_email"})
        log.record("id-2", "validation.denied", "Blocked.", {"intent": "send_sms"})

        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "audit.jsonl"
            log.save_json(path)

            restored = AuditLog.load_json(path)

        self.assertEqual(len(restored.events), 2)
        self.assertEqual(restored.events[0].agec_id, "id-1")
        self.assertEqual(restored.events[1].event_type, "validation.denied")

    def test_save_json_append_mode(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "audit.jsonl"

            log1 = AuditLog()
            log1.record("id-1", "validation.allowed", "Passed.", {})
            log1.save_json(path)

            log2 = AuditLog()
            log2.record("id-2", "validation.denied", "Blocked.", {})
            log2.save_json(path, append=True)

            restored = AuditLog.load_json(path)

        self.assertEqual(len(restored.events), 2)

    def test_to_list_returns_plain_dicts(self):
        log = AuditLog()
        log.record("x", "validation.allowed", "OK", {})
        result = log.to_list()
        self.assertIsInstance(result, list)
        self.assertIsInstance(result[0], dict)


# ---------------------------------------------------------------------------
# ExecutionPath
# ---------------------------------------------------------------------------


class TestExecutionPath(unittest.TestCase):
    def test_deterministic_hash_is_stable(self):
        path = ExecutionPath(path_id="p", steps=["a", "b", "c"])
        self.assertEqual(path.deterministic_hash(), path.deterministic_hash())

    def test_different_steps_produce_different_hash(self):
        p1 = ExecutionPath(path_id="p", steps=["a", "b"])
        p2 = ExecutionPath(path_id="p", steps=["b", "a"])
        self.assertNotEqual(p1.deterministic_hash(), p2.deterministic_hash())


if __name__ == "__main__":
    unittest.main()
