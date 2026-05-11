# Cortex

**SQLite for AI Agents**

A single-file database that records agent reasoning and enables time-travel queries, diff views, and debugging.

## The Problem

When your agent fails, hallucinates, or loops, you can't explain why.

- **Investors ask:** "Why did your agent make that decision?" → You don't know.
- **Compliance requires:** "Show us every decision and why." → You can't.
- **You're debugging:** "What was my agent thinking at 10:32am?" → You guess.

Cortex makes agent reasoning **inspectable, replayable, auditable**.

## Quick Start

```bash
pip install cortex
```

```python
from cortex import AgentDB

db = AgentDB("./agent-trace.cortex")

# Record every decision
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

# Diff reasoning before/after prompt change
diff = db.diff("flight-bot-1", "2026-05-01", "2026-05-08")
print(diff.summary)
# "Decisions: 142 → 89. Confidence: +12.3%. Tools: +2 -1"
```

## Features

| Feature | Description | Status |
|---------|-------------|--------|
| **Record decisions** | Log every agent decision with reasoning, confidence, tools | ✅ MVP |
| **Time-travel queries** | SQL-based queries to any point in time | ✅ MVP |
| **Diff view** | Compare reasoning between two timepoints | ✅ MVP |
| **Loop detection** | Background thread alerts when agent is stuck | 🚧 P1 |
| **VS Code extension** | Visualize decisions in IDE | 🚧 P1 |
| **Embeddings/search** | Semantic search over decisions | 📋 P2 |

## Architecture

```
cortex/
├── cortex-core/          # Rust crate (SQLite backend, core logic)
│   ├── src/
│   │   ├── lib.rs       # Main entry point
│   │   ├── db.rs        # AgentDB implementation
│   │   ├── decision.rs  # Decision types
│   │   ├── query.rs     # Query filters
│   │   └── diff.rs      # Diff calculation
│   └── Cargo.toml
│
├── cortex-py/           # Python SDK
│   ├── cortex/
│   │   ├── __init__.py
│   │   ├── db.py        # AgentDB class
│   │   ├── decision.py  # Decision dataclass
│   │   ├── query.py     # QueryFilter
│   │   ├── diff.py      # Diff result
│   │   └── cli.py       # CLI tool
│   └── pyproject.toml
│
└── README.md
```

## CLI Usage

```bash
# Initialize
cortex init ./my-agent.cortex

# Query decisions
cortex query --agent flight-bot-1 --start "2026-05-08 10:00" --end "2026-05-08 12:00"

# Raw SQL
cortex query --sql "SELECT * FROM decisions WHERE confidence < 0.5"

# Diff between timepoints
cortex diff flight-bot-1 --from 2026-05-01 --to 2026-05-08
```

## SQL Schema

```sql
CREATE TABLE decisions (
    id INTEGER PRIMARY KEY,
    agent_id TEXT NOT NULL,
    decision TEXT NOT NULL,
    confidence REAL NOT NULL,
    reasoning TEXT NOT NULL,
    tools_used TEXT,          -- JSON array
    metadata TEXT,            -- JSON object
    timestamp TEXT NOT NULL
);

CREATE INDEX idx_decisions_agent ON decisions(agent_id);
CREATE INDEX idx_decisions_timestamp ON decisions(timestamp);
```

## Example Queries

```sql
-- Low confidence decisions
SELECT * FROM decisions WHERE confidence < 0.5;

-- Decisions by agent in time range
SELECT * FROM decisions 
WHERE agent_id = 'flight-bot-1'
AND timestamp BETWEEN '2026-05-08 10:00' AND '2026-05-08 12:00';

-- Most used tools
SELECT tools_used, COUNT(*) 
FROM decisions 
GROUP BY tools_used 
ORDER BY COUNT(*) DESC;

-- Decisions that called a specific tool
SELECT * FROM decisions WHERE tools_used LIKE '%search_flights%';
```

## Who Needs This

| Segment | Pain | Solution |
|---------|------|----------|
| **AI Startups** | Investors ask why agents failed | Audit trail for due diligence |
| **Enterprise Teams** | Compliance requires explanations | Export audit logs, SOC 2 ready |
| **Framework Authors** | Users can't debug agents | Embed as built-in debug mode |

## Pricing

| Tier | Price | Features |
|------|-------|----------|
| **Open Source** | $0 | Core features, SQLite backend, community support |
| **Team** | $99/mo | Loop detection, audit export, priority support, dashboard |
| **Enterprise** | Custom | SSO, on-prem, SOC 2/HIPAA, dedicated support |

## Roadmap

### Week 1-2: MVP ✅
- [x] Rust crate skeleton (`cortex-core`)
- [x] Python SDK skeleton (`cortex-py`)
- [x] CLI tool (`cortex init`, `query`, `diff`)
- [ ] Tests and documentation
- [ ] PyPI publish

### Week 3-4: Launch Prep
- [ ] VS Code extension mockup
- [ ] HN launch post + terminal GIF
- [ ] Framework integrations (LangGraph, CrewAI)

### Month 2: Post-MVP
- [ ] Loop detection (background thread)
- [ ] Dashboard UI
- [ ] Enterprise pilots

## Building from Source

### Rust Crate

```bash
cd cortex/cortex-core
cargo build --release
```

### Python SDK

```bash
cd cortex/cortex-py
pip install -e .
```

## Contributing

MIT/Apache 2.0 dual license. PRs welcome.

## Links

- **GitHub:** https://github.com/overthought-labs/cortex
- **Docs:** https://cortex.overthoughtlabs.com
- **Discord:** https://discord.gg/cortex

---

*Built by Overthought Labs. "SQLite for AI Agents."*
