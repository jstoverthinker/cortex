"""Decision types for recording agent actions."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional


@dataclass
class Decision:
    """A recorded agent decision.

    Attributes:
        agent_id: Unique agent identifier
        decision: Decision/action name (e.g., "book_flight")
        confidence: Confidence score (0.0 - 1.0)
        reasoning: Reasoning/explanation for the decision
        tools_used: Tools/functions called during this decision
        metadata: Optional metadata (user_id, session, etc.)
        timestamp: When this decision was recorded (auto-filled)
    """

    agent_id: str
    decision: str
    confidence: float
    reasoning: str
    tools_used: list[str] = field(default_factory=list)
    metadata: Optional[dict[str, Any]] = None
    timestamp: Optional[datetime] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "agent_id": self.agent_id,
            "decision": self.decision,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "tools_used": self.tools_used,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Decision":
        """Create from dictionary."""
        timestamp = data.get("timestamp")
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        return cls(
            agent_id=data["agent_id"],
            decision=data["decision"],
            confidence=data["confidence"],
            reasoning=data["reasoning"],
            tools_used=data.get("tools_used", []),
            metadata=data.get("metadata"),
            timestamp=timestamp,
        )
