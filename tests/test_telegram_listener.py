import os
from pathlib import Path
import stat
import subprocess
import sys
import time
from unittest import mock


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
os.environ.setdefault("POLYCLAUDE_TELEGRAM_TOKEN", "/tmp/test-telegram-token")
os.environ.setdefault("POLYCLAUDE_TELEGRAM_STATE", "/tmp/test-telegram-state")
os.environ.setdefault("POLYCLAUDE_LISTENER_PID", "/tmp/test-telegram-pid")

import telegram_listener as listener  # noqa: E402


def _update(update_id: int, chat_id: int, text: str, sent_at: int = 1_700_000_000):
    return {
        "update_id": update_id,
        "message": {
            "message_id": update_id + 100,
            "date": sent_at,
            "chat": {"id": chat_id},
            "text": text,
        },
    }


def test_ingest_authorizes_spools_then_advances_cursor(tmp_path, monkeypatch, capsys):
    state_path = tmp_path / "state.json"
    queue_path = tmp_path / "queue.json"
    monkeypatch.setattr(listener, "STATE_PATH", state_path)
    monkeypatch.setattr(listener, "QUEUE_PATH", queue_path)
    state = {"chat_id": 42, "last_update_id": 0}
    queue = {"version": 1, "items": []}

    accepted = listener._ingest_updates(
        [_update(1, 999, "foreign secret"), _update(2, 42, "authorized secret")],
        state,
        queue,
        42,
    )

    assert accepted == 1
    assert state["last_update_id"] == 2
    assert [item["update_id"] for item in queue["items"]] == [2]
    assert queue["items"][0]["text"] == "authorized secret"
    assert stat.S_IMODE(state_path.stat().st_mode) == 0o600
    assert stat.S_IMODE(queue_path.stat().st_mode) == 0o600
    logs = capsys.readouterr().out
    assert "foreign secret" not in logs
    assert "authorized secret" not in logs
    assert "999" not in logs


def test_enqueue_deduplicates_stable_update_id(tmp_path, monkeypatch):
    monkeypatch.setattr(listener, "QUEUE_PATH", tmp_path / "queue.json")
    queue = {"version": 1, "items": []}
    update = _update(7, 42, "once")
    assert listener._enqueue(queue, update, "once") is True
    assert listener._enqueue(queue, update, "once") is False
    assert len(queue["items"]) == 1

    queue["items"].clear()
    queue["delivered_ids"] = [7]
    assert listener._enqueue(queue, update, "once") is False

    queue["delivered_ids"] = []
    queue["quarantined"] = [{"update_id": 7}]
    assert listener._enqueue(queue, update, "once") is False


def test_stale_envelope_requires_reconfirmation():
    item = {
        "update_id": 8,
        "message_id": 108,
        "sent_at": 1_700_000_000,
        "text": "do the consequential thing",
    }
    envelope = listener._delivery_envelope(
        item, now=1_700_000_000 + listener.STALE_INSTRUCTION_SECONDS + 1
    )
    assert envelope.startswith("telegram: [update_id=8")
    assert "do not execute the stale instruction" in envelope
    assert "do the consequential thing" in envelope


def test_delivery_uses_stdin_not_process_arguments(tmp_path, monkeypatch):
    runner = tmp_path / "runner"
    runner.write_text("#!/bin/sh\nexit 0\n")
    runner.chmod(0o700)
    monkeypatch.setattr(listener, "RUNNER", runner)
    monkeypatch.setattr(listener, "REPO_ROOT", tmp_path)
    completed = subprocess.CompletedProcess([], 0, "", "")
    item = {"update_id": 9, "message_id": 109, "sent_at": int(time.time()), "text": "private text"}

    with mock.patch.object(listener.subprocess, "run", return_value=completed) as run:
        listener._deliver(item)

    args, kwargs = run.call_args
    assert "private text" not in " ".join(args[0])
    assert "private text" in kwargs["input"]
    assert args[0] == [
        str(runner),
        "queue",
        "--workdir",
        str(tmp_path),
        "--reference-id",
        "9",
        "--expires-at",
        str(int(item["sent_at"]) + listener.STALE_INSTRUCTION_SECONDS),
    ]


