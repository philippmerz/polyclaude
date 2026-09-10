from __future__ import annotations

import sys
import subprocess
from pathlib import Path
from types import SimpleNamespace


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import polyclaude_status as status  # noqa: E402
import positions  # noqa: E402


CURRENT_POSITIONS_OUTPUT = """
OPEN TOTAL  cost $44.26  mtm $52.90  max-payout $64.00  unrealised P&L $+8.64  (+19.52%)
Max payout if every held outcome wins: $64.00  (+44.42%)
REALIZABLE (depth-walked, NET of taker fees): $46.81  (+5.76%)  — midpoints overstate by $6.09
"""


def test_run_script_preserves_stderr_from_successful_command(monkeypatch) -> None:
    completed = SimpleNamespace(
        returncode=0,
        stdout="financial output\n",
        stderr="warning: fallback value used\n",
    )
    monkeypatch.setattr(status.subprocess, "run", lambda *args, **kwargs: completed)

    output = status.run_script(["scripts/example.py"])

    assert output == "financial output\n[stderr] warning: fallback value used"


def test_hurdle_summary_keeps_actionable_rows_and_success_diagnostics() -> None:
    output = """# 8 clear; 3 flagged (NEGATIVE_EDGE / below-hurdle); 0 protected group(s)

=== FLAGGED (negative edge at own prior, or expected edge < hurdle) ===
  [NEGATIVE_EDGE — EXIT CLEARS COST] No 0.800 | 10.0d | example one
  [CLOSE_CANDIDATE — EXIT CLEARS COST] No 0.950 | 40.0d | example two
  [NO_PRIOR (gross-carry only)] No 0.990 | 400.0d | below hurdle example

=== HOLDS (expected edge clears hurdle) ===
  No 0.500 | 100.0d | routine hold
[stderr] warning: one quote used a fallback
"""

    summary = status.summarize_hurdle_output(output)

    assert "NEGATIVE_EDGE" in summary
    assert "CLOSE_CANDIDATE" in summary
    assert "below hurdle example" in summary
    assert "[stderr] warning: one quote used a fallback" in summary
    assert "routine hold" not in summary
    assert summary != "(see full check_marginal_apy.py output)"


def test_telegram_summary_carries_current_net_depth_value() -> None:
    message = status.format_telegram_summary(CURRENT_POSITIONS_OUTPUT, "2026-09-07T23:00 UTC")

    assert "PM cost $44.26 mtm $52.90" in message
    assert "realizable $46.81 (depth-walked, NET of taker fees)" in message
    assert "best bids" not in message


def test_tight_book_without_realizable_line_does_not_invent_one() -> None:
    output = (
        "OPEN TOTAL  cost $10.00  mtm $10.25  max-payout $12.00  "
        "unrealised P&L $+0.25  (+2.50%)\n"
    )

    message = status.format_telegram_summary(output, "2026-09-07T23:00 UTC")

    assert "PM cost $10.00 mtm $10.25" in message
    assert "realizable" not in message


def test_no_open_positions_is_reported_without_unknown_financial_values() -> None:
    message = status.format_telegram_summary(
        "(no open positions)",
        "2026-09-07T23:00 UTC",
    )

    assert "PM positions: no open positions" in message
    assert "PM cost $? mtm $?" not in message


def test_unavailable_realizable_check_is_kept_as_diagnostic() -> None:
    output = (
        "OPEN TOTAL  cost $10.00  mtm $10.25  max-payout $12.00\n"
        "(realizable check unavailable: gamma timeout)\n"
    )

    message = status.format_telegram_summary(output, "2026-09-07T23:00 UTC")

    assert "(realizable check unavailable: gamma timeout)" in message


def test_failed_positions_never_produce_financial_summary() -> None:
    message = status.format_telegram_summary(
        "OPEN TOTAL  cost $10.00  mtm $10.25",
        "2026-09-07T23:00 UTC",
        positions_returncode=2,
    )

    assert "PM position check failed: exit 2" in message
    assert "realizable unavailable (positions check failed)" in message
    assert "PM cost" not in message
    assert "mtm $10.25" not in message


def test_missing_open_total_is_explicitly_unavailable() -> None:
    message = status.format_telegram_summary(
        "positions returned an unexpected payload",
        "2026-09-07T23:00 UTC",
    )

    assert "PM cost/mtm unavailable (positions output missing OPEN TOTAL)" in message
    assert "PM cost $? mtm $?" not in message


def test_formatter_error_marker_is_diagnostic_only() -> None:
    message = status.format_telegram_summary(
        "[TIMEOUT after 15s]",
        "2026-09-07T23:00 UTC",
    )

    assert "PM position check failed: positions script error" in message
    assert "PM cost" not in message


def test_actual_positions_producer_output_reaches_status_formatter(
    monkeypatch, capsys
) -> None:
    class FakeResponse:
        def __init__(self, payload):
            self.payload = payload

        def json(self):
            return self.payload

        def raise_for_status(self):
            return None

    position = {
        "outcome": "YES",
        "avgPrice": 0.4,
        "curPrice": 0.8,
        "size": 20.0,
        "initialValue": 8.0,
        "currentValue": 16.0,
        "percentPnl": 100.0,
        "redeemable": False,
        "slug": "producer-consumer-drift",
        "title": "Producer output contract",
    }
    market = {
        "clobTokenIds": '["token-yes"]',
        "outcomes": '["YES"]',
        "feesEnabled": False,
    }
    book = {"bids": [{"price": "0.5", "size": "20"}]}

    class FakeClient:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def get(self, url, **kwargs):
            if url.endswith("/positions"):
                return FakeResponse([position])
            if "gamma-api.polymarket.com" in url:
                return FakeResponse([market])
            if "clob.polymarket.com" in url:
                return FakeResponse(book)
            raise AssertionError(f"unexpected URL: {url}")

    monkeypatch.setattr(
        positions.Wallet,
        "load",
        staticmethod(lambda: SimpleNamespace(address="0x1234")),
    )
    monkeypatch.setattr(positions.httpx, "Client", lambda *args, **kwargs: FakeClient())

    positions.main()
    producer_output = capsys.readouterr().out
    assert "REALIZABLE (depth-walked, NET of taker fees): $10.00" in producer_output

    message = status.format_telegram_summary(producer_output, "2026-09-07T23:00 UTC")
    assert "realizable $10.00 (depth-walked, NET of taker fees)" in message
    assert "best bids" not in message


