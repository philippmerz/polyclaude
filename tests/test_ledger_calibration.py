"""Calibration tests with mocked network and writes confined to temporary ledgers."""

from __future__ import annotations

import errno
import json
from argparse import Namespace
from pathlib import Path

import httpx
import pytest

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts import ledger_calibration as lc


@pytest.fixture(autouse=True)
def isolate_side_effects(monkeypatch, tmp_path):
    """Every test writes only inside its own directory and cannot use the network."""
    production_ledger = lc.LEDGER
    original = production_ledger.read_bytes()
    temporary_ledger = tmp_path / "ledger.json"
    temporary_ledger.write_text("[]\n")
    monkeypatch.setattr(lc, "LEDGER", temporary_ledger)
    actual_write = lc._write_document

    def confined_write(document):
        assert lc.LEDGER.resolve().is_relative_to(tmp_path.resolve())
        actual_write(document)

    def no_network(*args, **kwargs):
        raise AssertionError("calibration tests must mock all network requests")

    monkeypatch.setattr(lc, "_write_document", confined_write)
    monkeypatch.setattr(httpx.Client, "send", no_network)
    yield
    assert production_ledger.read_bytes() == original


class Response:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


def row(**extra):
    base = {"question": "q", "side": "YES", "ask": 0.4,
            "catalyst_p_yes_central": 0.7, "outcome": None,
            "slug": "exact-slug"}
    base.update(extra)
    return base


def market(**extra):
    base = {"id": "123", "slug": "exact-slug", "conditionId": "0xabc",
            "closed": True, "umaResolutionStatus": "resolved",
            "outcomes": '["Yes", "No"]', "outcomePrices": '["1", "0"]'}
    base.update(extra)
    return base


def test_resolve_swapped_labels_and_exact_slug(monkeypatch):
    calls = []

    def get(url, **kwargs):
        calls.append((url, kwargs))
        return Response([market(outcomes='["No", "Yes"]', outcomePrices='["0", "1"]')])

    monkeypatch.setattr(lc.httpx, "get", get)
    rec = row()
    monkeypatch.setattr(lc, "_load_document", lambda: ([rec], [rec]))
    assert lc.cmd_resolve(Namespace(dry_run=False)) == 0
    assert rec["outcome"] == "YES"
    assert calls[0][0] == lc.GAMMA + "/slug/exact-slug"


def test_numeric_id_and_condition_mismatch(monkeypatch):
    seen = []

    def get(url, **kwargs):
        seen.append(url)
        return Response(market())

    monkeypatch.setattr(lc.httpx, "get", get)
    rec = row(slug=None, market_id=123, condition_id="0xother")
    monkeypatch.setattr(lc, "_load_document", lambda: ([rec], [rec]))
    lc.cmd_resolve(Namespace(dry_run=False))
    assert rec["outcome"] is None
    assert seen == [lc.GAMMA + "/123"]


def test_conflicting_ids_bool_and_nan_are_ungraded(monkeypatch):
    recs = [
        row(slug=None, market_id=123, marketId=124),
        row(slug=None, market_id=True),
        row(slug=None, market_id=float("nan")),
    ]
    monkeypatch.setattr(lc, "_load_document", lambda: (recs, recs))
    monkeypatch.setattr(lc.httpx, "get", lambda *a, **k: pytest.fail("malformed IDs must not fetch"))
    lc.cmd_resolve(Namespace(dry_run=True))
    assert all(r.get("outcome") is None for r in recs)


def test_requires_closed_and_uma_resolved_and_binary_final(monkeypatch):
    recs = [row(slug="open"), row(slug="pending"), row(slug="nonbinary")]

    def get(url, **kwargs):
        slug = url.rsplit("/", 1)[-1]
        if slug == "open":
            return Response([market(slug=slug, closed=False)])
        if slug == "pending":
            return Response([market(slug=slug, umaResolutionStatus="pending")])
        return Response([market(slug=slug, outcomes='["Yes", "Maybe"]')])

    monkeypatch.setattr(lc.httpx, "get", get)
    monkeypatch.setattr(lc, "_load_document", lambda: (recs, recs))
    lc.cmd_resolve(Namespace(dry_run=False))
    assert [r["outcome"] for r in recs] == [None, None, None]


@pytest.mark.parametrize("changes", [
    {"closed": 1}, {"closed": "true"},
    {"umaResolutionStatus": None}, {"umaResolutionStatus": "proposed"},
    {"umaResolutionStatus": "disputed"},
    {"outcomes": ["Yes", "Yes"]}, {"outcomes": ["Yes"]},
    {"outcomePrices": [True, False]},
    {"outcomePrices": [1, 1]}, {"outcomePrices": [0, 0]},
    {"outcomePrices": [0.9995, 0.0005]},
    {"outcomePrices": [float("nan"), 0]},
    {"outcomePrices": [float("inf"), 0]},
    {"outcomePrices": [10**1000, 0]},
    {"outcomePrices": "not-json"},
])
def test_false_or_malformed_finality_never_grades(changes):
    assert lc._final_outcome(market(**changes))[0] is None


