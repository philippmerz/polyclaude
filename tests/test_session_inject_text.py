"""The live injector types through session_inject_text.py. These tests call that module."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def _load():
    path = REPO / "scripts" / "session_inject_text.py"
    spec = importlib.util.spec_from_file_location("session_inject_text", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


MOD = _load()


def test_rewrite_removes_a_mid_message_goal_and_keeps_newlines() -> None:
    src = "Cron tick.\n\nSee scripts/goal_inject.sh and one /goal line.\n"
    out = MOD.rewrite_prompt(src)
    assert out == "Cron tick.\n\nSee goal_inject.sh and one goal line.\n"
    assert "/goal" not in out
    assert out.count("\n") == src.count("\n")


def test_rewrite_keeps_a_leading_goal_and_strips_a_later_one() -> None:
    src = "/goal fix scripts/goal_inject.sh when it pastes /goal\n"
    out = MOD.rewrite_prompt(src)
    assert out == "/goal fix goal_inject.sh when it pastes goal\n"
    assert out.startswith("/goal ")
    assert out.count("/goal") == 1


def test_rewrite_keeps_goal_clear() -> None:
    assert MOD.rewrite_prompt("/goal clear\n") == "/goal clear\n"


def test_goal_inject_script_still_emits_a_leading_command() -> None:
    text = (REPO / "scripts" / "goal_inject.sh").read_text(encoding="utf-8")
    assert 'line="/goal clear"' in text
    assert 'line="/goal ${objective}"' in text


def test_classify_ours_chip_and_empty() -> None:
    needle = "INJECT-PROOF-1 token alpha."
    ours = (
        "Waiting…\n"
        "╭\n"
        f"❯ {needle} rest of the line\n"
        "│ second line\n"
        "╰\n"
        "Enter:send │ Alt+Enter:newline\n"
    )
    assert MOD.classify_capture(ours, needle) == "1 send ours"
    chip = "╭\n❯ [Pasted: 11 lines]\n╰\nEnter:send\n"
    assert MOD.classify_capture(chip, needle).endswith(" chip")
    empty = "╭\n│ ❯ \n╰\nShift+Tab:mode │ Ctrl+c:cancel\n"
    assert MOD.classify_capture(empty, needle) == "0 other empty"
    alt = "╭\n❯ hello\n╰\nAlt+Enter:send │ Enter:newline\n"
    assert MOD.classify_capture(alt, "hello").split()[1] == "alt"
    queued = "▾ Queued 1\n#1 a user message\n╭\n❯ \n╰\nEnter:send now │ Shift+Tab:mode\n"
    assert MOD.classify_capture(queued, needle).split()[1] == "sendnow"
    hint = "▾ Queued 1\n╭\n❯ \n╰\nEnter:send now │ Ctrl+;:queue\n"
    assert MOD.classify_capture(hint, needle).split()[1] == "sendnow"
    behind = (
        "▾ Queued 1\n#1 a user message\n╭\n"
        f"❯ {needle}\n╰\n"
        "Enter:queue │ Alt+Enter:newline\n"
    )
    assert MOD.classify_capture(behind, needle) == "0 queue ours"


def test_find_drain_ignores_enqueue_and_older_events() -> None:
    sid = "01a178b6-f938-7ca3-91a9-9538c2e791ef"
    rows = [
        {"ts": "2026-10-28T08:00:00.000Z", "sid": sid, "msg": "prompt.drain", "ctx": {"prompt_len": 10}},
        {"ts": "2026-10-29T10:00:00.000Z", "sid": sid, "msg": "prompt.enqueue", "ctx": {"len": 2024}},
        {
            "ts": "2026-10-29T10:00:01.000Z",
            "sid": sid,
            "msg": "prompt.drain",
            "ctx": {"kind": "prompt", "prompt_len": 1800, "remaining_in_queue": 0},
        },
    ]
    blob = "\n".join(json.dumps(row) for row in rows)
    found = MOD.find_drain(blob, "2026-10-29T10:00:00", sid)
    assert found is not None
    assert found["prompt_len"] == 1800
    assert MOD.find_drain(blob, "2026-10-29T11:00:00", sid) is None


class _FakeTmux:
    def __init__(self, send_on_enter: bool = False) -> None:
        self.actions: list[tuple[str, str]] = []
        self.parts: list[str] = []
        self.send_on_enter = send_on_enter

    def literal(self, text: str) -> None:
        self.actions.append(("literal", text))
        self.parts.append(text)

    def key(self, name: str) -> None:
        self.actions.append(("key", name))
        if name != "Enter":
            return
        if self.send_on_enter:
            self.parts.clear()
            return
        if self.parts and self.parts[-1] == "\\":
            self.parts.pop()
        self.parts.append("\n")

    def capture(self) -> str:
        body = "".join(self.parts)
        if not body:
            return "╭\n❯ \n╰\nShift+Tab:mode\n"
        shown = body.replace("\n", "\n│ ")
        return f"╭\n❯ {shown}\n╰\nEnter:send │ Alt+Enter:newline\n"


def test_insert_types_every_line_and_does_not_send() -> None:
    text = "\n".join(
        [
            "INJECT-PROOF-1. Stop immediately. Do not trade.",
            "",
            "padding line two " + ("x" * 80),
            "padding line three",
            "padding line four",
            "padding line five",
            "padding line six",
            "padding line seven",
            "The injector must remove a later goal token.",
            "INJECT-PROOF-1-END",
        ]
    )
    assert text.count("\n") >= 8
    tmux = _FakeTmux()
    MOD.insert_text(text, tmux, sleep=lambda _seconds: None, literal_pause=0, newline_pause=0)
    typed = "".join(value for kind, value in tmux.actions if kind == "literal" and value != "\\")
    assert typed == "\n".join(MOD.prompt_lines(text)).replace("\n", "")
    # A newline between lines, and no final Enter that would send.
    enters = [i for i, (kind, value) in enumerate(tmux.actions) if kind == "key" and value == "Enter"]
    assert len(enters) == text.count("\n")
    assert tmux.actions[-1] != ("key", "Enter")
    assert all(tmux.actions[i - 1] == ("literal", "\\") for i in enters)


def test_insert_stops_when_enter_submits() -> None:
    text = "INJECT-PROOF-2 stop now\nsecond line must not be typed\nINJECT-PROOF-2-END"
    tmux = _FakeTmux(send_on_enter=True)
    try:
        MOD.insert_text(text, tmux, sleep=lambda _seconds: None, literal_pause=0, newline_pause=0)
    except MOD.InjectError as exc:
        assert "submitted" in str(exc)
    else:
        raise AssertionError("insert kept typing after Enter submitted")
    literals = [value for kind, value in tmux.actions if kind == "literal"]
    assert "second line must not be typed" not in "\n".join(literals)


def test_queued_count_reads_the_followup_row() -> None:
    pane = "▾ Queued 1\n#1 a user note\n╭\n❯ \n╰\nEnter:send now\n"
    assert MOD.queued_count(pane) == 1
    assert MOD.queued_count("╭\n❯ \n╰\nEnter:send\n") == 0


def test_multiline_footer_uses_plain_enter_for_newlines() -> None:
    assert MOD.newline_actions("alt") == [("key", "Enter")]
    assert MOD.newline_actions("send")[0] == ("literal", "\\")
    assert MOD.newline_actions("other")[0] == ("literal", "\\")


def test_injector_source_types_through_the_module() -> None:
    source = (REPO / "scripts" / "pc-session-inject").read_text(encoding="utf-8")
    assert "session_inject_text.py" in source
    assert "--enqueue" in source
    assert "queued-count" in source
    assert "clear-busy" in source
    assert "paste-buffer" not in source
    assert "C-c" not in source
    live = Path("/usr/local/bin/pc-session-inject").read_text(encoding="utf-8")
    assert live == source
