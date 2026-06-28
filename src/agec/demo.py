"""AGEC Pipeline Demo — CLI entry point.

This module is the entry point for the ``agec-demo`` command installed
by ``pip install agec``. It re-exports ``main`` from
``examples/pipeline_demo.py`` packaged inside the ``agec`` namespace.
"""

from __future__ import annotations

import argparse
import sys
import time

# Reconfigure stdout to UTF-8 on Windows where the default may be CP1252.
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:
        pass

from agec import (
    AGEC,
    AGECValidator,
    AuditLog,
    DataPermissions,
    ExecutionPath,
    Intent,
    Policy,
)

# ---------------------------------------------------------------------------
# ANSI colour helpers (zero external deps)
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


def _use_color() -> bool:
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


def _supports_unicode() -> bool:
    enc = getattr(sys.stdout, "encoding", "") or ""
    return enc.lower().replace("-", "") in ("utf8", "utf16", "utf32")


def _c(text: str, *codes: str) -> str:
    if not _use_color():
        return text
    return "".join(codes) + text + RESET


def _banner() -> None:
    print()
    if _supports_unicode():
        print(_c("╔══════════════════════════════════════════════════════╗", CYAN, BOLD))
        print(_c("║           AGEC  ·  Pipeline Governance Demo          ║", CYAN, BOLD))
        print(_c("╚══════════════════════════════════════════════════════╝", CYAN, BOLD))
    else:
        print(_c("+------------------------------------------------------+", CYAN, BOLD))
        print(_c("|           AGEC  .  Pipeline Governance Demo          |", CYAN, BOLD))
        print(_c("+------------------------------------------------------+", CYAN, BOLD))
    print(_c("  Pre-execution authorization layer for AI agents", DIM))
    print()


def _separator() -> None:
    print(_c("  " + "─" * 52, GREY))


def _section(title: str) -> None:
    print()
    print(_c(f"  ▶ {title}", YELLOW, BOLD))
    _separator()


# ---------------------------------------------------------------------------
# Demo scenarios
# ---------------------------------------------------------------------------

_SCENARIOS = [
    {
        "label": "Customer support agent sends a routine email",
        "intent": "send_email",
        "tool": "gmail.send",
        "purpose": "customer_support",
        "legal_basis": "consent",
        "allowed_bases": ["consent"],
        "confidence": 0.95,
        "data_categories": ["email"],
        "blocked_categories": None,
    },
    {
        "label": "Agent attempts money transfer with low-confidence intent",
        "intent": "transfer_money",
        "tool": "bank.transfer",
        "purpose": "approved_payment",
        "legal_basis": "consent",
        "allowed_bases": ["consent"],
        "confidence": 0.42,
        "data_categories": ["financial"],
        "blocked_categories": None,
    },
    {
        "label": "Agent reads medical records without approved legal basis",
        "intent": "read_records",
        "tool": "ehr.read",
        "purpose": "analytics",
        "legal_basis": "legitimate_interest",
        "allowed_bases": ["consent", "contract"],  # legitimate_interest NOT allowed
        "confidence": 0.91,
        "data_categories": ["medical"],
        "blocked_categories": None,
    },
    {
        "label": "Compliance agent accesses contract data under contract basis",
        "intent": "read_contract",
        "tool": "legal.read",
        "purpose": "contract_review",
        "legal_basis": "contract",
        "allowed_bases": ["contract"],
        "confidence": 0.88,
        "data_categories": ["legal_documents"],
        "blocked_categories": None,
    },
    {
        "label": "Agent attempts to process biometric data (blocked category)",
        "intent": "process_biometrics",
        "tool": "biometrics.scan",
        "purpose": "security",
        "legal_basis": "consent",
        "allowed_bases": ["consent"],
        "confidence": 0.97,
        "data_categories": ["biometric"],
        "blocked_categories": ["biometric"],
    },
    {
        "label": "Scheduler sends a report with no tools declared",
        "intent": "send_report",
        "tool": None,
        "purpose": "internal_reporting",
        "legal_basis": "legitimate_interest",
        "allowed_bases": ["consent", "legitimate_interest"],
        "confidence": 0.80,
        "data_categories": [],
        "blocked_categories": None,
    },
]


