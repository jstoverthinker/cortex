"""Main AgentDB implementation with SQLite backend."""

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator, Optional

from cortex.decision import Decision
from cortex.diff import Diff
from cortex.query import QueryFilter


class AgentDB:
    """Cortex database for recording and querying agent decisions.

    Example:
        db = AgentDB("./agent-trace.cortex")

        # Record a decision
        db.record(
            agent_id="flight-bot-1",
            decision="book_flight",
            confidence=0.87,
            reasoning="User wants JFK→SFO, cheapest option is $312",
            tools_used=["search_flights", "get_price"],
        )

        # Query by time range
        decisions = db.query_time_range("flight-bot-1", "2026-05-08 10:00", "2026-05-08 12:00")

        # Diff between timepoints
        diff = db.diff("flight-bot-1", "2026-05-01", "2026-05-08")
        print(diff.summary)
    """

    def __init__(self, path: str):
        """Open or create a Cortex database.

        Args:
            path: Path to .cortex file (will be created if it doesn't exist)
        """
        self.path = Path(path)
        self._init_db()

    def _init_db(self) -> None:
        """Initialize database schema."""
        with self._conn() as conn:
            conn.executescript("""
                PRAGMA journal_mode = WAL;
                PRAGMA synchronous = NORMAL;

                CREATE TABLE IF NOT EXISTS decisions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_id TEXT NOT NULL,
                    decision TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    reasoning TEXT NOT NULL,
                    tools_used TEXT NOT NULL DEFAULT '[]',
                    metadata TEXT,
                    timestamp TEXT NOT NULL DEFAULT (datetime('now'))
                );

                CREATE INDEX IF NOT EXISTS idx_decisions_agent ON decisions(agent_id);
                CREATE INDEX IF NOT EXISTS idx_decisions_timestamp ON decisions(timestamp);
                CREATE INDEX IF NOT EXISTS idx_decisions_agent_timestamp ON decisions(agent_id, timestamp);
            """)

    @contextmanager
    def _conn(self) -> Iterator[sqlite3.Connection]:
        """Get a database connection."""
        conn = sqlite3.connect(str(self.path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def record(
        self,
        agent_id: str,
        decision: str,
        confidence: float,
        reasoning: str,
        tools_used: Optional[list[str]] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> int:
        """Record a decision.

        Args:
            agent_id: Unique agent identifier
            decision: Decision/action name
            confidence: Confidence score (0.0 - 1.0)
            reasoning: Reasoning/explanation
            tools_used: Tools/functions called
            metadata: Optional metadata

        Returns:
            The ID of the inserted record
        """
        with self._conn() as conn:
            cursor = conn.execute(
                """
                INSERT INTO decisions (agent_id, decision, confidence, reasoning, tools_used, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    agent_id,
                    decision,
                    confidence,
                    reasoning,
                    json.dumps(tools_used or []),
                    json.dumps(metadata) if metadata else None,
                ),
            )
            conn.commit()
            return cursor.lastrowid

    def query(self, filter: Optional[QueryFilter] = None) -> list[Decision]:
        """Query decisions with a filter.

        Args:
            filter: Query filter (optional)

        Returns:
            List of matching decisions
        """
        filter = filter or QueryFilter()
        where_clause, params = filter.to_sql_where()

        order = "ASC" if filter.order == "asc" else "DESC"
        limit_clause = f"LIMIT {filter.limit}" if filter.limit else ""

        sql = f"""
            SELECT id, agent_id, decision, confidence, reasoning, tools_used, metadata, timestamp
            FROM decisions
            WHERE {where_clause}
            ORDER BY timestamp {order}
            {limit_clause}
        """

        with self._conn() as conn:
            rows = conn.execute(sql, params).fetchall()
            return [self._row_to_decision(row) for row in rows]

    def query_time_range(
        self, agent_id: str, start: str, end: str, limit: int = 1000
    ) -> list[Decision]:
        """Query decisions for an agent within a time range.

        Args:
            agent_id: Agent identifier
            start: Start timestamp (ISO 8601)
            end: End timestamp (ISO 8601)
            limit: Maximum results

        Returns:
            List of decisions
        """
        return self.query(
            QueryFilter.for_agent(agent_id).time_range(start, end).limit_results(limit)
        )

    def _parse_timestamp(self, ts: str) -> datetime:
        """Parse various timestamp formats into datetime."""
        if isinstance(ts, datetime):
            return ts
        # Try ISO 8601 formats
        for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"]:
            try:
                return datetime.strptime(ts, fmt)
            except ValueError:
                continue
        # Fallback to fromisoformat
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))

    def diff(self, agent_id: str, from_time: str, to_time: str) -> Diff:
        """Diff agent reasoning between two timepoints.

        Splits the time range in half and compares the two periods.

        Args:
            agent_id: Agent identifier
            from_time: Start timestamp
            to_time: End timestamp

        Returns:
            Diff result
        """
        # Parse timestamps and calculate midpoint
        start_dt = self._parse_timestamp(from_time)
        end_dt = self._parse_timestamp(to_time)
        
        # Calculate midpoint
        midpoint_ts = start_dt + (end_dt - start_dt) / 2
        midpoint_str = midpoint_ts.strftime("%Y-%m-%d %H:%M:%S")

        # Get decisions from first half (from_time to midpoint)
        from_decisions = self.query_time_range(agent_id, from_time, midpoint_str)
        
        # Get decisions from second half (midpoint to to_time)
        to_decisions = self.query_time_range(agent_id, midpoint_str, to_time)

        # Calculate stats for first period
        from_count = len(from_decisions)
        from_avg_conf = (
            sum(d.confidence for d in from_decisions) / from_count
            if from_count > 0
            else 0.0
        )
        from_tools = set()
        from_decision_types = []
        from_reasoning_samples = []

        for d in from_decisions:
            from_tools.update(d.tools_used)
            from_decision_types.append(d.decision)
            if len(from_reasoning_samples) < 3:
                from_reasoning_samples.append(d.reasoning[:100])

        # Calculate stats for second period
        to_count = len(to_decisions)
        to_avg_conf = (
            sum(d.confidence for d in to_decisions) / to_count
            if to_count > 0
            else 0.0
        )
        to_tools = set()
        to_decision_types = []
        to_reasoning_samples = []

        for d in to_decisions:
            to_tools.update(d.tools_used)
            to_decision_types.append(d.decision)
            if len(to_reasoning_samples) < 3:
                to_reasoning_samples.append(d.reasoning[:100])

        # Calculate diff
        confidence_delta = to_avg_conf - from_avg_conf
        tools_added = list(to_tools - from_tools)
        tools_removed = list(from_tools - to_tools)

        return Diff(
            agent_id=agent_id,
            from_time=from_time,
            to_time=to_time,
            from_count=from_count,
            to_count=to_count,
            from_avg_confidence=from_avg_conf,
            to_avg_confidence=to_avg_conf,
            confidence_delta=confidence_delta,
            from_tools=list(from_tools),
            to_tools=list(to_tools),
            tools_added=tools_added,
            tools_removed=tools_removed,
            from_decision_types=from_decision_types,
            to_decision_types=to_decision_types,
            from_reasoning_samples=from_reasoning_samples,
            to_reasoning_samples=to_reasoning_samples,
        )

    def raw_query(self, sql: str) -> list[dict[str, Any]]:
        """Execute raw SQL query.

        Args:
            sql: SQL query

        Returns:
            List of rows as dictionaries
        """
        with self._conn() as conn:
            rows = conn.execute(sql).fetchall()
            return [dict(row) for row in rows]

    def _row_to_decision(self, row: sqlite3.Row) -> Decision:
        """Convert a database row to a Decision."""
        timestamp = row["timestamp"]
        if isinstance(timestamp, str):
            try:
                timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            except ValueError:
                timestamp = None

        return Decision(
            agent_id=row["agent_id"],
            decision=row["decision"],
            confidence=row["confidence"],
            reasoning=row["reasoning"],
            tools_used=json.loads(row["tools_used"]),
            metadata=json.loads(row["metadata"]) if row["metadata"] else None,
            timestamp=timestamp,
        )

    # Convenience methods

    def low_confidence(self, agent_id: Optional[str] = None) -> list[Decision]:
        """Get low confidence decisions (< 0.5)."""
        f = QueryFilter.low_confidence()
        if agent_id:
            f.agent_id = agent_id
        return self.query(f)

    def checkpoint(self, name: str) -> None:
        """Create a named checkpoint for future restore."""
        with self._conn() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS checkpoints (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    timestamp TEXT NOT NULL DEFAULT (datetime('now')),
                    metadata TEXT
                )
                """
            )
            conn.execute(
                "INSERT OR REPLACE INTO checkpoints (name) VALUES (?)", (name,)
            )
            conn.commit()

    def get_checkpoints(self) -> list[dict[str, Any]]:
        """List all checkpoints."""
        with self._conn() as conn:
            rows = conn.execute("SELECT name, timestamp FROM checkpoints").fetchall()
            return [dict(row) for row in rows]
