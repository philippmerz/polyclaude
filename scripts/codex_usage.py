#!/usr/bin/env python3
"""Read Codex account quota headroom through the supported app-server RPC.

This is deliberately read-only and non-conversational.  It starts a short-lived
local ``codex app-server`` process, performs the required initialize handshake,
calls ``account/rateLimits/read`` and (unless disabled) ``account/usage/read``,
then exits.  It never reads auth files and never injects a model turn merely to
ask the TUI's ``/usage`` command for the same data.
"""

from __future__ import annotations

import argparse
import json
import os
import select
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


CLIENT_VERSION = "1.0.0"
INITIALIZE_ID = 1
RATE_LIMITS_ID = 2
TOKEN_USAGE_ID = 3


class UsageProbeError(RuntimeError):
    """The local app-server did not return a trustworthy usage snapshot."""


def rpc_messages(include_token_usage: bool = True) -> list[dict[str, Any]]:
    """Return the complete newline-delimited JSON-RPC request sequence."""
    messages: list[dict[str, Any]] = [
        {
            "method": "initialize",
            "id": INITIALIZE_ID,
            "params": {
                "clientInfo": {
                    "name": "polyclaude_usage_probe",
                    "title": "PolyClaude usage probe",
                    "version": CLIENT_VERSION,
                }
            },
        },
        {"method": "initialized", "params": {}},
        {"method": "account/rateLimits/read", "id": RATE_LIMITS_ID},
    ]
    if include_token_usage:
        messages.append({"method": "account/usage/read", "id": TOKEN_USAGE_ID})
    return messages


def accept_rpc_line(line: bytes, responses: dict[int, dict[str, Any]]) -> None:
    """Collect only response objects; ignore notifications and non-JSON noise."""
    try:
        message = json.loads(line)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return
    if not isinstance(message, dict):
        return
    request_id = message.get("id")
    if isinstance(request_id, int):
        responses[request_id] = message


def _stop_process(process: subprocess.Popen[bytes]) -> str:
    """Stop the short-lived server and return bounded diagnostics."""
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=2)
    if process.stderr is None:
        return ""
    return process.stderr.read(4096).decode("utf-8", errors="replace").strip()


