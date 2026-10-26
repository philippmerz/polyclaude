from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"


def test_operator_start_does_not_launch_a_model():
    source = (SCRIPTS / "operator_start.sh").read_text(encoding="utf-8")

    assert "INITIAL_PROMPT" not in source
    assert "--initial-prompt" not in source
    assert "OPERATOR_READY" not in source
    assert "opencode" not in source
    assert "polyclaude-agent" not in source
    assert "prepare-blank" not in source
    assert "pc-attach" in source


def test_headless_fallback_onboards_from_agents():
    source = (SCRIPTS / "daily_checkin.sh").read_text(encoding="utf-8")

    assert (
        "Onboard first: read AGENTS.md, strategy/01_lessons.md, "
        "and strategy/02_operations.md"
    ) in source
