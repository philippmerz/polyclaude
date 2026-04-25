"""HackMD bridge for polyclaude.

Uploads markdown to the operator's HackMD account via the v1 API and prints the
shareable URL. Reads token from <HOME>/hackmd_token.txt (outside the repo).

The token is generated at https://hackmd.io/settings#api — single click, then
saved here as the only line in the file.

Subcommands:

    upload <md_path> [--title T] [--read PERM] [--write PERM]
        Create a new note from a markdown file. Prints the note URL on stdout.
        PERM ∈ {owner, signed_in, guest}; default read=guest, write=owner.

    update <noteId> <md_path>
        Replace an existing note's content (so weekly reports can rev in place).

    list [--limit N]
        List the most recent notes (id, title, publishLink).

    me
        Sanity-check the token by hitting /v1/me.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import httpx

TOKEN_PATH = Path("<HOME>/hackmd_token.txt")
API = "https://api.hackmd.io/v1"
HACKMD_BASE = "https://hackmd.io"


def _token() -> str:
    if not TOKEN_PATH.exists():
        print(f"ERROR: token file {TOKEN_PATH} not found. Generate at https://hackmd.io/settings#api and save token there (chmod 600).", file=sys.stderr)
        sys.exit(2)
    return TOKEN_PATH.read_text().strip()


def _headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {_token()}", "Content-Type": "application/json"}


def _note_url(note: dict) -> str:
    """Best-effort URL extraction. HackMD returns several link variants."""
    for k in ("publishLink", "permalinkUrl", "noteUrl"):
        if note.get(k):
            return note[k]
    if note.get("permalink"):
        return f"{HACKMD_BASE}/s/{note['permalink']}"
    if note.get("id"):
        return f"{HACKMD_BASE}/{note['id']}"
    return "(no URL field returned — full response printed below)"


def cmd_upload(args: argparse.Namespace) -> int:
    md = Path(args.path).expanduser().resolve()
    if not md.exists():
        print(f"ERROR: {md} not found", file=sys.stderr); return 1
    body = md.read_text()
    title = args.title or md.stem.replace("_", " ").replace("-", " ")
    payload = {
        "title": title,
        "content": body,
        "readPermission": args.read,
        "writePermission": args.write,
        "commentPermission": "everyone",
    }
    with httpx.Client(timeout=30) as c:
        r = c.post(f"{API}/notes", headers=_headers(), json=payload)
    if r.status_code >= 300:
        print(f"ERROR: HTTP {r.status_code}", file=sys.stderr)
        try: print(json.dumps(r.json(), indent=2), file=sys.stderr)
        except Exception: print(r.text, file=sys.stderr)
        return 1
    note = r.json()
    print(_note_url(note))
    if args.verbose:
        print(json.dumps(note, indent=2), file=sys.stderr)
    return 0


def cmd_update(args: argparse.Namespace) -> int:
    md = Path(args.path).expanduser().resolve()
    if not md.exists():
        print(f"ERROR: {md} not found", file=sys.stderr); return 1
    body = md.read_text()
    payload = {"content": body}
    with httpx.Client(timeout=30) as c:
        r = c.patch(f"{API}/notes/{args.note_id}", headers=_headers(), json=payload)
    if r.status_code >= 300:
        print(f"ERROR: HTTP {r.status_code}\n{r.text}", file=sys.stderr); return 1
    print(f"updated note {args.note_id}")
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    with httpx.Client(timeout=20) as c:
        r = c.get(f"{API}/notes", headers=_headers())
    if r.status_code >= 300:
        print(f"ERROR: HTTP {r.status_code}\n{r.text}", file=sys.stderr); return 1
    notes = r.json()
    for n in notes[: args.limit]:
        print(f"{n.get('id'):24s}  {(n.get('title') or '(untitled)')[:50]:50s}  {_note_url(n)}")
    return 0


def cmd_me(_args: argparse.Namespace) -> int:
    with httpx.Client(timeout=15) as c:
        r = c.get(f"{API}/me", headers=_headers())
    if r.status_code >= 300:
        print(f"ERROR: HTTP {r.status_code}\n{r.text}", file=sys.stderr); return 1
    print(json.dumps(r.json(), indent=2))
    return 0


def main() -> int:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("upload"); s.add_argument("path"); s.add_argument("--title")
    s.add_argument("--read", default="guest", choices=["owner", "signed_in", "guest"])
    s.add_argument("--write", default="owner", choices=["owner", "signed_in", "guest"])
    s.add_argument("-v", "--verbose", action="store_true")
    s.set_defaults(func=cmd_upload)

    s = sub.add_parser("update"); s.add_argument("note_id"); s.add_argument("path")
    s.set_defaults(func=cmd_update)

    s = sub.add_parser("list"); s.add_argument("--limit", type=int, default=20)
    s.set_defaults(func=cmd_list)

    s = sub.add_parser("me"); s.set_defaults(func=cmd_me)

    args = p.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
