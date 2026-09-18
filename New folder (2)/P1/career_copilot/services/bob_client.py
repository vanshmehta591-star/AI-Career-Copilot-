"""IBM Bob API client — wraps all Bob REST calls behind one class."""

import json
import os

import requests
from dotenv import load_dotenv

load_dotenv()


class BobClient:
    """Single entry-point for all IBM Bob API interactions."""

    def __init__(self) -> None:
        api_key = os.getenv("BOB_API_KEY", "")
        if not api_key:
            raise EnvironmentError("BOB_API_KEY not set")
        self._api_key = api_key
        self._base_url = os.getenv(
            "BOB_BASE_URL", "https://api.ibm.com/watsonx/v1"
        ).rstrip("/")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _post(self, prompt: str) -> str:
        """Send a prompt to the Bob REST API and return the text response."""
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        payload = {"prompt": prompt}
        response = requests.post(
            f"{self._base_url}/generate",
            headers=headers,
            json=payload,
            timeout=30,
        )
        if not response.ok:
            raise RuntimeError(
                f"Bob API error: HTTP {response.status_code} — {response.text}"
            )
        data = response.json()
        # Expect {"result": "...text..."}  or  {"choices": [{"text": "..."}]}
        if "result" in data:
            return str(data["result"])
        if "choices" in data and data["choices"]:
            return str(data["choices"][0].get("text", ""))
        return str(data)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def extract_skills(self, text: str) -> list[str]:
        """Return a list of technical skills extracted from *text*."""
        prompt = (
            "Extract a list of technical skills from the following text. "
            "Return only a JSON array of lowercase skill name strings, e.g. "
            '["python", "sql"]. Text:\n\n' + text
        )
        raw = self._post(prompt)
        try:
            skills = json.loads(raw)
            if isinstance(skills, list):
                return [str(s) for s in skills]
        except json.JSONDecodeError:
            pass
        # Fallback: split comma-separated tokens
        return [s.strip().strip('"').lower() for s in raw.split(",") if s.strip()]

    def suggest_careers(self, skills: list[str]) -> list[str]:
        """Return a list of career-path suggestions for the given skills."""
        prompt = (
            "Given these technical skills: " + ", ".join(skills) + ". "
            "Suggest suitable career paths. Return only a JSON array of "
            'career name strings, e.g. ["Data Scientist", "ML Engineer"].'
        )
        raw = self._post(prompt)
        try:
            careers = json.loads(raw)
            if isinstance(careers, list):
                return [str(c) for c in careers]
        except json.JSONDecodeError:
            pass
        return [c.strip().strip('"') for c in raw.split(",") if c.strip()]

    def generate_questions(self, career: str, skills: list[str]) -> list[str]:
        """Return 5 mock interview questions for *career* focusing on *skills*."""
        prompt = (
            f"Generate exactly 5 mock interview questions for a '{career}' role. "
            "Focus on these skills: " + ", ".join(skills) + ". "
            "Return only a JSON array of question strings."
        )
        raw = self._post(prompt)
        try:
            questions = json.loads(raw)
            if isinstance(questions, list):
                return [str(q) for q in questions]
        except json.JSONDecodeError:
            pass
        return [q.strip() for q in raw.split("\n") if q.strip()]

    def evaluate_answer(self, question: str, answer: str) -> dict:
        """Evaluate an interview answer and return score + feedback."""
        prompt = (
            f"Question: {question}\nAnswer: {answer}\n\n"
            "Evaluate this interview answer. Return a JSON object with keys: "
            '"score" (int 0-10), "feedback" (str), "suggestion" (str).'
        )
        raw = self._post(prompt)
        try:
            result = json.loads(raw)
            if isinstance(result, dict):
                return {
                    "score": int(result.get("score", 5)),
                    "feedback": str(result.get("feedback", "")),
                    "suggestion": str(result.get("suggestion", "")),
                }
        except (json.JSONDecodeError, ValueError):
            pass
        return {"score": 5, "feedback": raw, "suggestion": ""}
