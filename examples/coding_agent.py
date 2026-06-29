from agec import Context, ExecutionPath, Intent, wrap_langgraph_node


def run_tests(state: dict[str, str] | None = None) -> dict[str, str]:
    state = state or {}
    return {**state, "result": "tests passed"}


guarded_run_tests = wrap_langgraph_node(
    run_tests,
    intent=Intent(type="modify_code", source="agent_plan", confidence=0.87),
    context=Context(facts={"repo_status": "clean", "risk": "low"}),
    execution_path=ExecutionPath(
        steps=["repo.read", "code.edit", "tests.run"],
        approved_path_id="coding_agent_v1",
    ),
)

print(guarded_run_tests({"repo": "agec"}))
