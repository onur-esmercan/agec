"""AGEC policy definitions and built-in legal basis vocabulary."""

from __future__ import annotations

from dataclasses import dataclass


DEFAULT_LEGAL_BASES: list[str] = [
    "consent",
    "contract",
    "legal_obligation",
    "vital_interest",
    "public_task",
    "legitimate_interest",
]
"""GDPR Article 6 legal bases supported by AGEC out of the box."""


@dataclass
class Policy:
    """Declares what an agent is allowed to do.

    A :class:`Policy` is the authoritative source of truth for a single
    governance context. It specifies which intents, tools, purposes, and
    legal bases are permitted, and optionally blocks certain data
    categories.

    Args:
        allowed_intents: Intent types the agent may declare.
        allowed_tools: Tool identifiers the agent may invoke.
        allowed_purposes: Data processing purposes that are permitted.
        allowed_legal_bases: GDPR legal bases accepted for this policy.
        blocked_data_categories: Data categories explicitly disallowed.
            ``None`` means no categories are blocked.
        minimum_intent_confidence: Minimum confidence score required for
            an intent to be accepted (default ``0.7``).

    Example::

        policy = Policy(
            allowed_intents=["send_email"],
            allowed_tools=["gmail.send"],
            allowed_purposes=["customer_support"],
            allowed_legal_bases=["consent"],
        )
    """

    allowed_intents: list[str]
    allowed_tools: list[str]
    allowed_purposes: list[str]
    allowed_legal_bases: list[str]
    blocked_data_categories: list[str] | None = None
    minimum_intent_confidence: float = 0.7

    def is_intent_allowed(self, intent: str) -> bool:
        """Return ``True`` if *intent* is in :attr:`allowed_intents`."""
        return intent in self.allowed_intents

    def is_tool_allowed(self, tool: str) -> bool:
        """Return ``True`` if *tool* is in :attr:`allowed_tools`."""
        return tool in self.allowed_tools

    def is_purpose_allowed(self, purpose: str) -> bool:
        """Return ``True`` if *purpose* is in :attr:`allowed_purposes`."""
        return purpose in self.allowed_purposes

    def is_legal_basis_allowed(self, legal_basis: str) -> bool:
        """Return ``True`` if *legal_basis* is in :attr:`allowed_legal_bases`."""
        return legal_basis in self.allowed_legal_bases

    def has_blocked_data_category(self, categories: list[str]) -> bool:
        """Return ``True`` if any category in *categories* is blocked.

        Args:
            categories: Data categories to check against the block list.
        """
        if not self.blocked_data_categories:
            return False
        return any(category in self.blocked_data_categories for category in categories)
