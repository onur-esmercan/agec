# AGEC

Pre-execution governance layer for AI agents.

Every AI agent action should be authorized before execution. AGEC validates
intent, semantic context, execution path, and data processing permissions
before any tool call is executed. It provides deterministic authorization,
replayable decisions, and auditability for autonomous AI agents.

---

## Installation

```bash
pip install agec
```

## Quick Start

```python
from agec import guard, AGECBlockedError

@guard(
    intent="send_email",
    purpose="customer_support",
    allowed_tools=["gmail.send"],
    legal_basis="consent",
)
def send_email() -> str:
    return "Email sent."


@guard(
    intent="transfer_money",
    purpose="unknown",
    allowed_tools=["bank.transfer"],
    intent_confidence=0.48,         # below the 0.7 threshold
)
def unsafe_transfer() -> str:
    return "Transferred $1M."


print(send_email())                 # → Email sent.

try:
    unsafe_transfer()
except AGECBlockedError as exc:
    print("AGEC BLOCKED EXECUTION")
    print(f"Reason:   {exc.reason}")
    print(f"Audit ID: {exc.agec.agec_id}")
```

If validation fails, execution is blocked **before** the wrapped function runs.

---

## Why AGEC?

Traditional authorization systems answer:

```text
Can this identity access this resource?
```

AGEC answers a different question:

```text
Should this exact action execute right now?
```

AGEC introduces a mandatory governance layer between agent planning and tool
execution — combining intent validation, policy enforcement, and tamper-evident
audit logging in a single decorator.

---

## What AGEC Validates

| Check | What it enforces |
|---|---|
| **Intent** | Declared intent must be in the policy allowlist |
| **Confidence** | Intent confidence must meet the minimum threshold |
| **Execution path** | Every tool step must be explicitly permitted |
| **Purpose** | Data processing purpose must be allowed |
| **Legal basis** | GDPR-aligned legal basis must be declared and allowed |
| **Data categories** | Blocked data categories are rejected before execution |
| **Expiry (TTL)** | Stale contexts are cancelled automatically |

---

## Architecture

```text
User
  │
AI Agent (planning)
  │
AGEC  ◄─── Policy + Validator
  │              │
  │         AuditLog ──► audit.jsonl (optional)
  │
Tool Execution
```

---

## Lower-Level API

```python
from agec import AGEC, Intent, ExecutionPath, DataPermissions, Policy, AGECValidator

policy = Policy(
    allowed_intents=["send_email"],
    allowed_tools=["gmail.send"],
    allowed_purposes=["customer_support"],
    allowed_legal_bases=["consent", "contract"],
)

agec = AGEC(
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

validator = AGECValidator(policy)
result = validator.validate(agec)

print(result.allowed)   # True
print(result.reason)    # AGEC validation passed.
print(agec.status)      # AGECStatus.ACTIVE
```

### Persisting the Audit Log

```python
from agec import AuditLog

log = AuditLog()
# ... pass log to AGECValidator(policy, audit_log=log) ...

# Save all recorded events to disk
log.save_json("audit.jsonl")

# Reload later for replay or compliance review
restored = AuditLog.load_json("audit.jsonl")
```

---

## Roadmap

- [ ] OpenAI Agents SDK adapter
- [ ] LangGraph adapter
- [ ] CrewAI adapter
- [ ] AutoGen adapter
- [ ] CLI demo runner
- [ ] Policy manifest (YAML/JSON) support
- [x] Replayable audit log (JSON persistence)
- [x] Deterministic execution path hashing

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## Changelog

See [CHANGELOG.md](CHANGELOG.md).

## License

Apache-2.0
