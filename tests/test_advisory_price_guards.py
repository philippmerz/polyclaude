"""Focused regressions for sibling labels and executable-price advisories."""

from __future__ import annotations

import datetime as dt
import json
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import check_marginal_apy as marginal  # noqa: E402
import polyclaude_enter as entry  # noqa: E402


def test_same_deadline_threshold_ladder_is_not_called_different_deadline() -> None:
    at_least_50 = (
        "Will the highest score achieved by an OpenAI model on Humanity's Last "
        "Exam in 2026 be 50 or higher?"
    )
    at_least_55 = at_least_50.replace("50 or higher", "55 or higher")

    assert entry._sib_datesig(at_least_50) == entry._sib_datesig(at_least_55)
    assert entry._sibling_kind(at_least_50, at_least_55) == (
        "same deadline — threshold sibling, NOT fungible"
    )


def test_sibling_kind_still_distinguishes_deadlines_and_true_duplicates() -> None:
    assert entry._sibling_kind(
        "Will X happen by August 31, 2026?",
        "Will X happen by September 30, 2026?",
    ) == "different deadline — term-structure sibling, NOT fungible"
    assert entry._sibling_kind(
        "Will X happen before 2027?",
        "Will X happen by end of 2026?",
    ) == "CANDIDATE TRUE DUP (same deadline)"


def test_month_name_detection_uses_word_boundaries() -> None:
    assert entry._sib_datesig("Will X maybe happen in 2026?") == entry._sib_datesig(
        "Will X happen in 2026?"
    )


def test_single_buy_cap_applies_to_exact_signed_raw_limit() -> None:
    # Fine-tick amount precision rounds a 0.293 touch to a 0.30 signed limit.
    assert entry._single_buy_preflight(0.293, 0.001, 0.30) == pytest.approx(0.30)
    with pytest.raises(RuntimeError, match="exceeds --max-price"):
        entry._single_buy_preflight(0.301, 0.001, 0.30)
    with pytest.raises(ValueError, match=r"in \(0,1\)"):
        entry._single_buy_preflight(0.20, 0.01, 1.0)


def test_maker_preflight_preserves_passive_price_without_taker_ceiling() -> None:
    ask = 0.193
    maker_price = entry.maker_rest_price(0.191, ask, 0.001)

    assert maker_price == pytest.approx(0.19)
    assert entry._single_buy_preflight(
        maker_price, 0.001, 0.20, maker=True) == pytest.approx(maker_price)
    assert maker_price < ask
    with pytest.raises(ValueError, match="two-decimal amount precision"):
        entry._single_buy_preflight(0.192, 0.001, 0.20, maker=True)


def test_cli_help_explains_signed_live_max_price() -> None:
    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "polyclaude_enter.py"), "--help"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=15,
        check=True,
    )
    help_text = " ".join(result.stdout.split())
    assert "--max-price" in help_text
    assert "signed price" in help_text
    assert "fresh live ask" in help_text
    assert "preserve their already-gated post-only price" in help_text


def test_execute_rechecks_live_ask_and_never_submits_above_cap(
        monkeypatch, capsys) -> None:
    market = {
        "question": "Will the cap hold?",
        "slug": "cap-test",
        "id": "1",
        "umaResolutionStatus": None,
        "endDate": "2026-12-31T00:00:00Z",
        "outcomePrices": json.dumps([0.29, 0.71]),
        "outcomes": json.dumps(["Yes", "No"]),
        "clobTokenIds": json.dumps(["yes-token", "no-token"]),
        "orderPriceMinTickSize": 0.01,
        "takerBaseFee": None,
        "negRisk": False,
    }
    asks = iter([0.29, 0.31])  # gate-time touch, then immediate execution touch
    monkeypatch.setattr(entry, "fetch_market_by_slug_or_question", lambda _q: market)
    monkeypatch.setattr(entry, "_existing_exposure", lambda *_args: None)
    monkeypatch.setattr(entry, "_sibling_markets", lambda *_args: None)
    monkeypatch.setattr(entry, "_best_ask", lambda _token: next(asks))
    monkeypatch.setattr(
        entry.httpx,
        "get",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("no book")),
    )
    submitted = []
    monkeypatch.setattr(
        entry.subprocess,
        "run",
        lambda *args, **kwargs: submitted.append((args, kwargs)),
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "polyclaude_enter.py", "--slug", "cap-test", "--side", "YES",
            "--my-p", "0.80", "--edge-haircut", "0.10", "--usd", "10",
            "--bankroll", "100", "--max-price", "0.30", "--execute",
        ],
    )

    assert entry.main() == 0
    output = capsys.readouterr().out
    assert "hard price cap at execution" in output
    assert "0.3100 exceeds --max-price 0.3000" in output
    assert submitted == []


def test_sell_signal_uses_bid_for_both_negative_edge_and_hurdle() -> None:
    signal = marginal._sell_side_signal(
        prior_p=0.65,
        midpoint=0.67,
        best_bid=0.64,
        days=100,
        hurdle_apy=0.05,
    )

    assert signal["midpoint_above_fair"] is True
    assert signal["midpoint_edge_apy"] < 0
    assert signal["bid_edge_apy"] > 0.05
    assert signal["negative_edge"] is False
    assert signal["below_hurdle"] is False
    assert signal["would_flag"] is False


def _run_marginal_main(monkeypatch, capsys, tmp_path: Path, *, bid: float) -> dict:
    slug = "wide-book-position"
    prior_path = tmp_path / "priors.json"
    prior_path.write_text(json.dumps({
        slug: {"p_no": 0.65, "verified": dt.date.today().isoformat()},
    }))
    end = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=100)).isoformat()
    position = {
        "title": "Wide book",
        "slug": slug,
        "outcome": "No",
        "size": 100,
        "avgPrice": 0.60,
        "curPrice": 0.67,
        "endDate": end,
    }
    monkeypatch.setattr(marginal, "PRIORS_PATH", prior_path)
    monkeypatch.setattr(marginal, "_resolve_wallet_address", lambda: "0xabc")
    monkeypatch.setattr(marginal, "_fetch_positions", lambda _addr: [position])
    monkeypatch.setattr(
        marginal,
        "_exit_quote",
        lambda *_args, **_kwargs: {
            "best_bid": bid,
            "net": bid * 100,
            "avg_fill": bid,
            "unfilled": 0.0,
        },
    )
    monkeypatch.setattr(
        sys, "argv",
        ["check_marginal_apy.py", "--hurdle-apy", "0.05", "--json"],
    )

    assert marginal.main() == 0
    return json.loads(capsys.readouterr().out)


def test_main_keeps_midpoint_for_display_but_clears_on_executable_bid(
        monkeypatch, capsys, tmp_path: Path) -> None:
    result = _run_marginal_main(monkeypatch, capsys, tmp_path, bid=0.64)

    assert result["flagged"] == []
    assert len(result["holds"]) == 1
    row = result["holds"][0]
    assert row["mark"] == 0.67
    assert row["midpoint_above_fair"] is True
    assert row["expected_edge_apy_pct"] < 0
    assert row["sell_bid"] == 0.64
    assert row["sell_bid_expected_edge_apy_pct"] > 5.0


def test_main_still_flags_when_executable_bid_is_above_fair(
        monkeypatch, capsys, tmp_path: Path) -> None:
    result = _run_marginal_main(monkeypatch, capsys, tmp_path, bid=0.66)

    assert len(result["flagged"]) == 1
    assert result["flagged"][0]["verdict"].startswith("NEGATIVE_EDGE")
    assert result["flagged"][0]["sell_bid"] == 0.66
