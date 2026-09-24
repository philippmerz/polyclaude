from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import opportunity_watch as watch  # noqa: E402


def test_monotonicity_batch_snapshot_dispatches_revalidation(monkeypatch):
    output = (
        "# 3 events; 1 midpoint violation; 1 PROVISIONAL after batched CLOB walk; "
        "REVALIDATION REQUIRED\n"
        "Treasury bar>=4.5 bar>=4.4 +5.00pp +3.25pp PROVISIONAL ARB\n"
    )
    monkeypatch.setattr(
        watch.subprocess, "run",
        lambda *_args, **_kwargs: SimpleNamespace(stdout=output, stderr="", returncode=0),
    )
    alerts = []
    monkeypatch.setattr(
        watch, "_alert",
        lambda _state, key, text, **kwargs: alerts.append((key, text, kwargs)) or True,
    )

    watch.run_monotonicity({})

    assert len(alerts) == 1
    assert alerts[0][0] == "monotonicity-arb"
    assert "REVALIDATION candidate" in alerts[0][1]
    assert "Freshly rewalk both legs" in alerts[0][1]


def test_pair_batch_snapshot_dispatches_revalidation(monkeypatch, tmp_path):
    triggers = tmp_path / "triggers.json"
    triggers.write_text(json.dumps([{
        "key": "pair", "kind": "pair_arb", "mode": "implies",
        "a": "a", "b": "b", "note": "test",
    }]))
    output = (
        "# 1 mid violation(s); 1 provisional after batched live-CLOB walk + fees "
        "(floor 2.0pp); REVALIDATION REQUIRED\n"
    )
    monkeypatch.setattr(watch, "TRIGGERS_PATH", triggers)
    monkeypatch.setattr(
        watch.subprocess, "run",
        lambda *_args, **_kwargs: SimpleNamespace(stdout=output, stderr="", returncode=0),
    )
    alerts = []
    monkeypatch.setattr(
        watch, "_alert",
        lambda _state, key, text, actionable: alerts.append((key, text, actionable)) or True,
    )

    watch.run_pair_arb({})

    assert alerts == [(
        "pair",
        "pair-arb REVALIDATION candidate after a non-atomic batched book snapshot + fees: "
        "pair. Freshly rewalk both legs before any action. test",
        True,
    )]
