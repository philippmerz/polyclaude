"""Box wake runtime: policy, dedupe, rate limits, outbox and replay."""
import json
import os
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "wake_webhook.py"
sys.path.insert(0, str(SCRIPT.parent))
import wake_webhook as ww  # noqa: E402


def _run(repo, text, env_extra=None, args=()):
    env = {k: v for k, v in os.environ.items() if not k.startswith("POLYCLAUDE_")}
    env.update(env_extra or {})
    return subprocess.run([sys.executable, str(SCRIPT), "queue", "--workdir", str(repo), *args],
                          input=text, text=True, capture_output=True, env=env, timeout=30)


def _rows(repo):
    p = repo / "logs" / "wake_outbox.jsonl"
    return ww.state_of([json.loads(l) for l in p.read_text().splitlines() if l.strip()])


NEWS = ("Cron tick 20261102T190000Z. Run your scheduled polyclaude check-in. "
        "[NEWS REVIEW REQUEST: CRITICAL Fed cuts rates slug=fed-cut-december-2026]")


def test_unconfigured_logs_pending_and_payload_shape(tmp_path):
    r = _run(tmp_path, NEWS, {"POLYCLAUDE_WAKE_NOW": "2026-11-02T19:00:00+00:00"})
    assert r.returncode == 0
    (row,) = _rows(tmp_path).values()
    assert row["status"] == "pending"
    assert row["source"] == "news_watcher" and row["severity"] == "critical"
    assert row["market_slug"] == "fed-cut-december-2026"
    assert row["headline"].startswith("NEWS REVIEW REQUEST:")
    assert set(ww._payload(row)) == {"id", "source", "severity", "market_slug", "headline", "ts", "kind"}


def test_policy_scheduled_and_followup_never_wake(tmp_path):
    _run(tmp_path, "Cron tick 20261102T180000Z. Run your scheduled polyclaude check-in.")
    _run(tmp_path, "check the fill again", {"POLYCLAUDE_PROMPT_SOURCE": "self_followup"})
    assert {r["status"] for r in _rows(tmp_path).values()} == {"suppressed_policy"}


def test_market_cooldown_and_daily_cap(tmp_path):
    t0 = {"POLYCLAUDE_WAKE_NOW": "2026-11-02T10:00:00+00:00"}
    _run(tmp_path, NEWS, t0)
    _run(tmp_path, NEWS.replace("Fed cuts", "Fed hikes"), {"POLYCLAUDE_WAKE_NOW": "2026-11-02T10:10:00+00:00"})
    _run(tmp_path, NEWS.replace("Fed cuts", "Fed holds"), {"POLYCLAUDE_WAKE_NOW": "2026-11-02T10:31:00+00:00"})
    st = [r["status"] for r in sorted(_rows(tmp_path).values(), key=lambda r: r["ts"])]
    assert st == ["pending", "rate_limited_market", "pending"]
    for i in range(15):
        _run(tmp_path, f"[NEWS REVIEW REQUEST: item {i} slug=m-{i}]",
             {"POLYCLAUDE_WAKE_NOW": f"2026-11-02T12:{i:02d}:00+00:00"})
    counts = {}
    for r in _rows(tmp_path).values():
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    assert counts["pending"] == 12 and counts["rate_limited_daily"] == 5


def test_telegram_exempt_from_cap_but_deduped_by_update_id(tmp_path):
    env = {"POLYCLAUDE_WAKE_DAILY_CAP": "0"}
    msg = "telegram: [update_id=5 message_id=1 sent_at=x age_seconds=1]\nDelivery safety: ok\n\nsell it"
    _run(tmp_path, msg, env, ("--reference-id", "5"))
    _run(tmp_path, msg, env, ("--reference-id", "5"))
    st = sorted(r["status"] for r in _rows(tmp_path).values())
    assert st == ["duplicate", "pending"]
    (row,) = [r for r in _rows(tmp_path).values() if r["status"] == "pending"]
    assert row["source"] == "telegram" and row["headline"] == "sell it"


class _Hook(BaseHTTPRequestHandler):
    seen: list = []

    def do_POST(self):  # noqa: N802
        body = self.rfile.read(int(self.headers["Content-Length"]))
        _Hook.seen.append((dict(self.headers), json.loads(body)))
        self.send_response(204)
        self.end_headers()

    def log_message(self, *a):
        pass


@pytest.fixture
def hook():
    _Hook.seen = []
    srv = HTTPServer(("127.0.0.1", 0), _Hook)
    th = threading.Thread(target=srv.serve_forever, daemon=True)
    th.start()
    yield f"http://127.0.0.1:{srv.server_port}/wake"
    srv.shutdown()


def test_replay_after_configuring_with_bearer_header(tmp_path, hook):
    _run(tmp_path, "[resting_watch] FILL suspected: fed-cut-december-2026:YES — verify the fill")
    assert _Hook.seen == []
    (tmp_path / ".env.wake").write_text(f"POLYCLAUDE_WAKE_URL={hook}\nPOLYCLAUDE_WAKE_KEY=k123\n")
    env = {k: v for k, v in os.environ.items() if not k.startswith("POLYCLAUDE_")}
    r = subprocess.run([sys.executable, str(SCRIPT), "replay", "--workdir", str(tmp_path)],
                       text=True, capture_output=True, env=env, timeout=30)
    assert json.loads(r.stdout)["sent"] == 1
    headers, payload = _Hook.seen[0]
    assert headers["Authorization"] == "Bearer k123"
    assert payload["source"] == "resting_watch" and payload["severity"] == "critical"
    assert {r["status"] for r in _rows(tmp_path).values()} == {"sent"}


def test_custom_auth_header(tmp_path, hook):
    env = {"POLYCLAUDE_WAKE_URL": hook, "POLYCLAUDE_WAKE_KEY": "abc",
           "POLYCLAUDE_WAKE_AUTH_HEADER": "X-Wake-Key", "POLYCLAUDE_WAKE_AUTH_SCHEME": ""}
    _run(tmp_path, "[NEWS REVIEW REQUEST: x slug=abc-def]", env)
    headers, _ = _Hook.seen[0]
    assert headers["X-Wake-Key"] == "abc" and "Authorization" not in headers


def test_run_subcommand_has_no_model_backend():
    r = subprocess.run([sys.executable, str(SCRIPT), "run", "--profile", "fast"],
                       input="x", text=True, capture_output=True)
    assert r.returncode == 75
