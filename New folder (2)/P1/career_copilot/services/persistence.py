"""Simple JSON-based persistence for student profiles, reports and interviews."""

import json
import os
from typing import Optional


class Persistence:
    """Read and write student data to JSON files in a local directory."""

    def __init__(self, data_dir: str = "data") -> None:
        self._data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _path(self, username: str, kind: str) -> str:
        safe = username.replace("/", "_").replace("\\", "_")
        return os.path.join(self._data_dir, f"{safe}_{kind}.json")

    def _write(self, path: str, data: object) -> None:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2)

    def _read(self, path: str) -> Optional[object]:
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def save_profile(self, username: str, data: dict) -> None:
        """Persist a student profile dictionary."""
        self._write(self._path(username, "profile"), data)

    def load_profile(self, username: str) -> Optional[dict]:
        """Load a student profile, or ``None`` if it does not exist."""
        result = self._read(self._path(username, "profile"))
        return result if isinstance(result, dict) else None

    def save_report(self, username: str, report: dict) -> None:
        """Persist a skill-gap report dictionary."""
        self._write(self._path(username, "report"), report)

    def load_report(self, username: str) -> Optional[dict]:
        """Load a skill-gap report, or ``None`` if it does not exist."""
        result = self._read(self._path(username, "report"))
        return result if isinstance(result, dict) else None

    def save_interview(self, username: str, history: list[dict]) -> None:
        """Persist interview history (list of answer-evaluation dicts)."""
        self._write(self._path(username, "interview"), history)

    def load_interview(self, username: str) -> list[dict]:
        """Load interview history, or an empty list if none exists."""
        result = self._read(self._path(username, "interview"))
        return result if isinstance(result, list) else []
