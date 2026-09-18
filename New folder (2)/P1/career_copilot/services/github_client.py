"""GitHub client — fetches languages and topics from a user's public repos."""

import os
from typing import Optional

import requests
from dotenv import load_dotenv

load_dotenv()


class GitHubClient:
    """Retrieve skills (languages + repo topics) for a GitHub username."""

    _BASE = "https://api.github.com"

    def __init__(self) -> None:
        token: Optional[str] = os.getenv("GITHUB_TOKEN")
        self._headers: dict[str, str] = {"Accept": "application/vnd.github+json"}
        if token:
            self._headers["Authorization"] = f"Bearer {token}"

    def fetch_skills(self, username: str) -> list[str]:
        """Return language names and repo topics for *username*.

        Returns an empty list if the user is not found (404).

        Raises
        ------
        RuntimeError
            On unexpected HTTP errors (non-404).
        """
        username = username.strip()
        repos = self._get_repos(username)
        skills: set[str] = set()

        for repo in repos:
            # Primary language
            lang: Optional[str] = repo.get("language")
            if lang:
                skills.add(lang.lower())

            # Repo topics
            repo_name: str = repo.get("name", "")
            topics = self._get_topics(username, repo_name)
            for topic in topics:
                skills.add(topic.lower())

        return sorted(skills)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_repos(self, username: str) -> list[dict]:
        url = f"{self._BASE}/users/{username}/repos"
        params: dict[str, int] = {"per_page": 100}
        response = requests.get(url, headers=self._headers, params=params, timeout=10)
        if response.status_code == 404:
            return []
        if not response.ok:
            raise RuntimeError(
                f"GitHub API error: HTTP {response.status_code} — {response.text}"
            )
        return response.json()  # type: ignore[return-value]

    def _get_topics(self, username: str, repo_name: str) -> list[str]:
        url = f"{self._BASE}/repos/{username}/{repo_name}/topics"
        headers = {**self._headers, "Accept": "application/vnd.github.mercy-preview+json"}
        response = requests.get(url, headers=headers, timeout=10)
        if not response.ok:
            return []
        return response.json().get("names", [])  # type: ignore[return-value]
