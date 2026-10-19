"""Capital-path prompt regressions for catalyst_check."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import SimpleNamespace


SCRIPT = Path(__file__).parents[1] / "scripts" / "catalyst_check.py"
SPEC = importlib.util.spec_from_file_location("catalyst_check", SCRIPT)
assert SPEC and SPEC.loader
catalyst_check = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(catalyst_check)


def test_benchmark_prompt_requires_first_party_configuration_sweep() -> None:
    prompt = catalyst_check.PROMPT_TEMPLATE
    assert "ALREADY-EXISTING qualifying evidence" in prompt
    assert "official release notes / system card" in prompt
    assert "with tools" in prompt
    assert "no tools" in prompt
    assert "Never turn the" in prompt
    assert "maximum on one third-party tracker" in prompt
    assert "### Existing qualifying evidence" in prompt


def test_facts_mode_keeps_literal_rules_and_quarantines_feed_leads(monkeypatch, capsys) -> None:
    prompts = []
    rule = "Official Global Athletes list for the entire year; no list by March means No."
    monkeypatch.setattr(catalyst_check, "_fetch_resolution_description", lambda *a: rule)
    monkeypatch.setattr(catalyst_check, "_recent_alert_headlines", lambda *a: "- Unverified same-name headline")
    def worker(prompt, **kwargs):
        prompts.append(prompt)
        return SimpleNamespace(returncode=0, stdout="Source facts only", stderr="")
    monkeypatch.setattr(catalyst_check, "run_agent", worker)
    monkeypatch.setattr("sys.argv", [str(SCRIPT), "Exact question", "2099-12-31", "--facts-only", "--no-log", "--window-start", "2099-09-09"])
    assert catalyst_check.main() == 0
    prompt = prompts[0]
    assert rule in prompt
    assert "UNVERIFIED NEWS LEADS" in prompt
    assert "Do not estimate probabilities" in prompt
    assert "market creation alone does not truncate" in prompt
    assert "2099-09-09" in prompt
    assert "Exclude earlier events only when the literal criteria require" in prompt
    assert "An explicit annual ranking" in prompt
    assert "### P(YES) estimate" not in prompt
    assert "ground truth" not in prompt
    assert "Source facts only" in capsys.readouterr().out


def test_forecast_mode_also_does_not_promote_title_matches_to_verified_facts() -> None:
    block = catalyst_check._news_lead_block("- title only")
    assert "UNVERIFIED" in block
    assert "stale or unrelated" in block
    assert "ground truth" not in block
