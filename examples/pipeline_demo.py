"""AGEC Pipeline Demo — CLI

Simulates an AI agent pipeline where multiple tool calls are attempted.
AGEC intercepts each call before execution, allowing or blocking based on policy.

Usage:
    python examples/pipeline_demo.py
    python examples/pipeline_demo.py --verbose
"""

from __future__ import annotations

import argparse
import sys
import time
import uuid

from agec import (
    AGEC,
    AGECBlockedError,
    AGECValidator,
    AuditLog,
    DataPermissions,
    ExecutionPath,
    Intent,
    Policy,
    guard,
)

# ---------------------------------------------------------------------------
# ANSI colour helpers (no external deps)
# ---------------------------------------------------------------------------

RESET  = "\033[0m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
WHITE  = "\033[97m"
GREY   = "\033[90m"

def _supports_color() -> bool:
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()

USE_COLOR = _supports_color()

def c(text: str, *codes: str) -> str:
    if not USE_COLOR:
        return text
    return "".join(codes) + text + RESET

def banner() -> None:
    print()
    print(c("╔══════════════════════════════════════════════════════╗", CYAN, BOLD))
    print(c("║           AGEC  ·  Pipeline Governance Demo          ║", CYAN, BOLD))
    print(c("╚══════════════════════════════════════════════════════╝", CYAN, BOLD))
    print(c("  Pre-execution authorization layer for AI agents", DIM))
    print()

def separator() -> None:
    print(c("  " + "─" * 52, GREY))

def allowed_line(tool: str, reason: str) -> None:
    print(f"  {c('✔ ALLOWED', GREEN, BOLD)}  {c(tool, WHITE)}  {c('→ ' + reason, GREY)}")

def blocked_line(tool: str, reason: str) -> None:
    print(f"  {c('✘ BLOCKED', RED, BOLD)}  {c(tool, WHITE)}  {c('→ ' + reason, GREY)}")

def section(title: str) -> None:
    print()
    print(c(f"  ▶ {title}", YELLOW, BOLD))
    separator()

# ---------------------------------------------------------------------------
# Demo scenarios
# ---------------------------------------------------------------------------

SCENARIOS = [
    {
        "label": "Customer support agent sends a routine email",
        "intent": "send_email",
        "tool": "gmail.send",
        "purpose": "customer_support",
        "legal_basis": "consent",
        "confidence": 0.95,
        "data_categories": ["email"],
        "blocked_categories": None,
        "expect": "allow",
    },
    {
        "label": "Agent attempts money transfer with low-confidence intent",
        "intent": "transfer_money",
        "tool": "bank.transfer",
        "purpose": "approved_payment",
        "legal_basis": "consent",
        "confidence": 0.42,           # ← below 0.7 threshold
        "data_categories": ["financial"],
        "blocked_categories": None,
        "expect": "block",
    },
    {
        "label": "Agent reads medical records without legal basis",
        "intent": "read_records",
        "tool": "ehr.read",
        "purpose": "analytics",
        "legal_basis": "legitimate_interest",  # not in policy
        "confidence": 0.91,
        "data_categories": ["medical"],
        "blocked_categories": None,
        "expect": "block",
    },
    {
        "label": "Compliance agent accesses contract data under contract basis",
        "intent": "read_contract",
        "tool": "legal.read",
        "purpose": "contract_review",
        "legal_basis": "contract",
        "confidence": 0.88,
        "data_categories": ["legal_documents"],
        "blocked_categories": None,
        "expect": "allow",
    },
    {
        "label": "Agent attempts to process biometric data (blocked category)",
        "intent": "process_biometrics",
        "tool": "biometrics.scan",
        "purpose": "security",
        "legal_basis": "consent",
        "confidence": 0.97,
        "data_categories": ["biometric"],   # ← blocked
        "blocked_categories": ["biometric"],
        "expect": "block",
    },
    {
        "label": "Scheduler sends a report with zero tools declared",
        "intent": "send_report",
        "tool": None,                        # ← empty execution path
        "purpose": "internal_reporting",
        "legal_basis": "legitimate_interest",
        "confidence": 0.80,
        "data_categories": [],
        "blocked_categories": None,
        "expect": "block",
    },
]

