# Cortex Project - AGENTS.md

## Project Context

Cortex is **"SQLite for AI Agents"** — a single-file database that records agent reasoning and enables time-travel queries, diff views, and debugging.

**Target Users:**
- AI startups (audit trail for investors)
- Enterprise AI teams (compliance)
- Agent framework authors (debug mode for users)

**Business Model:**
- Open source core (Apache 2.0)
- Team tier: $99/mo (loop detection, export, dashboard)
- Enterprise: custom (SSO, on-prem, SOC 2)

## Current State (2026-05-11)

### Completed
- ✅ Product refinement doc (`Cortex-Refinement-Jstoverthinker.md`)
- ✅ Landing page (`overthought-labs-/src/pages/cortex-landing.tsx`)
- ✅ Rust crate skeleton (`cortex/cortex-core/`)
- ✅ **Python SDK fully implemented** (`cortex/cortex-py/`)
  - ✅ `db.py` - AgentDB with SQLite backend, WAL mode
  - ✅ `decision.py` - Decision dataclass with serialization
  - ✅ `query.py` - QueryFilter with fluent API
  - ✅ `diff.py` - Diff dataclass with summary
  - ✅ `cli.py` - CLI tool (init, query, diff, checkpoint)
  - ✅ Tests - 19 passing tests
  - ✅ `pip install cortex` works locally
- ✅ Build system ready for PyPI
- ✅ **GitHub repo created and pushed**
  - ✅ https://github.com/jstoverthinker/cortex
  - ✅ Apache 2.0 license
  - ✅ README with correct URLs

### In Progress
- 🚧 PyPI publish (requires `twine upload dist/*`)
- 🚧 Landing page TypeScript errors

### Blocked / Needs Owner Action
- ⏳ Framework outreach (LangGraph, CrewAI, LlamaIndex)
- ⏳ Pilot user conversations

## Architecture

### Storage
- SQLite backend (WAL mode)
- Single `.cortex` file
- Tables: `decisions`, `checkpoints`

### Core Types
```
Decision:
  - agent_id: str
  - decision: str
  - confidence: float (0.0-1.0)
  - reasoning: str
  - tools_used: list[str]
  - metadata: dict (optional)
  - timestamp: datetime

QueryFilter:
  - agent_id, start_time, end_time
  - min_confidence, max_confidence
  - decision_type, limit, order

Diff:
  - from/to counts
  - confidence delta
  - tools added/removed
  - reasoning samples
```

### MVP Features (P0) - COMPLETE
1. ✅ Record decision
2. ✅ Time-travel query
3. ✅ Diff view

### Post-MVP (P1)
- Loop detection (background thread)
- VS Code extension
- Audit log export
- Checkpoints/restore

## File Locations

```
/home/workspace/
├── Cortex-Refinement-Jstoverthinker.md  # Strategy doc
├── cortex/                              # Product code
│   ├── README.md
│   ├── cortex-core/                     # Rust crate
│   │   ├── Cargo.toml
│   │   └── src/
│   │       ├── lib.rs
│   │       ├── db.rs
│   │       ├── decision.rs
│   │       ├── query.rs
│   │       ├── diff.rs
│   │       └── error.rs
│   └── cortex-py/                       # Python SDK ✅
│       ├── pyproject.toml
│       ├── README.md
│       └── cortex/
│           ├── __init__.py
│           ├── db.py
│           ├── decision.py
│           ├── query.py
│           ├── diff.py
│           └── cli.py
│       └── tests/
│           └── test_cortex.py
└── overthought-labs-/                   # Landing page site
    └── src/pages/cortex-landing.tsx
```

## Next Steps

1. **Publish to PyPI** — `twine upload dist/*`
2. **Fix landing page** — resolve TypeScript errors
3. **Launch prep** — HN post, terminal GIF demo
4. **Framework integrations** — LangGraph, CrewAI, LlamaIndex

## Quick Test Commands

```bash
# Install locally
cd /home/workspace/cortex/cortex-py
pip install -e .

# Run tests
python -m pytest tests/ -v

# CLI usage
cortex init ./my-agent.cortex
cortex --db ./my-agent.cortex query --agent my-agent
cortex --db ./my-agent.cortex diff my-agent --from 2026-05-01 --to 2026-05-12

# Build for PyPI
pip install build
python -m build --wheel --sdist
```

## References

- Refinement doc: `/home/workspace/Cortex-Refinement-Jstoverthinker.md`
- 30-day plan: See "5. 30-Day Execution Plan" in refinement doc
- Contractor spec: See "6.1 Contractor Spec" in refinement doc
- Pricing: See "3.4 Pricing Model" in refinement doc
