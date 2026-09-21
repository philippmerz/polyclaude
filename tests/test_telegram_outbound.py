import argparse
import io
import os
from pathlib import Path
import sys


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
os.environ.setdefault("POLYCLAUDE_TELEGRAM_TOKEN", "/tmp/test-telegram-token")
os.environ.setdefault("POLYCLAUDE_TELEGRAM_STATE", "/tmp/test-telegram-state")

import telegram  # noqa: E402


def _args(**overrides):
    values = {
        "text": None,
        "stdin": False,
        "input_file": None,
        "parse_mode": None,
    }
    values.update(overrides)
    return argparse.Namespace(**values)


def test_stdin_preserves_shell_metacharacters_unicode_and_newlines(monkeypatch):
    body = "Wallet $170; literal $(date); `whoami`; café\nsecond line\n"
    monkeypatch.setattr(sys, "stdin", io.StringIO(body))

    assert telegram._message_text(_args(stdin=True)) == body


def test_input_file_preserves_literal_crlf(tmp_path):
    body = b"Wallet $164.65\r\nLiteral $1 and $(date)\r\n"
    path = tmp_path / "message.txt"
    path.write_bytes(body)

    assert telegram._message_text(_args(input_file=path)) == body.decode()


def test_positional_text_remains_backward_compatible():
    assert telegram._message_text(_args(text="ordinary argv text")) == "ordinary argv text"


def test_message_source_must_be_exactly_one(monkeypatch, tmp_path):
    monkeypatch.setattr(sys, "stdin", io.StringIO("stdin"))
    path = tmp_path / "message.txt"
    path.write_text("file")

    for args in (
        _args(),
        _args(text="argv", stdin=True),
        _args(stdin=True, input_file=path),
    ):
        try:
            telegram._message_text(args)
        except ValueError as exc:
            assert "exactly one" in str(exc)
        else:
            raise AssertionError("ambiguous message source was accepted")


def test_cmd_msg_rejects_missing_source_before_loading_credentials(monkeypatch):
    monkeypatch.setattr(
        telegram, "_token", lambda: (_ for _ in ()).throw(AssertionError("token read"))
    )

    assert telegram.cmd_msg(_args()) == 2


def test_cmd_msg_sends_stdin_body_without_changes(monkeypatch):
    body = "Values: $170, $164.65, and $12.35\n"
    payloads = []

    class Response:
        @staticmethod
        def json():
            return {"ok": True, "result": {"message_id": 1}}

    class Client:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def post(self, _url, json):
            payloads.append(json)
            return Response()

    monkeypatch.setattr(sys, "stdin", io.StringIO(body))
    monkeypatch.setattr(telegram, "_token", lambda: "token")
    monkeypatch.setattr(telegram, "_chat_id", lambda: 42)
    monkeypatch.setattr(telegram.httpx, "Client", lambda **_kwargs: Client())

    assert telegram.cmd_msg(_args(stdin=True)) == 0
    assert payloads == [
        {
            "chat_id": 42,
            "text": body,
            "disable_web_page_preview": True,
        }
    ]