def _run_scenario(scenario: dict, audit_log: AuditLog, verbose: bool) -> dict:
    intent  = scenario["intent"]
    tool    = scenario["tool"]
    purpose = scenario["purpose"]
    legal   = scenario["legal_basis"]
    conf    = scenario["confidence"]
    cats    = scenario["data_categories"]
    blocked = scenario["blocked_categories"]

    steps = [tool] if tool else []

    policy = Policy(
        allowed_intents=[intent],
        allowed_tools=steps,
        allowed_purposes=[purpose],
        allowed_legal_bases=scenario.get("allowed_bases", ["consent", "contract"]),
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

    result = AGECValidator(policy, audit_log=audit_log).validate(agec)
    tool_label = tool or "(no tool)"

    if result.allowed:
        print(
            f"  {_c('✔ ALLOWED', GREEN, BOLD)}  "
            f"{_c(tool_label, WHITE)}  "
            f"{_c('→ executing…', GREY)}"
        )
        if verbose:
            print(_c(f"           agec_id={agec.agec_id}", GREY))
            print(_c(f"           path_hash={agec.execution_path.deterministic_hash()[:16]}…", GREY))
        time.sleep(0.05)
        print(f"  {_c('✔ ALLOWED', GREEN, BOLD)}  {_c(tool_label, WHITE)}  {_c('→ Done ✓', GREY)}")
    else:
        print(
            f"  {_c('✘ BLOCKED', RED, BOLD)}  "
            f"{_c(tool_label, WHITE)}  "
            f"{_c('→ ' + result.reason, GREY)}"
        )
        if verbose:
            print(_c(f"           agec_id={agec.agec_id}", GREY))
            print(_c(f"           status={agec.status.value}", GREY))

    return {
        "label": scenario["label"],
        "tool": tool_label,
        "allowed": result.allowed,
        "reason": result.reason,
        "agec_id": agec.agec_id,
    }


def main() -> None:
    """Entry point for the ``agec-demo`` CLI command."""
    parser = argparse.ArgumentParser(
        prog="agec-demo",
        description=(
            "AGEC Pipeline Demo — simulates an AI agent making tool calls "
            "and shows AGEC intercepting each one before execution."
        ),
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show agec_id and path hash for each decision.",
    )
    parser.add_argument(
        "--audit-file",
        metavar="PATH",
        default=None,
        help="Save the full audit log to a JSON-lines file (e.g. audit.jsonl).",
    )
    args = parser.parse_args()

    _banner()

    audit_log: AuditLog = AuditLog()
    results: list[dict] = []
    total = len(_SCENARIOS)

    _section(f"Simulated Agent Pipeline — {total} tool calls")
    print()

    for i, scenario in enumerate(_SCENARIOS, start=1):
        print(_c(f"  [{i}/{total}] {scenario['label']}", DIM))
        result = _run_scenario(scenario, audit_log, verbose=args.verbose)
        results.append(result)
        print()
        time.sleep(0.1)

    # Summary
    _section("Summary")
    allowed_n = sum(1 for r in results if r["allowed"])
    blocked_n = len(results) - allowed_n
    print(
        f"  {_c(str(allowed_n) + ' allowed', GREEN, BOLD)}  ·  "
        f"{_c(str(blocked_n) + ' blocked', RED, BOLD)}  "
        f"out of {len(results)} tool calls"
    )

    # Audit log
    _section("Audit Log")
    for event in audit_log.events:
        tag = (
            _c("ALLOW", GREEN) if event.event_type == "validation.allowed"
            else _c("DENY ", RED)
        )
        intent = event.metadata.get("intent", "?")
        print(
            f"  {GREY}{event.timestamp[11:19]}{RESET}  "
            f"[{tag}]  "
            f"{_c(intent, WHITE)}  "
            f"{_c(event.message, GREY)}"
        )

    if args.audit_file:
        audit_log.save_json(args.audit_file)
        print()
        print(_c(f"  Audit log saved → {args.audit_file}", CYAN))

    print()
    print(_c("  AGEC intercepted every call before execution.", DIM))
    print(_c("  Zero unauthorized tool calls reached the execution layer.", GREEN, BOLD))
    print()


if __name__ == "__main__":
    main()
