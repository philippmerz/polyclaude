#!/usr/bin/env python3
"""Read model usage headroom from local OpenCode telemetry.

The kimi-for-coding backend exposes no provider quota API, so this probe is
deliberately read-only and non-conversational: it aggregates token usage from
the local OpenCode session database instead of asking the model for a ``/usage``
style turn. It never reads auth files and never injects a model turn.
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_DB = Path.home() / ".local" / "share" / "opencode" / "opencode.db"
DAY_MS = 24 * 60 * 60 * 1000
TOKEN_KEYS = (("input", "input"), ("output", "output"), ("reasoning", "reasoning"))
CACHE_KEYS = (("read", "cache_read"), ("write", "cache_write"))


class UsageProbeError(RuntimeError):
    """The local usage snapshot could not be produced."""


def _number(value: Any) -> str:
    try:
        amount = int(value)
    except (TypeError, ValueError):
        return "unknown"
    for divisor, suffix in ((1_000_000_000, "B"), (1_000_000, "M"), (1_000, "k")):
        if amount >= divisor:
            return f"{amount / divisor:.2f}{suffix}"
    return str(amount)


def _int(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _message_rows(db_path: Path) -> list[tuple[int, str]]:
    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True, timeout=5)
        try:
            return conn.execute("SELECT time_created, data FROM message").fetchall()
        finally:
            conn.close()
    except sqlite3.Error as exc:
        raise UsageProbeError(f"could not read opencode database: {exc}") from exc


def summarize(
    rows: list[tuple[int, str]], *, now_ms: int | None = None
) -> dict[str, Any]:
    """Aggregate (time_created_ms, message_json) rows into per-model totals."""
    now = now_ms if now_ms is not None else int(time.time() * 1000)
    models: dict[str, dict[str, Any]] = {}
    for created_ms, raw in rows:
        try:
            msg = json.loads(raw)
        except (TypeError, ValueError):
            continue
        if not isinstance(msg, dict):
            continue
        tokens = msg.get("tokens")
        if not isinstance(tokens, dict):
            continue
        model = str(msg.get("modelID") or "unknown")
        cache = tokens.get("cache") if isinstance(tokens.get("cache"), dict) else {}
        bucket = models.setdefault(
            model,
            {
                "tokens": {target: 0 for _src, target in TOKEN_KEYS + CACHE_KEYS},
                "total": {target: 0 for _src, target in TOKEN_KEYS + CACHE_KEYS},
            },
        )
        amounts = {
            target: _int(tokens.get(source)) for source, target in TOKEN_KEYS
        }
        amounts.update(
            {target: _int(cache.get(source)) for source, target in CACHE_KEYS}
        )
        for target, amount in amounts.items():
            bucket["total"][target] += amount
            if now - int(created_ms or 0) <= DAY_MS:
                bucket["tokens"][target] += amount
    return {"fetchedAt": datetime.now(timezone.utc).isoformat(), "models": models}


def format_snapshot(snapshot: dict[str, Any], *, brief: bool = False) -> str:
    models = snapshot.get("models")
    if not isinstance(models, dict) or not models:
        raise UsageProbeError("no model usage rows found")
    lines = [
        "Model usage headroom (local OpenCode telemetry; the kimi backend "
        "exposes no provider quota API):"
    ]
    for model in sorted(models):
        lines.append(f"  {model}: no provider quota exposed")
        if brief:
            continue
        totals = models[model]["tokens"]
        lines.append(
            "  24h tokens: "
            f"{_number(totals['input'])} in / {_number(totals['output'])} out / "
            f"{_number(totals['reasoning'])} reasoning "
            f"(cache {_number(totals['cache_read'])} read / "
            f"{_number(totals['cache_write'])} write)"
        )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--brief", action="store_true", help="omit token totals")
    parser.add_argument(
        "--json", action="store_true", help="emit the raw normalized snapshot"
    )
    parser.add_argument(
        "--no-token-usage",
        action="store_true",
        help="accepted for CLI compatibility; token totals are local-only",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=20.0,
        help="accepted for CLI compatibility; the probe is a local read",
    )
    parser.add_argument(
        "--db",
        default=os.environ.get("POLYCLAUDE_OPENCODE_DB", str(DEFAULT_DB)),
        help="opencode session database path",
    )
    args = parser.parse_args()

    db_path = Path(args.db)
    if not db_path.is_file():
        print(f"ERROR: opencode database not found: {db_path}", file=sys.stderr)
        return 2

    try:
        snapshot = summarize(_message_rows(db_path))
        print(
            json.dumps(snapshot, indent=2, sort_keys=True)
            if args.json
            else format_snapshot(snapshot, brief=args.brief)
        )
        return 0
    except UsageProbeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
