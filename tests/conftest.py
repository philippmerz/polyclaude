"""Shared test fixtures."""
import os
os.environ.setdefault("POLYCLAUDE_SUPERVISOR_GUARD", "0")

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import pytest


@pytest.fixture(autouse=True)
def isolate_bankroll_cache(monkeypatch, tmp_path):
    """Even reporting tests must never refresh the live sizing cache."""
    import bankroll
    monkeypatch.setattr(bankroll, 'BANKROLL_CACHE_PATH', tmp_path / 'bankroll-cache.json')