def test_summary_parser_ignores_spoofed_totals_inside_market_text() -> None:
    output = (
        "market title: OPEN TOTAL cost $1.00 mtm $2.00\n"
        "market note: REALIZABLE (depth-walked, NET of taker fees): $3.00\n"
        "OPEN TOTAL  cost $10.00  mtm $12.00  max-payout $15.00\n"
        "REALIZABLE (depth-walked, NET of taker fees): $11.50  (+15.00%)\n"
    )

    message = status.format_telegram_summary(output, "2026-09-07T23:00 UTC")

    assert "PM cost $10.00 mtm $12.00" in message
    assert "realizable $11.50 (depth-walked, NET of taker fees)" in message
    assert "$1.00" not in message
    assert "$3.00" not in message


def test_summary_parser_does_not_invent_status_from_embedded_market_text() -> None:
    output = (
        "market title: (no open positions)\n"
        "market note: (realizable check unavailable: fake error)\n"
    )

    message = status.format_telegram_summary(output, "2026-09-07T23:00 UTC")

    assert "PM cost/mtm unavailable" in message
    assert "PM positions: no open positions" not in message
    assert "fake error" not in message


def _run_main_with_telegram(
    monkeypatch,
    tmp_path: Path,
    positions_result,
) -> tuple[int, list[str]]:
    sent_messages: list[str] = []

    monkeypatch.setattr(status, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(status, "run_script", lambda *args, **kwargs: "(ok)")
    monkeypatch.setattr(status.sys, "argv", ["polyclaude_status.py", "--quick", "--telegram"])

    def fake_run(cmd, **kwargs):
        if any("telegram.py" in part for part in cmd):
            sent_messages.append(cmd[-1])
            return SimpleNamespace(returncode=0)
        if any("positions.py" in part for part in cmd):
            if isinstance(positions_result, BaseException):
                raise positions_result
            return positions_result
        raise AssertionError(f"unexpected subprocess: {cmd}")

    monkeypatch.setattr(status.subprocess, "run", fake_run)
    return status.main(), sent_messages


def test_main_telegram_delivers_current_net_depth_summary(
    monkeypatch, tmp_path: Path
) -> None:
    result = SimpleNamespace(returncode=0, stdout=CURRENT_POSITIONS_OUTPUT, stderr="")

    exit_code, sent = _run_main_with_telegram(monkeypatch, tmp_path, result)

    assert exit_code == 0
    assert len(sent) == 1
    assert "realizable $46.81 (depth-walked, NET of taker fees)" in sent[0]


def test_main_delivers_diagnostic_but_fails_on_positions_error(
    monkeypatch, tmp_path: Path
) -> None:
    result = SimpleNamespace(
        returncode=3,
        stdout="OPEN TOTAL  cost $10.00  mtm $10.25",
        stderr="private implementation detail",
    )

    exit_code, sent = _run_main_with_telegram(monkeypatch, tmp_path, result)

    assert exit_code != 0
    assert len(sent) == 1
    assert "realizable unavailable (positions check failed)" in sent[0]
    assert "PM cost" not in sent[0]
    assert "private implementation detail" not in sent[0]


def test_main_delivers_timeout_diagnostic_and_fails(
    monkeypatch, tmp_path: Path
) -> None:
    timeout = subprocess.TimeoutExpired("positions.py", 15)

    exit_code, sent = _run_main_with_telegram(monkeypatch, tmp_path, timeout)

    assert exit_code != 0
    assert len(sent) == 1
    assert "realizable unavailable (positions check failed)" in sent[0]
    assert "PM cost" not in sent[0]


def test_main_reports_sender_failure_and_fails(
    monkeypatch, tmp_path: Path, capsys
) -> None:
    result = SimpleNamespace(returncode=0, stdout=CURRENT_POSITIONS_OUTPUT, stderr="")
    monkeypatch.setattr(status, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(status, "run_script", lambda *args, **kwargs: "(ok)")
    monkeypatch.setattr(status.sys, "argv", ["polyclaude_status.py", "--quick", "--telegram"])

    def fake_run(cmd, **kwargs):
        if any("positions.py" in part for part in cmd):
            return result
        if any("telegram.py" in part for part in cmd):
            return SimpleNamespace(returncode=9)
        raise AssertionError(f"unexpected subprocess: {cmd}")

    monkeypatch.setattr(status.subprocess, "run", fake_run)

    assert status.main() != 0
    captured = capsys.readouterr().out
    assert "Telegram send failed: exit 9" in captured
    assert "Telegram summary sent" not in captured


def test_telegram_sender_nonzero_is_not_reported_as_success(monkeypatch) -> None:
    def failed_run(*args, **kwargs):
        return SimpleNamespace(returncode=7)

    monkeypatch.setattr(status.subprocess, "run", failed_run)

    sent, detail = status.send_telegram_message("test")

    assert sent is False
    assert detail == "exit 7"