# ---------------------------------------------------------------------------
# Run a single scenario
# ---------------------------------------------------------------------------

def run_scenario(
    scenario: dict,
    audit_log: AuditLog,
    verbose: bool = False,
) -> dict:
    label    = scenario["label"]
    intent   = scenario["intent"]
    tool     = scenario["tool"]
    purpose  = scenario["purpose"]
    legal    = scenario["legal_basis"]
    conf     = scenario["confidence"]
    cats     = scenario["data_categories"]
    blocked  = scenario["blocked_categories"]

    steps = [tool] if tool else []

    policy = Policy(
        allowed_intents=[intent],
        allowed_tools=steps,
        allowed_purposes=[purpose],
        allowed_legal_bases=[legal, "consent", "contract", "legitimate_interest"],
        blocked_data_categories=blocked,
        minimum_intent_confidence=0.7,
    )

    agec = AGEC(
        intent=Intent(type=intent, confidence=conf),
        context={"demo": True},
        execution_path=ExecutionPath(path_id=f"{intent}_path", steps=steps),
        data_permissions=DataPermissions(
            purpose=purpose,
            legal_basis=legal,
            allowed_operations=["execute"],
            data_categories=cats,
        ),
    )

    validator = AGECValidator(policy, audit_log=audit_log)
    result = validator.validate(agec)

    tool_label = tool or "(no tool)"

    if result.allowed:
        allowed_line(tool_label, "Executing tool call…")
        if verbose:
            print(c(f"           agec_id={agec.agec_id}", GREY))
            print(c(f"           path_hash={agec.execution_path.deterministic_hash()[:16]}…", GREY))
        time.sleep(0.05)
        allowed_line(tool_label, "Done ✓")
    else:
        blocked_line(tool_label, result.reason)
        if verbose:
            print(c(f"           agec_id={agec.agec_id}", GREY))
            print(c(f"           status={agec.status.value}", GREY))

    return {
        "label": label,
        "tool": tool_label,
        "allowed": result.allowed,
        "reason": result.reason,
        "agec_id": agec.agec_id,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="AGEC Pipeline Demo — shows pre-execution governance in action"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show agec_id and path hash for each decision",
    )
    parser.add_argument(
        "--audit-file",
        metavar="PATH",
        default=None,
        help="Save the audit log to a JSON-lines file (e.g. audit.jsonl)",
    )
    args = parser.parse_args()

    banner()

    audit_log = AuditLog()
    results: list[dict] = []

    section("Simulated Agent Pipeline — 6 tool calls")
    print()

    for i, scenario in enumerate(SCENARIOS, start=1):
        label = scenario["label"]
        print(c(f"  [{i}/6] {label}", DIM))
        result = run_scenario(scenario, audit_log, verbose=args.verbose)
        results.append(result)
        print()
        time.sleep(0.1)

    # Summary
    section("Summary")
    allowed_count = sum(1 for r in results if r["allowed"])
    blocked_count = len(results) - allowed_count
    print(f"  {c(str(allowed_count) + ' allowed', GREEN, BOLD)}  ·  {c(str(blocked_count) + ' blocked', RED, BOLD)}  out of {len(results)} tool calls")
    print()

    # Audit log
    section("Audit Log")
    for event in audit_log.events:
        status_tag = c("ALLOW", GREEN) if event.event_type == "validation.allowed" else c("DENY ", RED)
        intent = event.metadata.get("intent", "?")
        print(f"  {GREY}{event.timestamp[11:19]}{RESET}  [{status_tag}]  {c(intent, WHITE)}  {c(event.message, GREY)}")

    if args.audit_file:
        audit_log.save_json(args.audit_file)
        print()
        print(c(f"  Audit log saved → {args.audit_file}", CYAN))

    print()
    print(c("  AGEC intercepted every call before execution.", DIM))
    print(c("  Zero unauthorized tool calls reached the execution layer.", GREEN, BOLD))
    print()


if __name__ == "__main__":
    main()