def fetch_usage(
    *,
    codex_bin: str = "codex",
    timeout: float = 20.0,
    include_token_usage: bool = True,
) -> dict[str, Any]:
    """Fetch a single account snapshot from a fresh local app-server."""
    executable = shutil.which(codex_bin) if "/" not in codex_bin else codex_bin
    if not executable or not Path(executable).is_file():
        raise UsageProbeError(f"Codex CLI not found: {codex_bin}")

    expected = {INITIALIZE_ID, RATE_LIMITS_ID}
    if include_token_usage:
        expected.add(TOKEN_USAGE_ID)

    try:
        process = subprocess.Popen(
            [executable, "app-server"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except OSError as exc:
        raise UsageProbeError(f"could not start Codex app-server: {exc}") from exc
    responses: dict[int, dict[str, Any]] = {}
    buffer = b""
    failure: Exception | None = None
    diagnostics = ""
    try:
        if process.stdin is None or process.stdout is None:
            raise UsageProbeError("Codex app-server pipes were not created")
        messages = rpc_messages(include_token_usage)
        deadline = time.monotonic() + timeout
        phases = [([messages[0]], {INITIALIZE_ID}), (messages[1:], expected)]
        for phase_number, (outbound, required) in enumerate(phases):
            payload = b"".join(
                json.dumps(message, separators=(",", ":")).encode("utf-8") + b"\n"
                for message in outbound
            )
            process.stdin.write(payload)
            process.stdin.flush()

            while not required.issubset(responses):
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise UsageProbeError(
                        "timed out waiting for app-server responses "
                        f"{sorted(required - responses.keys())}"
                    )
                readable, _, _ = select.select([process.stdout], [], [], remaining)
                if not readable:
                    continue
                chunk = os.read(process.stdout.fileno(), 65536)
                if not chunk:
                    raise UsageProbeError(
                        "app-server exited before responses "
                        f"{sorted(required - responses.keys())}"
                    )
                buffer += chunk
                while b"\n" in buffer:
                    line, buffer = buffer.split(b"\n", 1)
                    accept_rpc_line(line, responses)

            # The protocol requires a successful initialize response before
            # the initialized notification and account reads are sent.
            if phase_number == 0 and "error" in responses[INITIALIZE_ID]:
                raise UsageProbeError(
                    "app-server initialize failed: "
                    f"{json.dumps(responses[INITIALIZE_ID]['error'], sort_keys=True)}"
                )
    except Exception as exc:  # diagnostics are available only after shutdown
        failure = exc
    finally:
        diagnostics = _stop_process(process)

    if failure is not None:
        suffix = f"; app-server: {diagnostics[:500]}" if diagnostics else ""
        raise UsageProbeError(f"{failure}{suffix}") from failure

    for request_id in sorted(expected):
        response = responses[request_id]
        if "error" in response:
            raise UsageProbeError(
                f"app-server request {request_id} failed: {json.dumps(response['error'], sort_keys=True)}"
            )
        if not isinstance(response.get("result"), dict):
            raise UsageProbeError(f"app-server request {request_id} returned no result object")

    snapshot: dict[str, Any] = {
        "fetchedAt": datetime.now(timezone.utc).isoformat(),
        "rateLimits": responses[RATE_LIMITS_ID]["result"],
    }
    if include_token_usage:
        snapshot["tokenUsage"] = responses[TOKEN_USAGE_ID]["result"]
    return snapshot


def _duration(minutes: Any) -> str:
    try:
        value = int(minutes)
    except (TypeError, ValueError):
        return "unknown window"
    if value % 10080 == 0:
        return f"{value // 10080}w"
    if value % 1440 == 0:
        return f"{value // 1440}d"
    if value % 60 == 0:
        return f"{value // 60}h"
    return f"{value}m"


def _reset_time(epoch: Any) -> str:
    try:
        value = float(epoch)
    except (TypeError, ValueError):
        return "unknown"
    return datetime.fromtimestamp(value, tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def _number(value: Any) -> str:
    try:
        amount = int(value)
    except (TypeError, ValueError):
        return "unknown"
    for divisor, suffix in ((1_000_000_000, "B"), (1_000_000, "M"), (1_000, "k")):
        if amount >= divisor:
            return f"{amount / divisor:.2f}{suffix}"
    return str(amount)


def rate_limit_rows(rate_result: dict[str, Any]) -> list[dict[str, Any]]:
    """Normalize the multi-bucket and legacy single-bucket response shapes."""
    buckets = rate_result.get("rateLimitsByLimitId")
    if not isinstance(buckets, dict) or not buckets:
        legacy = rate_result.get("rateLimits")
        buckets = {str(legacy.get("limitId", "codex")): legacy} if isinstance(legacy, dict) else {}

    rows: list[dict[str, Any]] = []
    for bucket_id, bucket in buckets.items():
        if not isinstance(bucket, dict):
            continue
        name = bucket.get("limitName") or bucket.get("limitId") or bucket_id
        for window_name in ("primary", "secondary"):
            window = bucket.get(window_name)
            if not isinstance(window, dict):
                continue
            try:
                used = float(window["usedPercent"])
            except (KeyError, TypeError, ValueError):
                continue
            rows.append(
                {
                    "bucketId": str(bucket.get("limitId") or bucket_id),
                    "name": str(name),
                    "window": window_name,
                    "usedPercent": used,
                    "headroomPercent": max(0.0, 100.0 - used),
                    "windowDurationMins": window.get("windowDurationMins"),
                    "resetsAt": window.get("resetsAt"),
                    "planType": bucket.get("planType"),
                    "rateLimitReachedType": bucket.get("rateLimitReachedType"),
                }
            )
    return sorted(
        rows,
        key=lambda row: (
            0 if row["bucketId"] == "codex" else 1,
            row["name"],
            0 if row["window"] == "primary" else 1,
        ),
    )


def main_codex_headroom(rate_result: dict[str, Any]) -> float | None:
    """Return the most constrained main-Codex window, excluding model-specific buckets."""
    values = [
        row["headroomPercent"]
        for row in rate_limit_rows(rate_result)
        if row["bucketId"] == "codex"
    ]
    return min(values) if values else None


def format_snapshot(snapshot: dict[str, Any], *, brief: bool = False) -> str:
    rate_result = snapshot.get("rateLimits")
    if not isinstance(rate_result, dict):
        raise UsageProbeError("rate-limit snapshot is missing")
    rows = rate_limit_rows(rate_result)
    if not rows:
        raise UsageProbeError("rate-limit snapshot contains no usable windows")

    lines = ["Codex quota headroom:"]
    for row in rows:
        used = f"{row['usedPercent']:g}%"
        headroom = f"{row['headroomPercent']:g}%"
        label = row["name"]
        if row["window"] == "secondary":
            label += " secondary"
        line = (
            f"  {label}: {used} used / {headroom} headroom "
            f"({_duration(row['windowDurationMins'])}, resets {_reset_time(row['resetsAt'])})"
        )
        if row.get("rateLimitReachedType"):
            line += f" LIMIT={row['rateLimitReachedType']}"
        lines.append(line)

    reset_credits = rate_result.get("rateLimitResetCredits")
    if not brief and isinstance(reset_credits, dict):
        lines.append(f"  earned reset credits: {reset_credits.get('availableCount', 'unknown')}")

    token_result = snapshot.get("tokenUsage")
    if not brief and isinstance(token_result, dict):
        summary = token_result.get("summary")
        buckets = token_result.get("dailyUsageBuckets")
        latest = None
        if isinstance(buckets, list):
            valid = [item for item in buckets if isinstance(item, dict) and item.get("startDate")]
            if valid:
                latest = max(valid, key=lambda item: str(item["startDate"]))
        pieces = []
        if latest:
            pieces.append(f"{latest['startDate']} {_number(latest.get('tokens'))} tokens")
        if isinstance(summary, dict):
            pieces.append(f"lifetime {_number(summary.get('lifetimeTokens'))}")
        if pieces:
            lines.append("Token activity: " + "; ".join(pieces))
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--brief", action="store_true", help="omit token totals and reset details")
    parser.add_argument("--json", action="store_true", help="emit the raw normalized snapshot")
    parser.add_argument(
        "--no-token-usage",
        action="store_true",
        help="skip account/usage/read and fetch rate-limit headroom only",
    )
    parser.add_argument("--timeout", type=float, default=20.0)
    parser.add_argument("--codex-bin", default=os.environ.get("POLYCLAUDE_CODEX_BIN", "codex"))
    parser.add_argument(
        "--warn-below",
        type=float,
        default=20.0,
        metavar="PCT",
        help="print a warning when the main Codex bucket has less headroom (default: 20)",
    )
    parser.add_argument(
        "--fail-below",
        type=float,
        default=None,
        metavar="PCT",
        help="exit 4 when main Codex headroom is below PCT (opt-in automation gate)",
    )
    args = parser.parse_args()
    if args.timeout <= 0 or args.warn_below < 0 or args.warn_below > 100:
        parser.error("timeout must be positive and percentages must be within 0..100")
    if args.fail_below is not None and not 0 <= args.fail_below <= 100:
        parser.error("--fail-below must be within 0..100")

    try:
        snapshot = fetch_usage(
            codex_bin=args.codex_bin,
            timeout=args.timeout,
            include_token_usage=not args.no_token_usage,
        )
        print(
            json.dumps(snapshot, indent=2, sort_keys=True)
            if args.json
            else format_snapshot(snapshot, brief=args.brief)
        )
        headroom = main_codex_headroom(snapshot["rateLimits"])
        if headroom is not None and headroom < args.warn_below:
            print(
                f"QUOTA WARNING: main Codex headroom is {headroom:g}% (< {args.warn_below:g}%). "
                "Reserve the main context for risk/asset judgment and route bounded routine work "
                "to cheaper subagents.",
                file=sys.stderr,
            )
        if args.fail_below is not None and headroom is not None and headroom < args.fail_below:
            return 4
        return 0
    except UsageProbeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
