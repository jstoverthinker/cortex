"""Query filters for time-travel queries."""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class QueryOrder(str, Enum):
    ASC = "asc"
    DESC = "desc"


@dataclass
class QueryFilter:
    """Filter for querying decisions.

    Example:
        filter = QueryFilter.for_agent("my-agent").time_range("10:00", "12:00")
        decisions = db.query(filter)
    """

    agent_id: Optional[str] = None
    min_confidence: Optional[float] = None
    max_confidence: Optional[float] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    decision_type: Optional[str] = None
    limit: Optional[int] = None
    order: Optional[QueryOrder] = None

    @classmethod
    def for_agent(cls, agent_id: str) -> "QueryFilter":
        """Create a filter for a specific agent."""
        return cls(agent_id=agent_id)

    def time_range(self, start: str, end: str) -> "QueryFilter":
        """Set time range."""
        self.start_time = start
        self.end_time = end
        return self

    def confidence_range(self, min_val: float, max_val: float) -> "QueryFilter":
        """Set confidence range."""
        self.min_confidence = min_val
        self.max_confidence = max_val
        return self

    @classmethod
    def low_confidence(cls) -> "QueryFilter":
        """Filter for low confidence decisions (< 0.5)."""
        return cls(max_confidence=0.5)

    def limit_results(self, n: int) -> "QueryFilter":
        """Limit results."""
        self.limit = n
        return self

    def to_sql_where(self) -> tuple[str, list]:
        """Convert to SQL WHERE clause and params."""
        conditions = ["1=1"]
        params = []

        if self.agent_id:
            conditions.append("agent_id = ?")
            params.append(self.agent_id)

        if self.start_time:
            conditions.append("timestamp >= ?")
            params.append(self.start_time)

        if self.end_time:
            conditions.append("timestamp <= ?")
            params.append(self.end_time)

        if self.min_confidence is not None:
            conditions.append("confidence >= ?")
            params.append(self.min_confidence)

        if self.max_confidence is not None:
            conditions.append("confidence <= ?")
            params.append(self.max_confidence)

        if self.decision_type:
            conditions.append("decision = ?")
            params.append(self.decision_type)

        return " AND ".join(conditions), params
