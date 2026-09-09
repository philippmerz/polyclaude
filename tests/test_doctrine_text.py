import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FEE_DOCTRINE_PATHS = (
    ROOT / "notes" / "resting_orders.md",
    ROOT / "scripts" / "daily_checkin.sh",
    ROOT / "scripts" / "limitless_arb_scan.py",
    ROOT / "scripts" / "limitless_arb_executor.py",
    ROOT / "scripts" / "sports_pm_scan.py",
    ROOT / "scripts" / "polyclaude_enter.py",
    ROOT / "scripts" / "polymarket_consistency_scan.py",
)
HIDDEN_INFO_PATHS = (
    ROOT / "notes" / "resting_orders.md",
    ROOT / "scripts" / "daily_checkin.sh",
    ROOT / "scripts" / "portfolio_kelly.py",
)
ACTIVE_SCRIPT_PATHS = tuple(
    sorted(
        path
        for pattern in ("*.py", "*.sh")
        for path in (ROOT / "scripts").glob(pattern)
        # pm_fees.py explicitly documents the superseded curve as history next
        # to the canonical implementation; executable/advisory callers may not.
        if path.name != "pm_fees.py"
    )
)


def _normalized(path: Path) -> str:
    return (
        path.read_text(encoding="utf-8")
        .lower()
        .replace("×", "x")
        .replace("−", "-")
    )


def test_active_fee_guidance_names_canonical_helper():
    for path in FEE_DOCTRINE_PATHS:
        text = _normalized(path)
        assert "pm_fees.py" in text


def test_operator_guidance_uses_structured_curve_and_legacy_only_cap():
    for path in (
        ROOT / "notes" / "resting_orders.md",
        ROOT / "scripts" / "daily_checkin.sh",
    ):
        text = _normalized(path)
        assert "rate x [p x (1-p)]^exponent" in text
        assert "feeschedule" in text
        assert "0.07 cap retained only for legacy compatibility" in text


def test_scalar_rate_helpers_do_not_claim_full_structured_fee_support():
    for filename in ("limitless_arb_scan.py", "sports_pm_scan.py"):
        text = _normalized(ROOT / "scripts" / filename)
        assert "legacy" in text
        assert "exponent" in text


def test_tick_summaries_remain_material_only():
    lessons = _normalized(ROOT / "strategy" / "01_lessons.md")
    driver = _normalized(ROOT / "scripts" / "daily_checkin.sh")
    assert "material-only" in lessons
    assert "material-only" in driver
    assert re.search(r"heartbeat\s+every tick", lessons) is None


def test_telegram_reader_exceptions_are_in_operator_onboarding():
    readme = _normalized(ROOT / "README.md")
    assert "already_claimed" in readme
    assert "expired" in readme
    assert "private one-time" in readme


def test_no_active_script_reintroduces_linear_tail_fee_curve():
    old_curve = re.compile(
        r"min\s*\(\s*([a-z_][a-z0-9_]*)\s*,\s*1\s*-\s*\1\s*\)"
    )
    for path in ACTIVE_SCRIPT_PATHS:
        assert old_curve.search(_normalized(path)) is None, (
            f"superseded fee curve remains in {path}"
        )


def test_live_fee_callers_delegate_to_canonical_helper():
    scanner = _normalized(ROOT / "scripts" / "limitless_arb_scan.py")
    executor = _normalized(ROOT / "scripts" / "limitless_arb_executor.py")
    sports = _normalized(ROOT / "scripts" / "sports_pm_scan.py")
    enter = _normalized(ROOT / "scripts" / "polyclaude_enter.py")
    consistency = _normalized(ROOT / "scripts" / "polymarket_consistency_scan.py")

    assert "return pm_fees.fee_per_share_at(raw_rate, p)" in scanner
    assert 'result["fee_market"]' in scanner
    assert "return pm_fees.fee_per_share(fee_rate, p)" in scanner
    # Pure per-level math owns fees; the public-data wrapper owns identity.
    quote_math = _normalized(ROOT / "scripts" / "limitless_quote_math.py")
    assert "quote_pair(" in executor
    assert "fee_per_share(dict(market), float(price))" in quote_math
    assert "fee_per_share = pm_fees.fee_per_share_at(raw_rate, p)" in sports
    assert "cost = p + fee_per_share" in sports
    assert "market_fee_rate = pm_fees.fee_rate(m)" in sports
    assert "_ofee = pm_fees.fee_per_share(m, _oask)" in enter
    assert "fee_per_share = pm_fees.fee_per_share(m, mark)" in enter
    assert "return pm_fees.fee_per_share(market, p)" in consistency
    assert 'fees = sum(q["fee_per_share"] for q in side_quotes)' in consistency
    assert "total_fees = _basket_fee_per_unit(valid)" in consistency


def test_hidden_info_guidance_allows_only_premium_to_fair_sells():
    stale_blanket_rules = (
        "get no resting take-profit sells",
        "get none",
        "except on hidden-info-class",
        "no resting sell",
    )
    for path in (*ACTIVE_SCRIPT_PATHS, ROOT / "notes" / "resting_orders.md"):
        text = _normalized(path)
        assert all(stale not in text for stale in stale_blanket_rules)

    for path in HIDDEN_INFO_PATHS:
        text = _normalized(path)
        assert "at or below fair" in text
        assert "premium-to-fair" in text
        assert "strictly above fair" in text


def test_live_clob_not_a_static_markdown_snapshot():
    text = _normalized(ROOT / "notes" / "resting_orders.md")
    assert "live orders (all 7" not in text
    assert "| placed | position | side | shares | price | fair | note |" not in text
    assert ".venv/bin/python scripts/clob_v2.py orders" in text
    assert "authoritative live order set" in text
