"""Decision objects returned by AGEC validation."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal

DecisionStatus = Literal["allow", "review", "suspend", "halt", "reauthorize"]


@dataclass(slots=True)
class GovernanceDecision:
    """Structured pre-execution governance decision."""

    agec_id: str
    status: DecisionStatus
    intent_score: float
    context_score: float
    path_score: float
    reason: str
    audit_id: str

    def to_dict(self) -> dict[str, object]:
        """Return the decision as a JSON-serializable dictionary."""
        return asdict(self)
