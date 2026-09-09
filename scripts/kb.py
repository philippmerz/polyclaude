#!/usr/bin/env python3
"""Small, read-only, bounded retrieval helper for the local knowledge base."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import re
import sys
from typing import Callable


ROOT = Path(__file__).resolve().parent.parent
MAX_OUTPUT = 6000
MAX_OUTPUT_LIMIT = 20000
MAX_SEARCH_HITS = 12
MATCH_LINE_LIMIT = 240
PROSE_SUFFIXES = {".md", ".txt"}
PRIVATE_PARTS = {"private", "inbox", "spool", "secrets", "credentials", "transcripts", "sessions"}
ALLOWED_TOP_LEVEL = {"notes", "strategy", "research", "docs", "scripts"}
ALLOWED_ROOT_FILES = {"readme.md", "primer.md", "agents.md"}

CURRENT_FILES = (
    "docs/START.md",
    "README.md",
    "scripts/README.md",
    "docs/INDEX.md",
    "docs/checkin.md",
    "notes/backlog.md",
    "notes/resting_orders.md",
    "notes/longterm_watchlist.md",
    "notes/primary_sources.md",
    "notes/capital_ledger.md",
)

HEADING_RE = re.compile(r"^(#{1,6})[ \t]+(.+?)\s*$")
DATE_RE = re.compile(r"(?<!\d)(20\d{2}[-/]\d{1,2}[-/]\d{1,2})(?!\d)")
HEADING_TIME_RE = re.compile(r"^(?:\*\*)?(\d{1,2}:\d{2})\b")
BODY_TIME_RE = re.compile(r"^\s*(?:[-*+]>?\s+|>\s+|\*\*)(\d{1,2}:\d{2})\b")
FENCE_RE = re.compile(r"^\s*(`{3,}|~{3,})")


class KBError(ValueError):
    """A user-facing, non-traceback retrieval error."""


def _is_prose(path: Path) -> bool:
    return path.suffix.lower() in PROSE_SUFFIXES or path.name.upper() == "README"


def _relative(path: Path, *, allow_dir: bool = False) -> Path:
    """Validate a user path and return its canonical in-repository file path."""
    raw = Path(path)
    if ".." in raw.parts:
        raise KBError("path traversal is not allowed")
    candidate = raw if raw.is_absolute() else ROOT / raw
    try:
        # Keep the lexical path for symlink checks, while separately checking
        # the resolved destination for an escape through a symlink.
        relative = candidate.absolute().relative_to(ROOT.absolute())
        candidate.resolve(strict=False).relative_to(ROOT.resolve())
    except ValueError as exc:
        raise KBError("path must stay inside the repository") from exc
    if not relative.parts or (
        len(relative.parts) == 1
        and relative.name.lower() not in ALLOWED_ROOT_FILES
        and relative.name.lower() not in ALLOWED_TOP_LEVEL
    ):
        raise KBError("path is outside the approved prose directories")
    if len(relative.parts) > 1 and relative.parts[0] not in ALLOWED_TOP_LEVEL:
        raise KBError("path is outside the approved prose directories")
    if any(part.startswith(".") or part.lower() in PRIVATE_PARTS for part in relative.parts):
        raise KBError("private or hidden paths are not readable")
    if relative.name.lower() == "agents.md":
        raise KBError("AGENTS.md is host-private; use docs/START.md")

    # Check every component, not just the final file, so a symlinked directory
    # cannot smuggle a file outside the repository into the reader.
    cursor = ROOT
    for part in relative.parts:
        cursor /= part
        if cursor.is_symlink():
            raise KBError("symlink paths are not readable")
    if not candidate.exists():
        raise KBError(f"file not found: {relative}")
    if allow_dir and candidate.is_dir():
        return candidate
    if not candidate.is_file():
        raise KBError("path is not a regular file")
    if not _is_prose(candidate):
        raise KBError("only Markdown/text prose files are readable")
    return candidate


def _display(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT.resolve()))


def _read(path: Path) -> list[str]:
    try:
        return path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError as exc:
        raise KBError(f"cannot read {_display(path)}") from exc


def _render_rows(
    header: str,
    rows: list[tuple[int, str]],
    limit: int,
    continuation: Callable[[int, str], str],
    tail: str = "",
) -> str:
    """Render complete source lines, reserving an exact continuation marker."""
    def marker(number: int, command: str) -> str:
        return f"\n[INCOMPLETE: output truncated before source line {number}]\nCONTINUE: {command}\n"

    text = header
    for index, (number, row) in enumerate(rows):
        reserve = len(tail) if not index + 1 < len(rows) and tail else 0
        if index + 1 < len(rows):
            next_number, next_row = rows[index + 1]
            reserve = len(marker(next_number, continuation(next_number, next_row)))
        candidate = text + "\n" + row
        if len(candidate) + reserve > limit:
            command = continuation(number, row)
            return text + marker(number, command)
        text = candidate
    if tail:
        if len(text) + len(tail) <= limit:
            return text + tail
        # A tail marker is reserved above, so this only occurs for a header
        # larger than the caller's bound; retain the explicit marker.
        return text + tail
    return text


def _fenced_headings(lines: list[str]) -> list[tuple[int, str, str]]:
    headings: list[tuple[int, str, str]] = []
    fence: str | None = None
    fence_len = 0
    for number, line in enumerate(lines, 1):
        fence_match = FENCE_RE.match(line)
        if fence_match:
            marker = fence_match.group(1)
            char = marker[0]
            if fence is None:
                fence, fence_len = char, len(marker)
            elif char == fence and len(marker) >= fence_len:
                fence = None
            continue
        if fence is None:
            match = HEADING_RE.match(line)
            if match:
                headings.append((number, match.group(1), match.group(2)))
    return headings


def _dated_entries(lines: list[str]) -> list[tuple[int, int, str]]:
    """Return (line number, end line number, display label) dated entries."""
    starts: list[tuple[int, str]] = []
    current_date: str | None = None
    fence: str | None = None
    fence_len = 0
    for number, line in enumerate(lines, 1):
        fence_match = FENCE_RE.match(line)
        if fence_match:
            marker = fence_match.group(1)
            char = marker[0]
            if fence is None:
                fence, fence_len = char, len(marker)
            elif char == fence and len(marker) >= fence_len:
                fence = None
            continue
        if fence is not None:
            continue

        heading = HEADING_RE.match(line)
        date_match = DATE_RE.search(heading.group(2) if heading else "")
        if heading and date_match:
            current_date = date_match.group(1)
            starts.append((number, f"{current_date} — {heading.group(2)}"))
            continue
        time_match = HEADING_TIME_RE.match(heading.group(2)) if heading else BODY_TIME_RE.match(line)
        if time_match and current_date:
            starts.append((number, f"{current_date} {time_match.group(1)} (date inherited)"))

    result: list[tuple[int, int, str]] = []
    for index, (start, label) in enumerate(starts):
        end = starts[index + 1][0] - 1 if index + 1 < len(starts) else len(lines)
        result.append((start, end, label))
    return result


def _walk_prose(base: Path, *, include_archive: bool) -> list[Path]:
    paths: list[Path] = []
    if base.is_file():
        return [base] if _is_prose(base) else []
    if not base.exists():
        return paths
    for directory, dirnames, filenames in os.walk(base, followlinks=False):
        directory_path = Path(directory)
        dirnames[:] = [
            name for name in dirnames
            if not name.startswith(".")
            and name.lower() not in PRIVATE_PARTS
            and not (directory_path / name).is_symlink()
        ]
        if not include_archive:
            dirnames[:] = [name for name in dirnames if name != "archive"]
        for name in filenames:
            path = directory_path / name
            if path.is_symlink() or not _is_prose(path):
                continue
            try:
                _relative(path)
            except KBError:
                continue
            paths.append(path)
    return paths


def _current_corpus() -> list[Path]:
    paths: list[Path] = []
    for item in CURRENT_FILES:
        path = ROOT / item
        if path.exists() and path.is_file() and not path.is_symlink():
            try:
                paths.append(_relative(path))
            except KBError:
                pass
    paths.extend(_walk_prose(ROOT / "strategy", include_archive=False))
    paths.extend(_walk_prose(ROOT / "docs/reference", include_archive=False))
    return sorted(set(paths), key=lambda path: str(path))


def _history_corpus() -> list[Path]:
    # Walk only approved trees; never descend through unrelated root data.
    paths: list[Path] = []
    for top in ("notes", "strategy", "research", "docs"):
        paths.extend(_walk_prose(ROOT / top, include_archive=True))
    scripts_readme = ROOT / "scripts/README.md"
    if scripts_readme.exists() and not scripts_readme.is_symlink():
        paths.append(_relative(scripts_readme))
    for name in ("README.md", "PRIMER.md"):
        path = ROOT / name
        if path.exists() and not path.is_symlink():
            try:
                paths.append(_relative(path))
            except KBError:
                pass
    return sorted(set(paths), key=lambda path: str(path))


def _max_arg(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("max chars must be an integer") from exc
    if not 256 <= parsed <= MAX_OUTPUT_LIMIT:
        raise argparse.ArgumentTypeError(f"max chars must be 256..{MAX_OUTPUT_LIMIT}")
    return parsed


def _search(args: argparse.Namespace) -> str:
    term = args.term.casefold()
    if args.path:
        base = _relative(args.path, allow_dir=True)
        corpus = _walk_prose(base, include_archive=args.history) if base.is_dir() else [base]
        if not args.history:
            corpus = [path for path in corpus if path in set(_current_corpus())]
    else:
        corpus = _history_corpus() if args.history else _current_corpus()
    hits: list[tuple[Path, int, str]] = []
    total = 0
    clipped = False
    first_omitted: tuple[Path, int] | None = None
    for path in corpus:
        for number, line in enumerate(_read(path), 1):
            if term not in line.casefold():
                continue
            total += 1
            if len(hits) >= MAX_SEARCH_HITS:
                first_omitted = first_omitted or (path, number)
                continue
            rendered = line
            if len(rendered) > MATCH_LINE_LIMIT:
                rendered = rendered[:MATCH_LINE_LIMIT].rstrip() + " …"
                clipped = True
                first_omitted = first_omitted or (path, number)
            hits.append((path, number, rendered))
    if not hits:
        return f"No matches for {args.term!r} in {'history' if args.history else 'current'} corpus."
    rows = [(number, f"{_display(path)}:{number}: {rendered}") for path, number, rendered in hits]
    if total > MAX_SEARCH_HITS:
        clipped = True
    if clipped:
        if first_omitted:
            omitted_path, omitted_line = first_omitted
            tail = f"\n[INCOMPLETE: search results are bounded to 12 hits and/or clipped lines]\nCONTINUE: read {_display(omitted_path)} --start {omitted_line} --lines 60 (next matching line is at or after this line)."
        else:
            tail = "\n[INCOMPLETE: search results are bounded to 12 hits and/or clipped lines]\nCONTINUE: rerun with a narrower term or an approved --path."
    else:
        tail = ""
    return _render_rows(
        f"Search {args.term!r} ({'history' if args.history else 'current'} corpus):",
        rows,
        args.max_chars,
        lambda line, row: f"read {row.split(':', 1)[0]} --start {line} --lines 60",
        tail,
    )


def _toc(args: argparse.Namespace) -> str:
    path = _relative(args.path)
    headings = _fenced_headings(_read(path))
    heading_total = len(headings)
    omitted = False
    if args.last is not None:
        omitted = len(headings) > args.last
        headings = headings[-args.last :]
    if not headings:
        return f"WARNING: no Markdown headings found in {_display(path)}."
    rows = [(number, f"{_display(path)}:{number}: {level} {title}") for number, level, title in headings]
    tail = ""
    if omitted:
        first = heading_total - len(headings) + 1
        tail = f"\n[INCOMPLETE: showing headings {first}-{heading_total} of {heading_total}; earlier headings omitted]\nCONTINUE: toc {_display(path)} (omit --last for the full heading list)."
    return _render_rows(
        f"FILE: {_display(path)}",
        rows,
        args.max_chars,
        lambda line, row: f"toc {_display(path)} (continue near source line {line})",
        tail,
    )


def _recent(args: argparse.Namespace) -> str:
    path = _relative(args.path)
    lines = _read(path)
    entries = _dated_entries(lines)
    if not entries:
        return f"WARNING: no dated entries found in {_display(path)}."
    selected = entries[-args.entries :]
    rows: list[tuple[int, str]] = []
    for start, end, label in selected:
        rows.append((start, f"--- {label} (line {start}) ---"))
        rows.extend((number, f"{number}: {lines[number - 1]}") for number in range(start, end + 1))
    tail = ""
    if len(entries) > len(selected):
        tail = f"\n[INCOMPLETE: {len(entries) - len(selected)} older dated entries omitted]\nCONTINUE: recent {_display(path)} --entries {len(entries)} for the omitted history."
    return _render_rows(
        f"FILE: {_display(path)}",
        rows,
        args.max_chars,
        lambda line, row: f"read {_display(path)} --start {line} --lines 60",
        tail,
    )


def _read_slice(args: argparse.Namespace) -> str:
    path = _relative(args.path)
    lines = _read(path)
    if args.start > len(lines):
        return f"WARNING: start line {args.start} is beyond end of {_display(path)} ({len(lines)} lines)."
    end = min(len(lines), args.start + args.lines - 1)
    rows = [(number, f"{number}: {lines[number - 1]}") for number in range(args.start, end + 1)]
    tail = ""
    if end < len(lines):
        tail = f"\n[INCOMPLETE: {_display(path)} continues after line {end}]\nCONTINUE: read {_display(path)} --start {end + 1} --lines {args.lines} (next line {end + 1})."
    return _render_rows(
        f"FILE: {_display(path)}",
        rows,
        args.max_chars,
        lambda line, row: f"read {_display(path)} --start {line} --lines {args.lines}",
        tail,
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Bounded, read-only local prose retrieval")
    commands = parser.add_subparsers(dest="command", required=True)

    search = commands.add_parser("search", help="search the current corpus or bounded history")
    search.add_argument("term")
    search.add_argument("--history", action="store_true")
    search.add_argument("--path", help="approved prose file or directory to search")
    search.add_argument("--max-chars", type=_max_arg, default=MAX_OUTPUT)

    toc = commands.add_parser("toc", help="list Markdown headings outside fenced code")
    toc.add_argument("path")
    toc.add_argument("--last", type=int, default=None)
    toc.add_argument("--max-chars", type=_max_arg, default=MAX_OUTPUT)

    recent = commands.add_parser("recent", help="show recent dated entries")
    recent.add_argument("path")
    recent.add_argument("--entries", type=int, default=2)
    recent.add_argument("--max-chars", type=_max_arg, default=MAX_OUTPUT)

    read = commands.add_parser("read", help="show a numbered line slice")
    read.add_argument("path")
    read.add_argument("--start", type=int, default=1)
    read.add_argument("--lines", type=int, default=60)
    read.add_argument("--max-chars", type=_max_arg, default=MAX_OUTPUT)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "search":
            output = _search(args)
        elif args.command == "toc":
            if args.last is not None and args.last < 1:
                raise KBError("--last must be positive")
            output = _toc(args)
        elif args.command == "recent":
            if args.entries < 1:
                raise KBError("--entries must be positive")
            output = _recent(args)
        else:
            if args.start < 1 or args.lines < 1:
                raise KBError("--start and --lines must be positive")
            output = _read_slice(args)
        print(output)
        return 0
    except KBError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
