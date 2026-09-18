"""Mock interview question generation and answer evaluation service."""

from services.bob_client import BobClient


class InterviewService:
    """Generate interview questions and evaluate user answers via Bob AI."""

    def __init__(self, bob: BobClient) -> None:
        self._bob = bob

    def generate_questions(self, career: str, skills: list[str]) -> list[str]:
        """Generate 5 mock interview questions for *career* and *skills*.

        Parameters
        ----------
        career:
            Target career path name.
        skills:
            Skills to focus questions on (typically missing skills).

        Returns
        -------
        list[str]
            List of interview question strings.
        """
        return self._bob.generate_questions(career, skills)

    def evaluate_answer(self, question: str, answer: str) -> dict:
        """Evaluate a user's *answer* to *question*.

        Parameters
        ----------
        question:
            The interview question that was asked.
        answer:
            The user's free-text answer.

        Returns
        -------
        dict
            ``{"score": int (0-10), "feedback": str, "suggestion": str}``
        """
        return self._bob.evaluate_answer(question, answer)
