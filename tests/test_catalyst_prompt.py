"""Capital-path prompt regressions for catalyst_check."""

from __future__ import annotations

import importlib.util
from pathlib import Path


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
