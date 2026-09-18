"""Tests for ScoreService."""

from services.score_service import ScoreService


def _gap(matched: list[str], missing: list[str]) -> dict:
    return {"matched": matched, "missing": missing, "priority": missing[:]}


def test_perfect_score() -> None:
    """All skills matched + interview avg 10 → total 100."""
    service = ScoreService()
    gap = _gap(
        matched=["python", "sql", "docker", "git", "rest api"],
        missing=[],
    )
    interview_results = [{"score": 10}] * 5
    result = service.calculate(gap, interview_results)

    assert result["total"] == 100
    assert result["breakdown"]["skill_match"] == 50
    assert result["breakdown"]["interview"] == 50


def test_zero_score() -> None:
    """No skills matched + no interview results → total 0."""
    service = ScoreService()
    gap = _gap(matched=[], missing=["python", "sql", "docker"])
    result = service.calculate(gap, interview_results=[])

    assert result["total"] == 0
    assert result["breakdown"]["skill_match"] == 0
    assert result["breakdown"]["interview"] == 0


def test_partial_score() -> None:
    """2 out of 4 skills matched + interview avg 5 → ~50 total."""
    service = ScoreService()
    gap = _gap(matched=["python", "sql"], missing=["docker", "git"])
    interview_results = [{"score": 5}] * 4
    result = service.calculate(gap, interview_results)

    # skill_match: 2/4 * 50 = 25
    assert result["breakdown"]["skill_match"] == 25
    # interview: avg=5, 5/10 * 50 = 25
    assert result["breakdown"]["interview"] == 25
    assert result["total"] == 50
