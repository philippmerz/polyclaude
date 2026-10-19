from __future__ import annotations

import sys
from decimal import Decimal
from types import SimpleNamespace

import pytest

sys.path.insert(0, "scripts")

import book_walk  # noqa: E402
import polyclaude_enter as entry  # noqa: E402


NOW = 1_800_000_000.0
TOKEN = "yes-token"
CONDITION = "0xabc"


def _book(**changes):
    result = {
        "asset_id": TOKEN, "market": CONDITION,
        "timestamp": str(int(NOW * 1000)), "tick_size": "0.001",
        "min_order_size": "5",
        "bids": [{"price": "0.001", "size": "2000"}],
        "asks": [{"price": "0.002", "size": "2000"}],
    }
    result.update(changes)
    return result


class _BookResponse:
    def __init__(self, payload):
        self.payload = payload

    def json(self):
        return self.payload

    def raise_for_status(self):
        return None


def _install_main_mocks(monkeypatch, books, *, execute=False):
    market = {
        "id": "test-market", "conditionId": CONDITION,
        "question": "Will the test resolve yes?", "slug": "test-market",
        "umaResolutionStatus": None, "endDate": "2027-01-01T00:00:00Z",
        "outcomePrices": '["0.50", "0.50"]',
        "clobTokenIds": '["yes-token", "no-token"]',
        "outcomes": '["Yes", "No"]', "events": [],
        "negRisk": False, "orderPriceMinTickSize": 0.001,
        "feesEnabled": False,
    }
    monkeypatch.setattr(entry.time, "time", lambda: NOW)
    monkeypatch.setattr(entry, "fetch_market_by_slug_or_question", lambda _q: market)
    monkeypatch.setattr(entry, "_existing_exposure", lambda *_a: None)
    monkeypatch.setattr(entry, "_sibling_markets", lambda *_a: None)
    monkeypatch.setattr(entry, "_best_ask", lambda _t: 0.002)
    monkeypatch.setattr(entry, "_fetch_live_positions", lambda: [])
    monkeypatch.setattr(entry, "_fetch_open_buy_commitments", lambda: [])
    monkeypatch.setattr(entry, "_merge_entry_commitments", lambda *a, **_k: [])
    cap_calls = []

    def cap_state(_m, _positions, _bankroll, risk, *_args):
        cap_calls.append(risk)
        return {"ticket_after": 1.0, "ticket_cap": 15.0,
                "cluster_after": 1.0, "cluster_cap": 30.0,
                "cluster": "test"}

    monkeypatch.setattr(entry, "_single_entry_cap_state", cap_state)
    monkeypatch.setattr(entry, "_single_entry_cap_error", lambda _state: None)
    monkeypatch.setattr(entry, "_reservation_indexed_bought", lambda *_a: 0.0)
    book_iter = iter(books)
    monkeypatch.setattr(entry.httpx, "get",
                        lambda *_a, **_k: _BookResponse(next(book_iter)))
    argv = ["polyclaude_enter.py", "--slug", "test-market", "--side", "YES",
            "--my-p", "0.99", "--skip-catalyst-check", "--maker",
            "--maker-price", "0.001", "--usd", "1", "--bankroll", "100"]
    if execute:
        argv.append("--execute")
    monkeypatch.setattr(sys, "argv", argv)
    return cap_calls


def test_mocked_main_dry_run_uses_exact_fine_tick_price_and_cash(monkeypatch, capsys):
    cap_calls = _install_main_mocks(monkeypatch, [_book(), _book()])
    assert entry.main() == 0
    output = capsys.readouterr().out
    assert "1000 integer shares; exact signed cash $1.000" in output
    assert "WOULD_REST $1.00 of YES @ 0.001" in output
    assert cap_calls == [1.0]


def test_mocked_main_execute_keeps_exact_price_cash_risk_and_post_only(monkeypatch):
    cap_calls = _install_main_mocks(monkeypatch, [_book(), _book(), _book()], execute=True)
    reservations = []
    commands = []
    monkeypatch.setattr(entry, "_acquire_entry_lock", lambda: object())
    monkeypatch.setattr(entry, "_add_entry_reservation",
                        lambda record: reservations.append(record) or "reservation-1")
    monkeypatch.setattr(entry, "_update_entry_reservation", lambda *_a, **_k: None)
    monkeypatch.setattr(entry, "_classify_clob_result",
                        lambda *_a, **_k: ("matched", {"body": {}}))

    def fake_run(command, **_kwargs):
        commands.append(command)
        return SimpleNamespace(returncode=0, stdout="mocked", stderr="")

    monkeypatch.setattr(entry.subprocess, "run", fake_run)
    assert entry.main() == 0
    assert cap_calls == [1.0, 1.0]
    assert reservations[0]["risk"] == 1.0
    assert reservations[0]["shares"] == 1000.0
    assert reservations[0]["limitPrice"] == "0.001"
    command = commands[0]
    assert command[3:6] == [TOKEN, "0.001", "1.000"]
    assert "--post-only" in command and "--reservation-id" in command