@pytest.mark.parametrize("changes", [
    {"id": "124"}, {"slug": "same-date-different-market"},
    {"conditionId": "0xdef"},
])
def test_every_stored_identity_must_match(monkeypatch, changes):
    monkeypatch.setattr(lc.httpx, "get", lambda *a, **k: Response(market(**changes)))
    result, status = lc._market_for_record(row(market_id="123", condition_id="0xabc"))
    assert result is None and status == "identity_mismatch"


def test_title_only_pending_and_existing_outcome_are_untouched(monkeypatch):
    title_only = row(slug=None)
    title_only.pop("slug")
    pending = row(outcome="PENDING-NO")
    existing = row(outcome="NO")
    monkeypatch.setattr(lc, "_load_document", lambda: ([title_only, pending, existing],
                                                          [title_only, pending, existing]))
    def fail(*args, **kwargs):
        raise AssertionError("title-only row must not trigger public search")
    monkeypatch.setattr(lc.httpx, "get", fail)
    lc.cmd_resolve(Namespace(dry_run=False))
    assert title_only.get("outcome") is None
    assert pending["outcome"] == "PENDING-NO"
    assert existing["outcome"] == "NO"


def test_score_pending_excluded_and_missing_baseline_keeps_own_cohort():
    result = lc._score_records([
        row(outcome="PENDING-NO"),
        row(outcome="YES", ask=None),
        row(outcome="NO", catalyst_p_yes_central=True),
    ])
    assert len(result["own"]) == 1
    assert len(result["matched"]) == 0
    assert result["counts"]["pending"] == 1
    assert result["counts"]["missing_or_bad_market_baseline"] == 1


def test_bad_numbers_are_rejected_and_valid_own_forecast_scores():
    result = lc._score_records([
        row(outcome="YES", catalyst_p_yes_central=True),
        row(outcome="YES", catalyst_p_yes_central=float("nan")),
        row(outcome="YES", ask=True),
        row(outcome="YES", ask=1.2),
    ])
    assert len(result["own"]) == 2
    assert len(result["matched"]) == 0
    assert result["counts"]["missing_or_bad_forecast"] == 2


def test_dry_run_and_fetch_failure_do_not_write(monkeypatch, tmp_path: Path):
    path = tmp_path / "ledger.json"
    original = {"records": [row()], "metadata": {"keep": "exact"}, "other": [1, 2]}
    path.write_text(json.dumps(original) + "\n")
    monkeypatch.setattr(lc, "LEDGER", path)
    monkeypatch.setattr(lc, "_market_for_record",
                        lambda rec: (_ for _ in ()).throw(httpx.RequestError("offline")))
    lc.cmd_resolve(Namespace(dry_run=True))
    assert json.loads(path.read_text()) == original


def test_successful_dry_run_does_not_write(monkeypatch, tmp_path: Path):
    path = tmp_path / "ledger.json"
    original = {"records": [row()], "metadata": {"keep": "exact"}}
    path.write_text(json.dumps(original) + "\n")
    monkeypatch.setattr(lc, "LEDGER", path)
    monkeypatch.setattr(lc.httpx, "get", lambda *a, **k: Response([market()]))
    lc.cmd_resolve(Namespace(dry_run=True))
    assert json.loads(path.read_text()) == original


def test_matched_market_metrics_are_subset_of_full_own_cohort():
    result = lc._score_records([
        row(outcome="YES", catalyst_p_yes_central=0.8, ask=0.4),
        row(outcome="NO", catalyst_p_yes_central=0.2, ask=None),
    ])
    assert len(result["own"]) == 2
    assert len(result["matched"]) == 1
    assert result["matched"][0]["mkt_p"] == 0.4


def test_score_table_and_comparison_keep_observed_baselines(monkeypatch, capsys):
    recs = [
        row(question="quoted", outcome="YES", catalyst_p_yes_central=0.8, ask=0.4),
        row(question="unquoted", outcome="NO", catalyst_p_yes_central=0.9, ask=None),
    ]
    monkeypatch.setattr(lc, "_load_document", lambda: (recs, recs))
    lc.cmd_score(Namespace())
    output = capsys.readouterr().out
    lines = output.splitlines()
    quoted = next(line for line in lines if line.endswith("  quoted"))
    unquoted = next(line for line in lines if line.endswith("  unquoted"))
    assert "0.40" in quoted and "n/a" not in quoted
    assert "n/a" in unquoted
    assert "Own cohort N=2; market-matched subset N=1" in output
    assert "Own Brier 0.4250" in output
    assert "Brier mine 0.0400 vs market 0.3600" in output


