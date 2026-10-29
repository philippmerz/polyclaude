#!/usr/bin/env python3
"""Text and key plan for /usr/local/bin/pc-session-inject.

Scheduled prompts are multiline. A tmux bracketed paste of that shape becomes a
[Pasted: N lines] chip and never reaches prompt.enqueue. This module rewrites
a mid-message /goal mention, classifies a pane capture, and types the lines
with the remote newline chord (a trailing backslash, then Enter). A message
that starts with /goal keeps that leading command.
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

SOCK = "/tmp/tmux-1000/default"
SESSION = "grok:0.0"
CHUNK = 400


class InjectError(Exception):
    def __init__(self, message: str, clear: bool = False) -> None:
        super().__init__(message)
        self.clear = clear


def rewrite_prompt(src: str) -> str:
    """Drop a /goal mention that is not the leading command.

    Grok refuses to send a message that contains /goal unless the message
    itself starts with that command. It logs prompt.enqueue and restores the
    draft. The path scripts/goal_inject.sh contains the same character sequence,
    so it is rewritten first.
    """
    if src.startswith("/goal"):
        head, tail = src[:5], src[5:]
        tail = tail.replace("scripts/goal_inject.sh", "goal_inject.sh")
        tail = tail.replace("/goal", "goal")
        return head + tail
    text = src.replace("scripts/goal_inject.sh", "goal_inject.sh")
    return text.replace("/goal", "goal")


def _composer(lines: list[str]) -> tuple[str, str, str]:
    """Return waiting, footer, composer body from a tmux capture."""
    n = len(lines)
    waiting = "0"
    footer = "other"
    start = max(0, n - 8)
    foot = " ".join(lines[start:])
    # Alt+Enter:send contains the substring Enter:send. Match the longer one first.
    if "Enter:queue" in foot:
        footer = "queue"
    elif "Alt+Enter:send" in foot:
        footer = "alt"
    elif "Enter:send" in foot:
        footer = "send"
    for i in range(n - 1, max(-1, n - 40), -1):
        if "╭" in lines[i]:
            for j in range(i - 1, max(-1, i - 4), -1):
                if "Waiting…" in lines[j]:
                    waiting = "1"
            break
    body: list[str] = []
    beg = None
    for i in range(n - 1, -1, -1):
        if "❯" in lines[i]:
            beg = i
            break
    if beg is not None:
        for i in range(beg, n):
            if "╰" in lines[i]:
                break
            body.append(lines[i])
    return waiting, footer, "\n".join(body)


def classify_capture(capture: str, needle: str) -> str:
    """One line: waiting footer draft.

    waiting is 0 or 1. footer is send, queue, alt, or other.
    draft is empty, ours, foreign, chip, stuck, or unknown.
    """
    waiting, footer, text = _composer(capture.splitlines())
    if "❯" not in capture:
        draft = "unknown"
    elif "[Pasted:" in text:
        draft = "chip"
    elif needle and needle in text:
        draft = "ours"
    else:
        stripped = text.replace("❯", "").replace("│", "").replace(" ", "").replace("\n", "")
        if stripped == "":
            draft = "empty"
        elif "Cron tick " in text:
            draft = "stuck"
        else:
            draft = "foreign"
    return f"{waiting} {footer} {draft}"


def composer_text(capture: str) -> str:
    return _composer(capture.splitlines())[2]


def prompt_lines(text: str) -> list[str]:
    lines = text.split("\n")
    if lines and lines[-1] == "":
        lines = lines[:-1]
    return lines


def literal_chunks(line: str, size: int = CHUNK) -> list[str]:
    if line == "":
        return []
    return [line[i : i + size] for i in range(0, len(line), size)]


def newline_actions(footer: str) -> list[tuple[str, str]]:
    """Keys that insert a newline and do not send.

    Over this tmux, extended-keys are off, so Alt+Enter is not a reliable
    chord. A trailing backslash then Enter is the remote newline. In
    /multiline mode the footer is alt and plain Enter inserts the newline.
    """
    if footer == "alt":
        return [("key", "Enter")]
    return [("literal", "\\"), ("key", "Enter")]


def find_drain(blob: str, since: str, sid: str) -> dict | None:
    """Return the ctx of the first prompt.drain or prompt.drain_blocked at or after since."""
    import json

    nl = blob.find("\n")
    # A tail slice can start mid-line. Drop that partial record.
    if nl != -1 and not blob.startswith("{"):
        blob = blob[nl + 1 :]
    for line in blob.splitlines():
        i = line.find("{")
        if i < 0:
            continue
        try:
            obj = json.loads(line[i:])
        except json.JSONDecodeError:
            continue
        if obj.get("sid") != sid:
            continue
        ts = obj.get("ts") or ""
        if ts < since:
            continue
        if obj.get("msg") in ("prompt.drain", "prompt.drain_blocked"):
            ctx = obj.get("ctx")
            return ctx if isinstance(ctx, dict) else {"msg": obj.get("msg")}
    return None


class Tmux:
    def literal(self, text: str) -> None:
        raise NotImplementedError

    def key(self, name: str) -> None:
        raise NotImplementedError

    def capture(self) -> str:
        raise NotImplementedError


class LiveTmux(Tmux):
    def _run(self, args: list[str], capture: bool = False) -> str:
        result = subprocess.run(
            ["/usr/sbin/runuser", "-u", "philipp", "--", "/usr/bin/tmux", "-S", SOCK, *args],
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            detail = (result.stderr or result.stdout or "tmux failed").strip()
            raise InjectError(detail[:200])
        return result.stdout if capture else ""

    def literal(self, text: str) -> None:
        if text == "":
            return
        self._run(["send-keys", "-t", SESSION, "-l", "--", text])

    def key(self, name: str) -> None:
        self._run(["send-keys", "-t", SESSION, name])

    def capture(self) -> str:
        return self._run(["capture-pane", "-p", "-t", SESSION], capture=True)


def _apply(tmux: Tmux, actions: list[tuple[str, str]], sleep, pause: float) -> None:
    for kind, value in actions:
        if kind == "literal":
            tmux.literal(value)
        elif kind == "key":
            tmux.key(value)
        else:
            raise InjectError(f"unknown action {kind}")
        if pause:
            sleep(pause)


def insert_text(
    text: str,
    tmux: Tmux,
    sleep=time.sleep,
    literal_pause: float = 0.04,
    newline_pause: float = 0.15,
) -> None:
    """Type text into the focused composer. Do not press the send key."""
    lines = prompt_lines(text)
    if not lines or not any(line.strip() for line in lines):
        raise InjectError("refusing to type an empty prompt")
    _apply(tmux, [("literal", chunk) for chunk in literal_chunks(lines[0])], sleep, literal_pause)
    sleep(newline_pause)
    _waiting, footer, _draft = classify_capture(tmux.capture(), "").split()
    if footer == "queue":
        raise InjectError("composer is queueing, not idle")
    for line in lines[1:]:
        _apply(tmux, newline_actions(footer), sleep, newline_pause)
        draft = classify_capture(tmux.capture(), "").split()[2]
        if draft == "empty":
            raise InjectError("newline chord submitted the draft")
        _apply(tmux, [("literal", chunk) for chunk in literal_chunks(line)], sleep, literal_pause)
    sleep(newline_pause)
    capture = tmux.capture()
    state = classify_capture(capture, "")
    draft = state.split()[2]
    if draft == "chip":
        raise InjectError("typed text collapsed to a paste chip", clear=True)
    last = ""
    for line in reversed(lines):
        if line.strip():
            last = line
            break
    prefix = last[:24]
    visible = composer_text(capture)
    if prefix and prefix not in visible:
        # Esc Esc on an empty composer opens rewind. Clear only a confirmed draft.
        raise InjectError(
            "typed text did not appear in the composer",
            clear=draft not in ("empty", "unknown"),
        )


def clear_idle_draft(tmux: Tmux, sleep=time.sleep) -> None:
    """Esc Esc within 800ms clears a nonempty idle draft. It does not send Ctrl+C."""
    tmux.key("Escape")
    sleep(0.2)
    tmux.key("Escape")
    sleep(0.4)


def insert_file(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    tmux = LiveTmux()
    try:
        insert_text(text, tmux)
    except InjectError as exc:
        if exc.clear:
            try:
                clear_idle_draft(tmux)
            except InjectError:
                pass
        print(str(exc), file=sys.stderr)
        raise SystemExit(75) from exc


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("usage: session_inject_text.py rewrite|classify|insert|drain-since", file=sys.stderr)
        return 64
    cmd = argv[1]
    if cmd == "rewrite":
        if len(argv) != 4:
            print("usage: session_inject_text.py rewrite SRC DEST|-", file=sys.stderr)
            return 64
        out = rewrite_prompt(Path(argv[2]).read_text(encoding="utf-8"))
        if argv[3] == "-":
            sys.stdout.write(out)
        else:
            Path(argv[3]).write_text(out, encoding="utf-8")
        return 0
    if cmd == "classify":
        print(classify_capture(sys.stdin.read(), os.environ.get("NEEDLE", "")))
        return 0
    if cmd == "insert":
        if len(argv) != 3:
            print("usage: session_inject_text.py insert FILE", file=sys.stderr)
            return 64
        insert_file(Path(argv[2]))
        return 0
    if cmd == "drain-since":
        if len(argv) != 4:
            print("usage: session_inject_text.py drain-since SINCE SID", file=sys.stderr)
            return 64
        import json

        found = find_drain(sys.stdin.read(), argv[2], argv[3])
        if found is None:
            return 1
        sys.stdout.write(json.dumps(found) + "\n")
        return 0
    print(f"unknown command {cmd}", file=sys.stderr)
    return 64


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
