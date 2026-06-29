"""Execution path approval helpers."""

from __future__ import annotations

from .models import ExecutionPath

DEFAULT_APPROVED_PATHS: dict[str, list[str]] = {
    "price_campaign_v1": [
        "crm.read_customers",
        "pricing.get_latest_list",
        "crm.filter_segment",
        "email.send_campaign",
    ],
    "coding_agent_v1": [
        "repo.read",
        "code.edit",
        "tests.run",
    ],
}


class ApprovedPathRegistry:
    """Stores approved execution paths and detects unknown or modified paths."""

    def __init__(self, approved_paths: dict[str, list[str]] | None = None) -> None:
        self._paths = dict(DEFAULT_APPROVED_PATHS)
        if approved_paths:
            self._paths.update(approved_paths)

    def evaluate(self, execution_path: ExecutionPath) -> tuple[str, float, str]:
        """Return ``(status, score, reason)`` for an execution path."""
        if not execution_path.steps:
            return "halt", 0.0, "Execution path is empty."

        if not execution_path.approved_path_id:
            return "reauthorize", 0.0, "Execution path has no approved_path_id."

        approved_steps = self._paths.get(execution_path.approved_path_id)
        if approved_steps is None:
            return "reauthorize", 0.0, "Execution path is unknown."

        if approved_steps != execution_path.steps:
            return "halt", 0.0, "Execution path was modified from the approved path."

        return "allow", 1.0, "Execution path validated."
