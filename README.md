# AGEC

AGEC SDK is a pre-execution governance layer for AI agents.

It is not an agent framework. It validates `Intent + Context + Execution Path`
immediately before an agent executes tools.

```text
Agent Reasoning
    |
AGEC SDK
    |
Tool Execution
```

## Installation

```bash
pip install agec
```

## Quick Start

```python
from agec import AGEC, Intent, Context, ExecutionPath

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
# allow / review / suspend / halt / reauthorize
```

The decision is a structured object:

```json
{
  "agec_id": "agec_123",
  "status": "allow",
  "intent_score": 0.91,
  "context_score": 0.88,
  "path_score": 1.0,
  "reason": "Intent, context and execution path validated.",
  "audit_id": "audit_456"
}
```

## Core API

```python
agec.validate(intent, context, execution_path)
```

### Models

```python
Intent(type: str, source: str, confidence: float)
Context(facts: dict, context_hash: str | None = None)
ExecutionPath(steps: list[str], approved_path_id: str | None = None)
GovernanceDecision(status, reason, intent_score, context_score, path_score)
```

## MVP Decision Logic

| Condition | Decision |
|---|---|
| Intent invalid | `halt` |
| Intent ambiguous | `review` |
| Context missing | `review` |
| Context invalid | `suspend` |
| Path unknown | `reauthorize` |
| Path modified | `halt` |
| All valid | `allow` |

## Audit Log

Every validation writes an in-memory audit event. You can persist it as JSONL:

```python
from agec import AGEC, AuditLog

audit_log = AuditLog()
agec = AGEC(audit_log=audit_log)

# ... run validations ...

audit_log.save_json("audit.jsonl")
```

## Simple Agent Wrapper

`AGEC.wrap_callable(...)` can guard a LangGraph node, an OpenAI Agents tool
function, or any regular Python callable:

```python
guarded_tool = agec.wrap_callable(
    tool_function,
    intent=intent,
    context=context,
    execution_path=execution_path,
)

result = guarded_tool()
```

The callable runs only when the decision status is `allow`.

## Examples

- `examples/crm_email_agent.py`
- `examples/coding_agent.py`

## Roadmap

- [x] Python SDK
- [x] Audit log
- [x] Simple LangGraph/OpenAI Agents-compatible callable wrapper
- [ ] MCP server

## License

Apache-2.0
