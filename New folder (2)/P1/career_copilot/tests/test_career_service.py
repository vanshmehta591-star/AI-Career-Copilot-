"""Tests for CareerService."""

import pytest

from services.career_service import CareerService, CAREER_PATHS


def test_list_careers_returns_all_paths() -> None:
    """list_careers must return all keys from CAREER_PATHS."""
    service = CareerService()
    careers = service.list_careers()
    assert set(careers) == set(CAREER_PATHS.keys())
    assert len(careers) == len(CAREER_PATHS)


def test_skill_gap_correct_matched_and_missing() -> None:
    """skill_gap must correctly split user skills into matched and missing."""
    service = CareerService()
    # Data Scientist requires: python, machine learning, statistics, sql, data visualization
    user_skills = ["python", "sql"]
    gap = service.skill_gap("Data Scientist", user_skills)

    assert set(gap["matched"]) == {"python", "sql"}
    assert set(gap["missing"]) == {"machine learning", "statistics", "data visualization"}
    # priority should be a subset of missing
    assert set(gap["priority"]) == set(gap["missing"])


def test_skill_gap_unknown_career_raises() -> None:
    """skill_gap must raise ValueError for an unknown career path."""
    service = CareerService()
    with pytest.raises(ValueError, match="Unknown career path"):
        service.skill_gap("Astronaut", ["python"])