def test_stale_item_is_quarantined_and_fresh_item_continues(tmp_path, monkeypatch):
    monkeypatch.setattr(listener, "QUEUE_PATH", tmp_path / "queue.json")
    now = int(time.time())
    queue = {
        "version": 2,
        "items": [
            {"update_id": 10, "sent_at": now - 601, "text": "old command"},
            {"update_id": 11, "sent_at": now, "text": "fresh correction"},
        ],
        "quarantined": [],
        "delivered_ids": [],
    }
    delivered = []
    notices = []
    monkeypatch.setattr(listener, "_deliver", lambda item: delivered.append(item["update_id"]))
    monkeypatch.setattr(
        listener,
        "_notify_sender",
        lambda _token, _chat, text: notices.append(text) or True,
    )

    assert listener._drain_pending(queue, "token", 42) == 1
    assert delivered == [11]
    assert queue["items"] == []
    assert [item["update_id"] for item in queue["quarantined"]] == [10]
    assert queue["quarantined"][0]["warning_sent"] is True
    assert queue["delivered_ids"] == [11]
    assert len(notices) == 1


def test_missing_timestamp_fails_closed_even_if_notice_fails(tmp_path, monkeypatch):
    monkeypatch.setattr(listener, "QUEUE_PATH", tmp_path / "queue.json")
    queue = {
        "version": 2,
        "items": [{"update_id": 12, "sent_at": 0, "text": "unknown age"}],
        "quarantined": [],
        "delivered_ids": [],
    }
    deliver = mock.Mock()
    monkeypatch.setattr(listener, "_deliver", deliver)
    monkeypatch.setattr(listener, "_notify_sender", mock.Mock(side_effect=OSError("down")))

    assert listener._drain_pending(queue, "token", 42) == 0
    deliver.assert_not_called()
    assert queue["items"] == []
    assert queue["quarantined"][0]["update_id"] == 12
    assert queue["quarantined"][0]["warning_sent"] is False


def test_drain_preserves_order_after_failure(tmp_path, monkeypatch):
    monkeypatch.setattr(listener, "QUEUE_PATH", tmp_path / "queue.json")
    queue = {
        "version": 1,
        "items": [
            {"update_id": 1, "sent_at": int(time.time()), "attempts": 0, "next_attempt_at": 0, "text": "one"},
            {"update_id": 2, "sent_at": int(time.time()), "attempts": 0, "next_attempt_at": 0, "text": "two"},
        ],
    }
    delivered = []

    def fail_first(item):
        delivered.append(item["update_id"])
        raise RuntimeError("down")

    monkeypatch.setattr(listener, "_deliver", fail_first)
    monkeypatch.setattr(listener, "_notify_sender", lambda *args: True)
    assert listener._drain_pending(queue, "token", 42) == 0
    assert delivered == [1]
    assert [item["update_id"] for item in queue["items"]] == [1, 2]

    queue["items"][0]["next_attempt_at"] = 0
    delivered.clear()
    monkeypatch.setattr(listener, "_deliver", lambda item: delivered.append(item["update_id"]))
    assert listener._drain_pending(queue, "token", 42) == 2
    assert delivered == [1, 2]
    assert queue["items"] == []
    assert queue["delivered_ids"] == [1, 2]


def test_listener_singleton_lock_is_lifetime_scoped(tmp_path, monkeypatch):
    listener._release_pid()
    monkeypatch.setattr(listener, "PID_PATH", tmp_path / "listener.pid")
    monkeypatch.setattr(listener, "LOCK_PATH", tmp_path / "listener.pid.lock")
    monkeypatch.setattr(listener, "_pid_is_listener", lambda _pid: False)

    assert listener._claim_pid() is True
    assert listener._claim_pid() is False
    listener._release_pid()
    assert listener._claim_pid() is True
    listener._release_pid()
