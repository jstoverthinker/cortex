"""
Cortex - SQLite for AI Agents

A single-file database that records agent reasoning and enables
time-travel queries, diff views, and debugging.

Example:
    from cortex import AgentDB

    db = AgentDB("./agent-trace.cortex")
    db.record(
        agent_id="flight-bot-1",
        decision="book_flight",
        confidence=0.87,
        reasoning="User wants JFK→SFO, cheapest option is $312",
        tools_used=["search_flights", "get_price"],
    )

    # Time-travel query
    decisions = db.query_time_range("flight-bot-1", "2026-05-08 10:00", "2026-05-08 12:00")

    # Diff reasoning between two timepoints
    diff = db.diff("flight-bot-1", "2026-05-01", "2026-05-08")
    print(diff.summary)
"""

__version__ = "0.1.0"

from cortex.db import AgentDB
from cortex.decision import Decision
from cortex.diff import Diff
from cortex.query import QueryFilter

__all__ = ["AgentDB", "Decision", "Diff", "QueryFilter"]