def test_envelope_shape_and_unrelated_fields_preserved_on_write(monkeypatch, tmp_path: Path):
    path = tmp_path / "ledger.json"
    original = {"records": [row()], "metadata": {"keep": True}}
    path.write_text(json.dumps(original))
    monkeypatch.setattr(lc, "LEDGER", path)
    monkeypatch.setattr(lc.httpx, "get", lambda *a, **k: Response([market()]))
    lc.cmd_resolve(Namespace(dry_run=False))
    written = json.loads(path.read_text())
    assert isinstance(written, dict)
    assert written["metadata"] == original["metadata"]
    assert written["records"][0]["outcome"] == "YES"


@pytest.mark.parametrize("document", [
    [row(outcome="YES")],
    {"records": [row(outcome="NO")], "metadata": {"keep": "exact"}},
])
def test_atomic_write_success_preserves_existing_mode_and_document_shape(
        monkeypatch, tmp_path: Path, document):
    path = tmp_path / "ledger.json"
    original_bytes = b'{"old": true}\n'
    path.write_bytes(original_bytes)
    path.chmod(0o640)
    monkeypatch.setattr(lc, "LEDGER", path)

    lc._write_document(document)

    assert json.loads(path.read_text()) == document
    assert path.stat().st_mode & 0o777 == 0o640
    assert original_bytes != path.read_bytes()
    assert list(tmp_path.iterdir()) == [path]


def test_atomic_write_new_ledger_is_private(monkeypatch, tmp_path: Path):
    path = tmp_path / "new-ledger.json"
    monkeypatch.setattr(lc, "LEDGER", path)

    lc._write_document([row(outcome="YES")])

    assert path.exists()
    assert path.stat().st_mode & 0o777 == 0o600
    assert {item.name for item in tmp_path.iterdir()} == {
        "ledger.json", "new-ledger.json"
    }


def test_atomic_write_serialization_failure_preserves_original(monkeypatch, tmp_path: Path):
    path = tmp_path / "ledger.json"
    original = b"unchanged\n"
    path.write_bytes(original)
    monkeypatch.setattr(lc, "LEDGER", path)

    def fail_serialization(*args, **kwargs):
        raise ValueError("serialization failed")

    monkeypatch.setattr(lc.json, "dumps", fail_serialization)
    with pytest.raises(ValueError, match="serialization failed"):
        lc._write_document([row()])

    assert path.read_bytes() == original
    assert list(tmp_path.iterdir()) == [path]


@pytest.mark.parametrize("failure_phase", ["write", "flush"])
def test_atomic_write_enospc_during_temp_write_preserves_original(
        monkeypatch, tmp_path: Path, failure_phase):
    path = tmp_path / "ledger.json"
    original = b"original bytes\n"
    path.write_bytes(original)
    monkeypatch.setattr(lc, "LEDGER", path)
    real_fdopen = lc.os.fdopen

    class FailingFile:
        def __init__(self, wrapped):
            self.wrapped = wrapped

        def __enter__(self):
            self.wrapped.__enter__()
            return self

        def __exit__(self, *exc_info):
            return self.wrapped.__exit__(*exc_info)

        def write(self, data):
            if failure_phase == "write":
                self.wrapped.write(data[:max(1, len(data) // 2)])
                self.wrapped.flush()
                raise OSError(errno.ENOSPC, "no space left on device")
            return self.wrapped.write(data)

        def flush(self):
            if failure_phase == "flush":
                raise OSError(errno.ENOSPC, "no space left on device")
            return self.wrapped.flush()

        def __getattr__(self, name):
            return getattr(self.wrapped, name)

    def fdopen(fd, *args, **kwargs):
        return FailingFile(real_fdopen(fd, *args, **kwargs))

    monkeypatch.setattr(lc.os, "fdopen", fdopen)
    with pytest.raises(OSError) as exc_info:
        lc._write_document([row(outcome="YES")])

    assert exc_info.value.errno == errno.ENOSPC
    assert path.read_bytes() == original
    assert list(tmp_path.iterdir()) == [path]


def test_atomic_write_fsync_failure_preserves_original(monkeypatch, tmp_path: Path):
    path = tmp_path / "ledger.json"
    original = b"original bytes\n"
    path.write_bytes(original)
    monkeypatch.setattr(lc, "LEDGER", path)

    def fail_fsync(fd):
        raise OSError(errno.EIO, "fsync failed")

    monkeypatch.setattr(lc.os, "fsync", fail_fsync)
    with pytest.raises(OSError, match="fsync failed"):
        lc._write_document([row(outcome="YES")])

    assert path.read_bytes() == original
    assert list(tmp_path.iterdir()) == [path]


def test_atomic_write_replace_failure_preserves_original(monkeypatch, tmp_path: Path):
    path = tmp_path / "ledger.json"
    original = b"original bytes\n"
    path.write_bytes(original)
    monkeypatch.setattr(lc, "LEDGER", path)

    def fail_replace(source, destination):
        assert destination == path
        raise OSError(errno.EIO, "replace failed")

    monkeypatch.setattr(lc.os, "replace", fail_replace)
    with pytest.raises(OSError, match="replace failed"):
        lc._write_document([row(outcome="YES")])

    assert path.read_bytes() == original
    assert list(tmp_path.iterdir()) == [path]
