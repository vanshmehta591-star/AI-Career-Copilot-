"""Tests for InterviewService."""

from unittest.mock import MagicMock

from services.interview_service import InterviewService


def _make_service() -> tuple[InterviewService, MagicMock]:
    mock_bob = MagicMock()
    service = InterviewService(bob=mock_bob)
    return service, mock_bob


def test_generate_questions_calls_bob() -> None:
    """generate_questions must delegate to BobClient.generate_questions."""
    service, mock_bob = _make_service()
    mock_bob.generate_questions.return_value = ["Q1?", "Q2?", "Q3?"]

    result = service.generate_questions("Data Scientist", ["python", "sql"])

    mock_bob.generate_questions.assert_called_once_with(
        "Data Scientist", ["python", "sql"]
    )
    assert result == ["Q1?", "Q2?", "Q3?"]


def test_evaluate_answer_calls_bob() -> None:
    """evaluate_answer must delegate to BobClient.evaluate_answer."""
    service, mock_bob = _make_service()
    expected = {"score": 8, "feedback": "Good answer.", "suggestion": "Add examples."}
    mock_bob.evaluate_answer.return_value = expected

    result = service.evaluate_answer("Tell me about Python.", "Python is great.")

    mock_bob.evaluate_answer.assert_called_once_with(
        "Tell me about Python.", "Python is great."
    )
    assert result == expected
