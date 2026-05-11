"""Diff between two timepoints of agent reasoning."""

from dataclasses import dataclass


@dataclass
class Diff:
    """Diff result between two timepoints.

    Attributes:
        agent_id: Agent identifier
        from_time: Start timestamp
        to_time: End timestamp
        from_count: Number of decisions in first period
        to_count: Number of decisions in second period
        from_avg_confidence: Average confidence in first period
        to_avg_confidence: Average confidence in second period
        confidence_delta: Confidence change (to - from)
        from_tools: Tools used in first period
        to_tools: Tools used in second period
        tools_added: Tools added in second period
        tools_removed: Tools removed in second period
    """

    agent_id: str
    from_time: str
    to_time: str
    from_count: int
    to_count: int
    from_avg_confidence: float
    to_avg_confidence: float
    confidence_delta: float
    from_tools: list[str]
    to_tools: list[str]
    tools_added: list[str]
    tools_removed: list[str]
    from_decision_types: list[str] = None
    to_decision_types: list[str] = None
    from_reasoning_samples: list[str] = None
    to_reasoning_samples: list[str] = None

    def __post_init__(self):
        if self.from_decision_types is None:
            self.from_decision_types = []
        if self.to_decision_types is None:
            self.to_decision_types = []
        if self.from_reasoning_samples is None:
            self.from_reasoning_samples = []
        if self.to_reasoning_samples is None:
            self.to_reasoning_samples = []

    @property
    def summary(self) -> str:
        """Human-readable summary."""
        conf_dir = "+" if self.confidence_delta > 0 else ""
        tool_change = ""
        if self.tools_added or self.tools_removed:
            tool_change = f" Tools: +{len(self.tools_added)} -{len(self.tools_removed)}"

        return (
            f"Decisions: {self.from_count} → {self.to_count}. "
            f"Confidence: {conf_dir}{self.confidence_delta * 100:.1f}%.{tool_change}"
        )
