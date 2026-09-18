"""Skill extraction and normalization service."""

from services.bob_client import BobClient
from services.github_client import GitHubClient


class SkillService:
    """Extract and normalize technical skills from text or GitHub profiles."""

    def __init__(self, bob: BobClient) -> None:
        self._bob = bob
        self._github = GitHubClient()

    def extract_from_text(self, text: str) -> list[str]:
        """Extract skills from raw text using Bob AI.

        Parameters
        ----------
        text:
            Plain text of the resume or any free-form input.

        Returns
        -------
        list[str]
            Normalized list of skill strings.
        """
        raw_skills = self._bob.extract_skills(text)
        return self.normalize(raw_skills)

    def extract_from_github(self, username: str) -> list[str]:
        """Fetch and normalize skills from a GitHub user's public repos.

        Parameters
        ----------
        username:
            GitHub username.

        Returns
        -------
        list[str]
            Normalized list of skill strings.
        """
        raw_skills = self._github.fetch_skills(username)
        return self.normalize(raw_skills)

    def normalize(self, skills: list[str]) -> list[str]:
        """Lowercase, strip whitespace, and deduplicate *skills*.

        Parameters
        ----------
        skills:
            Raw skill strings (possibly mixed-case, with duplicates).

        Returns
        -------
        list[str]
            Sorted, deduplicated, lowercased skill strings.
        """
        seen: set[str] = set()
        result: list[str] = []
        for skill in skills:
            cleaned = skill.lower().strip()
            if cleaned and cleaned not in seen:
                seen.add(cleaned)
                result.append(cleaned)
        return sorted(result)
