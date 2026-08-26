from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"


def test_operator_start_has_no_bootstrap_prompt_and_arms_gate():
    source = (SCRIPTS / "operator_start.sh").read_text(encoding="utf-8")

    assert "INITIAL_PROMPT" not in source
    assert "--initial-prompt" not in source
    assert "OPERATOR_READY" not in source
    assert "prepare-blank --workdir" in source
    assert "operator-live" in source
    assert "wait-ready" not in source


def test_headless_fallback_does_not_require_agents_file():
    source = (SCRIPTS / "daily_checkin.sh").read_text(encoding="utf-8")

    onboarding = source.partition("Onboard first, in this order:")[2].splitlines()[0]
    assert "AGENTS.md" not in onboarding
    assert "README.md" in onboarding
