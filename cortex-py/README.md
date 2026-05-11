# Cortex Python SDK

**SQLite for AI Agents** — A single-file database for recording agent reasoning.

## Installation

```bash
pip install cortex
```

## Quick Start

```python
from cortex import AgentDB

# Create or open a database
db = AgentDB("./agent-trace.cortex")

# Record a decision
db.record(
    agent_id="flight-bot-1",
    decision="book_flight",
    confidence=0.87,
    reasoning="User wants JFK→SFO, cheapest option is $312 on Delta",
    tools_used=["search_flights", "get_price"],
    metadata={"user_id": "u42", "session": "abc123"}
)

# Time-travel query
decisions = db.query_time_range(
    "flight-bot-1", 
    "2026-05-08 10:00", 
    "2026-05-08 12:00"
)

# Diff reasoning between two timepoints
diff = db.diff("flight-bot-1", "2026-05-01", "2026-05-08")
print(diff.summary)
# "Decisions: 142 → 89. Confidence: +12.3%. Tools: +2 -1"
```

## CLI Usage

```bash
# Initialize a database
cortex init ./my-agent.cortex

# Query decisions
cortex query --agent flight-bot-1 --start "2026-05-08 10:00" --end "2026-05-08 12:00"

# Raw SQL
cortex query --sql "SELECT * FROM decisions WHERE confidence < 0.5"

# Diff between timepoints
cortex diff flight-bot-1 --from 2026-05-01 --to 2026-05-08
```

## Features

- **Record decisions** — Log every agent decision with reasoning, confidence, tools
- **Time-travel queries** — SQL-based queries to any point in time
- **Diff view** — Compare reasoning between two timepoints
- **Zero dependencies** — Pure Python, SQLite stdlib backend
- **Single-file storage** — Portable `.cortex` files

## API Reference

### `AgentDB(path: str)`

Open or create a Cortex database.

### `db.record(...)`

Record a decision:

| Parameter | Type | Description |
|-----------|------|-------------|
| `agent_id` | str | Unique agent identifier |
| `decision` | str | Decision/action name |
| `confidence` | float | Confidence score (0.0-1.0) |
| `reasoning` | str | Reasoning/explanation |
| `tools_used` | list[str] | Tools/functions called |
| `metadata` | dict | Optional metadata |

### `db.query(filter: QueryFilter)`

Query decisions with a filter.

### `db.query_time_range(agent_id, start, end)`

Query decisions for an agent within a time range.

### `db.diff(agent_id, from_time, to_time)`

Diff agent reasoning between two timepoints.

### `db.raw_query(sql)`

Execute raw SQL query.

## License

Apache-2.0
