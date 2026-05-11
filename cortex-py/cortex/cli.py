"""Cortex CLI tool."""

import argparse
import json
import sys
from pathlib import Path

from cortex import AgentDB, QueryFilter


def main():
    parser = argparse.ArgumentParser(
        description="Cortex - SQLite for AI Agents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--db",
        default="./agent-trace.cortex",
        help="Path to Cortex database file",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # Init command
    init_parser = subparsers.add_parser("init", help="Create a new Cortex database")
    init_parser.add_argument("path", nargs="?", default=None, help="Path for new database")

    # Query command
    query_parser = subparsers.add_parser("query", help="Query decisions")
    query_parser.add_argument("--agent", "-a", help="Filter by agent ID")
    query_parser.add_argument("--start", "-s", help="Start timestamp")
    query_parser.add_argument("--end", "-e", help="End timestamp")
    query_parser.add_argument("--min-conf", type=float, help="Minimum confidence")
    query_parser.add_argument("--max-conf", type=float, help="Maximum confidence")
    query_parser.add_argument("--limit", "-l", type=int, default=50)
    query_parser.add_argument("--sql", help="Raw SQL query")

    # Diff command
    diff_parser = subparsers.add_parser("diff", help="Compare reasoning between timepoints")
    diff_parser.add_argument("agent", help="Agent ID")
    diff_parser.add_argument("--from", dest="from_time", required=True, help="Start timestamp")
    diff_parser.add_argument("--to", dest="to_time", required=True, help="End timestamp")

    # Checkpoint command
    cp_parser = subparsers.add_parser("checkpoint", help="Manage checkpoints")
    cp_parser.add_argument("action", choices=["create", "list"], help="Action")
    cp_parser.add_argument("--name", "-n", help="Checkpoint name (for create)")

    args = parser.parse_args()

    if args.command == "init":
        # Use provided path or fall back to --db default
        db_path = args.path if args.path else args.db
        db = AgentDB(db_path)
        print(f"✓ Created Cortex database at {db_path}")
        return

    db = AgentDB(args.db)

    if args.command == "query":
        if args.sql:
            results = db.raw_query(args.sql)
        else:
            f = QueryFilter()
            if args.agent:
                f.agent_id = args.agent
            if args.start and args.end:
                f.time_range(args.start, args.end)
            if args.min_conf:
                f.min_confidence = args.min_conf
            if args.max_conf:
                f.max_confidence = args.max_conf
            f.limit = args.limit

            decisions = db.query(f)
            results = [d.to_dict() for d in decisions]

        print(json.dumps(results, indent=2, default=str))

    elif args.command == "diff":
        diff = db.diff(args.agent, args.from_time, args.to_time)
        print(f"\n{diff.summary}\n")
        print(json.dumps(diff.__dict__, indent=2, default=str))

    elif args.command == "checkpoint":
        if args.action == "create":
            if not args.name:
                print("Error: --name required for create", file=sys.stderr)
                sys.exit(1)
            db.checkpoint(args.name)
            print(f"✓ Created checkpoint: {args.name}")
        elif args.action == "list":
            checkpoints = db.get_checkpoints()
            print(json.dumps(checkpoints, indent=2))


if __name__ == "__main__":
    main()
