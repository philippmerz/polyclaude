"""Offline documentation routing/size contracts; no live services or credentials."""

from pathlib import Path
import re
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
CURRENT = (
    "docs/START.md", "README.md", "docs/INDEX.md", "docs/checkin.md",
    "scripts/README.md", "strategy/00_philosophy.md", "strategy/01_lessons.md",
    "strategy/02_operations.md", "docs/reference/reporting.md",
    "docs/reference/emergency.md", "notes/backlog.md", "notes/resting_orders.md",
    "notes/fade_basket.md", "notes/recoup_campaign.md",
    "notes/arb_thesis_check_2026-06-10.md", "research/INDEX.md",
)
LINK = re.compile(r"\[[^\]\n]+\]\(([^)]+)\)")


def local_links(path):
    for target in LINK.findall(path.read_text()):
        if urlsplit(target).scheme or target.startswith("//"):
            continue
        location, _, fragment = unquote(target).partition("#")
        yield ((path.parent / location).resolve() if location else path), fragment


def heading_ids(path):
    # Sufficient GFM heading slug support for this KB; ignore fenced examples.
    result = set()
    counts = {}
    fence = None
    for line in path.read_text().splitlines():
        match = re.match(r"^\s*(`{3,}|~{3,})", line)
        if match:
            token = match.group(1)
            if fence is None:
                fence = token
            elif token[0] == fence[0] and len(token) >= len(fence):
                fence = None
            continue
        if fence:
            continue
        heading = re.match(r"^#{1,6}\s+(.+)", line)
        if not heading:
            continue
        title = heading.group(1).strip().lower()
        title = re.sub(r"[^\w\- ]", "", title)
        slug = title.replace(" ", "-")
        duplicate = counts.get(slug, 0)
        counts[slug] = duplicate + 1
        result.add(slug if duplicate == 0 else f"{slug}-{duplicate}")
    return result


def test_current_document_links_resolve():
    for name in CURRENT:
        path = ROOT / name
        for target, fragment in local_links(path):
            assert target.is_relative_to(ROOT), (name, target)
            assert target.exists(), (name, target)
            if fragment and target.suffix == ".md":
                assert fragment in heading_ids(target), (name, target, fragment)


def test_all_repo_prose_has_a_route():
    files = {ROOT / "README.md", ROOT / "PRIMER.md", ROOT / "scripts/README.md"}
    for directory in ("docs", "strategy", "notes", "research"):
        for suffix in ("*.md", "*.txt"):
            files.update((ROOT / directory).rglob(suffix))
    # Files are indexed centrally or through their canonical topic, not auto-loaded.
    linked = {ROOT / name for name in CURRENT}
    for name in CURRENT:
        linked.update(target for target, _ in local_links(ROOT / name))
    assert not files - linked, sorted(str(p.relative_to(ROOT)) for p in files - linked)


def test_startup_and_active_documents_stay_small():
    budgets = {
        "docs/START.md": 600, "README.md": 700,
        "strategy/00_philosophy.md": 1200, "strategy/01_lessons.md": 1500,
        "notes/backlog.md": 1500, "notes/resting_orders.md": 700,
    }
    for name, maximum in budgets.items():
        assert len((ROOT / name).read_text().split()) <= maximum, name


def test_archive_files_identify_historical_authority():
    for path in (ROOT / "docs/archive").glob("*.md"):
        beginning = path.read_text()[:700].lower()
        assert "archive" in beginning and ("histor" in beginning or "not current" in beginning), path


def test_checklist_keeps_all_required_commands_and_steps():
    text = (ROOT / "docs/checkin.md").read_text()
    assert re.findall(r"^## (\d+)\.", text, flags=re.M) == [str(n) for n in range(1, 12)]
    for command in (
        "positions.py", "wallet_status.py", "crypto_status.py", "bankroll.py",
        "clob_v2.py orders", "ostium_client.py status", "uma_status_check.py",
        "ostium_state_diff.py", "crux_coverage_check.py --quiet",
        "check_marginal_apy.py", "watchlist_monitor.py --hits-only --auto-revet",
        "position_state_audit.py --fix", "exit_analysis.py", "decisions.py pending",
        "portfolio_kelly.py --constrained", "clob_v2.py redeem-all --dry-run",
        "discover_markets.py", "--min-liquidity 500 --min-vol24 20",
        "sports_pm_scan.py --hours 36 --with-consensus --consensus-top-n 3",
        "macro_pm_scan.py --no-consensus --days 60",
        "event_monotonicity_scan.py", "polymarket_consistency_scan.py",
        "favorite_fade_scan.py --min-edge-pp 3", "world_state_digest.py",
        "longterm_check.py", "notes/pnl_weekly.md",
    ):
        assert command in text, command
    assert ">8 days" in text
    assert "15% ticket/30% cluster" in text
    # Keep this contract about the canonical checklist's routing and shape;
    # execution-authority wording belongs to the current operating docs.
    assert "# Scheduled check-in" in text


def test_public_onboarding_does_not_require_host_private_file():
    driver = (ROOT / "scripts/daily_checkin.sh").read_text()
    onboarding = driver.partition("Onboard first, in this order:")[2].splitlines()[0]
    assert "docs/START.md" in onboarding
    assert "AGENTS.md" not in onboarding
    assert "strategy/01_lessons.md" not in onboarding
    assert "PRIMER.md" not in onboarding
