"""Telegram bridge for polyclaude.

Reads bot token from <HOME>/telegram_token.txt (outside the repo) and
caches the operator's chat_id to <HOME>/.polyclaude_telegram.json
(also outside the repo, 0600). Subcommands:

    setup            Poll for the latest incoming message and store its chat_id.
                     Operator must send a message to the bot first.
    msg "<text>"     Send a text message. Long text auto-splits at ~3500 chars.
    file <path> [-c "caption"]
                     Send a file as a document. Up to 50 MB.
    md <path>        Send a markdown file. If small, send as text; if large,
                     send as document (preserving fences/structure).

All subcommands exit 0 on success, non-zero with a JSON error blob on failure.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import httpx

TOKEN_PATH = Path("<SECRETS>/telegram_token.txt")
STATE_PATH = Path("<HOME>/.polyclaude_telegram.json")
API = "https://api.telegram.org"
TEXT_CHUNK = 3500  # < 4096 Telegram limit, leaves room for markdown formatting
SMALL_MD_LIMIT = 3000  # send shorter md as text


def _token() -> str:
    return TOKEN_PATH.read_text().strip()


def _state() -> dict:
    if not STATE_PATH.exists():
        return {}
    return json.loads(STATE_PATH.read_text())


def _save_state(state: dict) -> None:
    STATE_PATH.write_text(json.dumps(state, indent=2))
    os.chmod(STATE_PATH, 0o600)


def _chat_id() -> int:
    s = _state()
    cid = s.get("chat_id")
    if not cid:
        print("ERROR: chat_id not configured. Have the operator message the bot, then run: telegram.py setup", file=sys.stderr)
        sys.exit(2)
    return int(cid)


def cmd_setup(_args: argparse.Namespace) -> int:
    token = _token()
    with httpx.Client(timeout=15) as c:
        r = c.get(f"{API}/bot{token}/getUpdates", params={"timeout": 0})
        r.raise_for_status()
        data = r.json()
    if not data.get("ok"):
        print(json.dumps(data, indent=2)); return 1
    updates = data["result"]
    if not updates:
        print("No updates yet. Have the operator send any message to the bot, then re-run setup.", file=sys.stderr)
        return 3
    # Find the most recent private chat
    candidates = []
    for u in updates:
        msg = u.get("message") or u.get("edited_message")
        if not msg: continue
        chat = msg.get("chat", {})
        if chat.get("type") == "private":
            candidates.append((u["update_id"], chat))
    if not candidates:
        print("Found updates but no private-chat messages. Send the bot a direct message.", file=sys.stderr)
        return 3
    candidates.sort(key=lambda x: x[0])
    chat = candidates[-1][1]
    state = _state()
    state["chat_id"] = chat["id"]
    state["operator_username"] = chat.get("username")
    state["operator_first_name"] = chat.get("first_name")
    _save_state(state)
    print(f"chat_id stored: {chat['id']}  (@{chat.get('username')}, {chat.get('first_name')})")
    return 0


def _split(text: str, n: int = TEXT_CHUNK) -> list[str]:
    if len(text) <= n:
        return [text]
    parts: list[str] = []
    while text:
        if len(text) <= n:
            parts.append(text); break
        # try to break at a newline
        cut = text.rfind("\n", 0, n)
        if cut < n // 2:
            cut = n
        parts.append(text[:cut])
        text = text[cut:].lstrip("\n")
    return parts


def cmd_msg(args: argparse.Namespace) -> int:
    token = _token(); chat_id = _chat_id()
    text = args.text
    parse_mode = args.parse_mode
    chunks = _split(text)
    with httpx.Client(timeout=20) as c:
        for i, chunk in enumerate(chunks):
            payload = {"chat_id": chat_id, "text": chunk, "disable_web_page_preview": True}
            if parse_mode:
                payload["parse_mode"] = parse_mode
            r = c.post(f"{API}/bot{token}/sendMessage", json=payload)
            j = r.json()
            if not j.get("ok"):
                print(json.dumps(j, indent=2)); return 1
            if i == 0:
                print(f"sent message_id {j['result']['message_id']} ({len(chunks)} part{'s' if len(chunks)>1 else ''})")
    return 0


def cmd_file(args: argparse.Namespace) -> int:
    token = _token(); chat_id = _chat_id()
    p = Path(args.path).expanduser().resolve()
    if not p.exists():
        print(f"ERROR: {p} not found", file=sys.stderr); return 1
    if p.stat().st_size > 50 * 1024 * 1024:
        print(f"ERROR: {p} > 50 MB (Telegram limit for bot uploads)", file=sys.stderr); return 1
    with httpx.Client(timeout=120) as c:
        with p.open("rb") as f:
            files = {"document": (p.name, f)}
            data = {"chat_id": str(chat_id)}
            if args.caption:
                data["caption"] = args.caption
            r = c.post(f"{API}/bot{token}/sendDocument", files=files, data=data)
        j = r.json()
        if not j.get("ok"):
            print(json.dumps(j, indent=2)); return 1
        print(f"sent document_id {j['result']['message_id']}  ({p.name}, {p.stat().st_size} bytes)")
    return 0


def cmd_md(args: argparse.Namespace) -> int:
    p = Path(args.path).expanduser().resolve()
    if not p.exists():
        print(f"ERROR: {p} not found", file=sys.stderr); return 1
    body = p.read_text()
    if len(body) <= SMALL_MD_LIMIT:
        ns = argparse.Namespace(text=body, parse_mode=None)
        return cmd_msg(ns)
    ns = argparse.Namespace(path=str(p), caption=args.caption or p.name)
    return cmd_file(ns)


def main() -> int:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("setup", help="Discover and store chat_id from getUpdates")
    s.set_defaults(func=cmd_setup)

    s = sub.add_parser("msg", help="Send a text message")
    s.add_argument("text")
    s.add_argument("--parse-mode", default=None, choices=[None, "Markdown", "MarkdownV2", "HTML"])
    s.set_defaults(func=cmd_msg)

    s = sub.add_parser("file", help="Send a file as a document")
    s.add_argument("path")
    s.add_argument("-c", "--caption", default=None)
    s.set_defaults(func=cmd_file)

    s = sub.add_parser("md", help="Send a markdown file (text if small, document if large)")
    s.add_argument("path")
    s.add_argument("-c", "--caption", default=None)
    s.set_defaults(func=cmd_md)

    args = p.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
