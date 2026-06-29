"""Guard a local automation before it can run.

This demo intentionally does not make a network call. It shows where AGEC sits
when a local script is about to perform a side-effect such as sending an email,
calling an API, writing a file, or deleting data.
"""

from pathlib import Path

from agec import AGEC, AGECExecutionBlocked, AuditLog, Context, ExecutionPath, Intent, wrap_openai_tool


def _load_env_local(path: Path = Path(".env.local")) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line or line.lstrip().startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def _send_campaign_with_local_api() -> str:
    # Replace this body with a real local automation:
    # - OpenAI API call
    # - CRM update
    # - email send
    # - file write
    return "LOCAL AUTOMATION RAN"


def main() -> None:
    env = _load_env_local()
    audit_log = AuditLog()
    agec = AGEC(audit_log=audit_log)

    guarded_automation = wrap_openai_tool(
        _send_campaign_with_local_api,
        intent=Intent(
            type="send_price_list",
            source="local_operator",
            confidence=0.91,
        ),
        context=Context(
            facts={
                "openai_key_configured": bool(env.get("OPENAI_API_KEY")),
                "price_list_status": "stale",
                "campaign_status": "active",
                "customer_segment": "premium",
            }
        ),
        execution_path=ExecutionPath(
            steps=[
                "local.load_env",
                "openai.prepare_message",
                "email.send_campaign",
            ],
            approved_path_id="local_campaign_v1",
        ),
        agec=agec,
    )

    print("AGEC local automation guard demo")
    try:
        result = guarded_automation()
    except AGECExecutionBlocked as exc:
        print(f"Decision: {exc.decision.status}")
        print(f"Reason: {exc.decision.reason}")
        print(f"Audit ID: {exc.decision.audit_id}")
        print("Local automation: blocked before API/tool execution")
    else:
        print(f"Local automation: {result}")

    audit_log.save_json("local_automation_audit.jsonl", append=True)
    print("Audit file: local_automation_audit.jsonl")


if __name__ == "__main__":
    main()
