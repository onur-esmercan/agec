from agec import AGEC, Context, ExecutionPath, Intent


def run_tests() -> str:
    return "tests passed"


agec = AGEC()
guarded_run_tests = agec.wrap_callable(
    run_tests,
    intent=Intent(type="modify_code", source="agent_plan", confidence=0.87),
    context=Context(facts={"repo_status": "clean", "risk": "low"}),
    execution_path=ExecutionPath(
        steps=["repo.read", "code.edit", "tests.run"],
        approved_path_id="coding_agent_v1",
    ),
)

print(guarded_run_tests())
