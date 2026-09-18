"""Tests for SkillService."""

from unittest.mock import MagicMock

import pytest

from services.skill_service import SkillService


def _make_service(extract_return: list[str]) -> tuple[SkillService, MagicMock]:
    """Helper: returns a SkillService with a mocked BobClient."""
    mock_bob = MagicMock()
    mock_bob.extract_skills.return_value = extract_return
    service = SkillService(bob=mock_bob)
    return service, mock_bob


def test_extract_from_text_calls_bob() -> None:
    """extract_from_text must delegate to BobClient.extract_skills."""
    service, mock_bob = _make_service(["Python", "SQL"])
    result = service.extract_from_text("I know Python and SQL")
    mock_bob.extract_skills.assert_called_once_with("I know Python and SQL")
    assert "python" in result
    assert "sql" in result


def test_normalize_lowercases_and_deduplicates() -> None:
    """normalize must lowercase, strip, and deduplicate."""
    service, _ = _make_service([])
    raw = ["Python", "python", "SQL ", " SQL", "Docker"]
    result = service.normalize(raw)
    assert result == sorted({"python", "sql", "docker"})
    assert len(result) == 3
