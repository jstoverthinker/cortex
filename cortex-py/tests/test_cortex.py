"""Tests for Cortex Python SDK."""

import json
import os
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from cortex import AgentDB, Decision, Diff, QueryFilter


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".cortex", delete=False) as f:
        db_path = f.name
    db = AgentDB(db_path)
    yield db
    # Cleanup
    if os.path.exists(db_path):
        os.remove(db_path)


class TestAgentDB:
    """Tests for AgentDB class."""

    def test_init_creates_database(self, temp_db):
        """Test that initializing creates the database file."""
        assert Path(temp_db.path).exists()

    def test_record_returns_id(self, temp_db):
        """Test that record returns an ID."""
        record_id = temp_db.record(
            agent_id="test-agent",
            decision="test_decision",
            confidence=0.9,
            reasoning="Test reasoning",
        )
        assert record_id == 1

    def test_record_with_tools_and_metadata(self, temp_db):
        """Test recording with tools and metadata."""
        record_id = temp_db.record(
            agent_id="test-agent",
            decision="book_flight",
            confidence=0.87,
            reasoning="Found cheapest flight",
            tools_used=["search_flights", "get_price"],
            metadata={"user_id": "u42", "session": "abc"},
        )
        assert record_id == 1

        decisions = temp_db.query(QueryFilter.for_agent("test-agent"))
        assert len(decisions) == 1
        assert decisions[0].tools_used == ["search_flights", "get_price"]
        assert decisions[0].metadata == {"user_id": "u42", "session": "abc"}

    def test_query_returns_decisions(self, temp_db):
        """Test that query returns decisions."""
        temp_db.record("agent-1", "decision-1", 0.9, "reasoning-1")
        temp_db.record("agent-1", "decision-2", 0.8, "reasoning-2")
        temp_db.record("agent-2", "decision-3", 0.7, "reasoning-3")

        decisions = temp_db.query(QueryFilter.for_agent("agent-1"))
        assert len(decisions) == 2
        assert all(d.agent_id == "agent-1" for d in decisions)

    def test_query_with_confidence_filter(self, temp_db):
        """Test querying with confidence filter."""
        temp_db.record("agent-1", "d1", 0.3, "low conf")
        temp_db.record("agent-1", "d2", 0.7, "high conf")
        temp_db.record("agent-1", "d3", 0.9, "very high conf")

        decisions = temp_db.query(QueryFilter(min_confidence=0.5))
        assert len(decisions) == 2

    def test_query_with_limit(self, temp_db):
        """Test querying with limit."""
        for i in range(10):
            temp_db.record("agent-1", f"d{i}", 0.5, f"reasoning {i}")

        decisions = temp_db.query(QueryFilter.for_agent("agent-1").limit_results(5))
        assert len(decisions) == 5

    def test_query_time_range(self, temp_db):
        """Test time range query."""
        # Record with specific timestamp by manipulating the SQL
        now = datetime.now()
        
        temp_db.record("agent-1", "d1", 0.8, "r1")
        temp_db.record("agent-1", "d2", 0.8, "r2")

        # Query with time range (should include the records)
        start = (now - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M")
        end = (now + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M")
        
        decisions = temp_db.query_time_range("agent-1", start, end)
        assert len(decisions) == 2

    def test_raw_query(self, temp_db):
        """Test raw SQL query."""
        temp_db.record("agent-1", "d1", 0.3, "low")
        temp_db.record("agent-1", "d2", 0.9, "high")

        results = temp_db.raw_query("SELECT * FROM decisions WHERE confidence < 0.5")
        assert len(results) == 1
        assert results[0]["decision"] == "d1"

    def test_low_confidence(self, temp_db):
        """Test low confidence convenience method."""
        temp_db.record("agent-1", "d1", 0.3, "low")
        temp_db.record("agent-1", "d2", 0.7, "high")

        decisions = temp_db.low_confidence()
        assert len(decisions) == 1
        assert decisions[0].confidence < 0.5

    def test_diff(self, temp_db):
        """Test diff between timepoints."""
        # Create records with timestamps by using raw SQL
        now = datetime.now()
        base_time = now - timedelta(hours=4)
        
        # First period records (from -4h to -2h)
        with temp_db._conn() as conn:
            conn.execute(
                "INSERT INTO decisions (agent_id, decision, confidence, reasoning, tools_used, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
                ("agent-1", "d1", 0.6, "old reasoning 1", '["tool1"]', (base_time + timedelta(minutes=30)).strftime("%Y-%m-%d %H:%M:%S")),
            )
            conn.execute(
                "INSERT INTO decisions (agent_id, decision, confidence, reasoning, tools_used, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
                ("agent-1", "d2", 0.7, "old reasoning 2", '["tool1", "tool2"]', (base_time + timedelta(minutes=60)).strftime("%Y-%m-%d %H:%M:%S")),
            )
            # Second period records (from -2h to now)
            conn.execute(
                "INSERT INTO decisions (agent_id, decision, confidence, reasoning, tools_used, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
                ("agent-1", "d3", 0.9, "new reasoning 1", '["tool2", "tool3"]', (now - timedelta(minutes=30)).strftime("%Y-%m-%d %H:%M:%S")),
            )
            conn.execute(
                "INSERT INTO decisions (agent_id, decision, confidence, reasoning, tools_used, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
                ("agent-1", "d4", 0.85, "new reasoning 2", '["tool2"]', (now - timedelta(minutes=15)).strftime("%Y-%m-%d %H:%M:%S")),
            )
            conn.commit()  # Commit the raw SQL inserts

        from_time = base_time.strftime("%Y-%m-%d %H:%M")
        to_time = now.strftime("%Y-%m-%d %H:%M")
        
        diff = temp_db.diff("agent-1", from_time, to_time)
        
        assert diff.agent_id == "agent-1"
        assert diff.from_count == 2  # First half
        assert diff.to_count == 2    # Second half
        # First period avg: (0.6 + 0.7) / 2 = 0.65
        # Second period avg: (0.9 + 0.85) / 2 = 0.875
        # Delta: 0.875 - 0.65 = 0.225
        assert diff.confidence_delta > 0  # Confidence improved
        assert "tool3" in diff.tools_added  # New tool in second period
        assert "tool1" in diff.tools_removed  # Tool removed in second period

    def test_checkpoint(self, temp_db):
        """Test checkpoint creation."""
        temp_db.checkpoint("before-upgrade")
        checkpoints = temp_db.get_checkpoints()
        assert len(checkpoints) == 1
        assert checkpoints[0]["name"] == "before-upgrade"


class TestDecision:
    """Tests for Decision dataclass."""

    def test_to_dict(self):
        """Test conversion to dict."""
        d = Decision(
            agent_id="agent-1",
            decision="test",
            confidence=0.9,
            reasoning="test reasoning",
            tools_used=["tool1"],
            metadata={"key": "value"},
        )
        result = d.to_dict()
        assert result["agent_id"] == "agent-1"
        assert result["tools_used"] == ["tool1"]
        assert result["metadata"] == {"key": "value"}

    def test_from_dict(self):
        """Test creation from dict."""
        data = {
            "agent_id": "agent-1",
            "decision": "test",
            "confidence": 0.9,
            "reasoning": "test reasoning",
            "tools_used": ["tool1"],
            "metadata": {"key": "value"},
            "timestamp": "2026-05-08T10:00:00",
        }
        d = Decision.from_dict(data)
        assert d.agent_id == "agent-1"
        assert d.tools_used == ["tool1"]
        assert d.timestamp is not None


class TestQueryFilter:
    """Tests for QueryFilter."""

    def test_for_agent(self):
        """Test agent filter creation."""
        f = QueryFilter.for_agent("agent-1")
        assert f.agent_id == "agent-1"

    def test_fluent_api(self):
        """Test fluent API chaining."""
        f = (
            QueryFilter.for_agent("agent-1")
            .time_range("10:00", "12:00")
            .confidence_range(0.5, 1.0)
            .limit_results(10)
        )
        assert f.agent_id == "agent-1"
        assert f.start_time == "10:00"
        assert f.end_time == "12:00"
        assert f.min_confidence == 0.5
        assert f.max_confidence == 1.0
        assert f.limit == 10

    def test_to_sql_where(self):
        """Test SQL WHERE clause generation."""
        f = QueryFilter.for_agent("agent-1").time_range("10:00", "12:00")
        where, params = f.to_sql_where()
        assert "agent_id = ?" in where
        assert "timestamp >= ?" in where
        assert "timestamp <= ?" in where
        assert params == ["agent-1", "10:00", "12:00"]

    def test_low_confidence(self):
        """Test low confidence filter."""
        f = QueryFilter.low_confidence()
        assert f.max_confidence == 0.5


class TestDiff:
    """Tests for Diff dataclass."""

    def test_summary(self):
        """Test diff summary generation."""
        diff = Diff(
            agent_id="agent-1",
            from_time="10:00",
            to_time="12:00",
            from_count=10,
            to_count=15,
            from_avg_confidence=0.7,
            to_avg_confidence=0.8,
            confidence_delta=0.1,
            from_tools=["tool1"],
            to_tools=["tool1", "tool2"],
            tools_added=["tool2"],
            tools_removed=[],
        )
        assert "Decisions: 10 → 15" in diff.summary
        assert "+10.0%" in diff.summary
        assert "Tools: +1 -0" in diff.summary

    def test_summary_negative_delta(self):
        """Test diff summary with negative confidence delta."""
        diff = Diff(
            agent_id="agent-1",
            from_time="10:00",
            to_time="12:00",
            from_count=10,
            to_count=8,
            from_avg_confidence=0.8,
            to_avg_confidence=0.6,
            confidence_delta=-0.2,
            from_tools=["tool1"],
            to_tools=["tool1"],
            tools_added=[],
            tools_removed=[],
        )
        assert "Decisions: 10 → 8" in diff.summary
        assert "-20.0%" in diff.summary