@pytest.mark.parametrize(
    "bad_initial",
    [
        {"asset_id": None}, {"asset_id": "wrong"}, {"market": None},
        {"market": "0xwrong"}, {"timestamp": None}, {"timestamp": "NaN"},
        {"timestamp": str(int((NOW + 1) * 1000))},
        {"timestamp": str(int((NOW - 181) * 1000))},
    ],
)
def test_mocked_main_rejects_bad_initial_identity_or_timestamp_before_entry(
    monkeypatch, capsys, bad_initial
):
    initial = _book(**bad_initial)
    _install_main_mocks(monkeypatch, [initial, _book()], execute=True)
    monkeypatch.setattr(entry, "_add_entry_reservation",
                        lambda *_a: pytest.fail("invalid initial book reached reservation"))
    monkeypatch.setattr(entry.subprocess, "run",
                        lambda *_a, **_k: pytest.fail("invalid initial book reached writer"))
    assert entry.main() == 2
    assert "book" in capsys.readouterr().out


@pytest.mark.parametrize(
    "bad_final",
    [
        {"asset_id": None}, {"asset_id": "wrong"},
        {"market": None}, {"market": "0xwrong"},
        {"timestamp": None},
        {"timestamp": str(int((NOW + 1) * 1000))},
        {"timestamp": str(int((NOW - 181) * 1000))},
        {"asks": [{"price": "0.001", "size": "5"}]},
        {"tick_size": "0.01"}, {"min_order_size": "0"},
        {"min_order_size": "NaN"}, {"min_order_size": "1001"},
    ],
)
def test_mocked_main_rejects_changed_final_book_before_reservation_or_writer(
    monkeypatch, capsys, bad_final
):
    _install_main_mocks(monkeypatch, [_book(), _book(), _book(**bad_final)], execute=True)
    monkeypatch.setattr(entry, "_add_entry_reservation",
                        lambda *_a: pytest.fail("invalid final book reached reservation"))
    monkeypatch.setattr(entry.subprocess, "run",
                        lambda *_a, **_k: pytest.fail("invalid final book reached writer"))
    assert entry.main() == 1
    assert "NEED_REVIEW" in capsys.readouterr().out


def test_fine_tick_price_and_integer_cash_lot_at_one_mil():
    price = entry._validate_fine_tick_maker_price("0.001", "0.001", "0.002")
    shares, cash = entry._fine_tick_maker_size("1.00", price, "5")
    assert (shares, cash) == (1000, Decimal("1.000"))
    assert entry._single_buy_preflight(
        "0.001", "0.001", maker=True, allow_fine_tick_maker=True) == 0.001


def test_price_293_uses_ten_share_cash_lot_and_floors_budget():
    price = entry._validate_fine_tick_maker_price("0.293", "0.001", "0.294")
    shares, cash = entry._fine_tick_maker_size("5.85", price, "5")
    assert shares == 10
    assert cash == Decimal("2.930")
    assert cash <= Decimal("5.85")
    assert cash * 100 == (cash * 100).to_integral_value()


@pytest.mark.parametrize(
    ("price", "tick", "ask", "message"),
    [
        ("not-a-price", "0.001", "0.002", "finite decimal"),
        ("NaN", "0.001", "0.002", "finite decimal"),
        ("0.0015", "0.001", "0.002", "align exactly"),
        ("0.002", "0.001", "0.002", "strictly below"),
        ("0.001", "0.001", None, "without a live ask"),
    ],
)
def test_explicit_price_validation_fails_closed(price, tick, ask, message):
    with pytest.raises(ValueError, match=message):
        entry._validate_fine_tick_maker_price(price, tick, ask)


def test_fine_tick_size_enforces_cash_and_live_share_minima():
    price = Decimal("0.001")
    with pytest.raises(ValueError, match=r"below \$1 minimum"):
        entry._fine_tick_maker_size("0.99", price, "5")
    with pytest.raises(ValueError, match="below live minimum"):
        entry._fine_tick_maker_size("1.00", price, "1001")


def test_default_maker_price_path_retains_cent_grid_and_preflight_guard():
    assert book_walk.maker_rest_price(0.008, 0.03, 0.001) == pytest.approx(0.01)
    with pytest.raises(ValueError, match="no positive price"):
        book_walk.maker_rest_price(0.001, 0.002, 0.001)
    with pytest.raises(ValueError, match="two-decimal amount precision"):
        entry._single_buy_preflight("0.001", "0.001", maker=True)
    with pytest.raises(ValueError, match="requires --maker"):
        entry._single_buy_preflight(
            "0.001", "0.001", allow_fine_tick_maker=True)
    with pytest.raises(RuntimeError, match="exceeds --max-price"):
        entry._single_buy_preflight(
            "0.001", "0.001", "0.0009999999995", maker=True,
            allow_fine_tick_maker=True)


@pytest.mark.parametrize(
    "argv",
    [
        ["polyclaude_enter.py", "--maker-price", "0.001", "--my-p", "0.9", "--slug", "x"],
        ["polyclaude_enter.py", "--maker", "--maker-price", "0.001",
         "--bundle-slug", "one", "--bundle-slug", "two", "--side", "YES",
         "--my-p", "0.9", "--bundle-shares", "10", "--max-bundle-cost", "0.5"],
    ],
)
def test_flag_scope_is_rejected_before_default_bankroll_or_market_reads(monkeypatch, argv):
    monkeypatch.setattr(sys, "argv", argv)
    monkeypatch.setattr(
        entry, "_bankroll_default",
        lambda: pytest.fail("flag-scope errors must precede bankroll reads"),
    )
    monkeypatch.setattr(
        entry, "fetch_market_by_slug_or_question",
        lambda *_: pytest.fail("flag-scope errors must precede market reads"),
    )
    assert entry.main() == 2
