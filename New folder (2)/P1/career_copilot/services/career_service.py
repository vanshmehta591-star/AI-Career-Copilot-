"""Career path definitions and skill-gap analysis."""

CAREER_PATHS: dict[str, list[str]] = {
    "Data Scientist": ["python", "machine learning", "statistics", "sql", "data visualization"],
    "Backend Developer": ["python", "sql", "rest api", "git", "docker"],
    "Frontend Developer": ["javascript", "react", "css", "html", "typescript"],
    "DevOps Engineer": ["docker", "kubernetes", "linux", "ci/cd", "terraform"],
    "ML Engineer": ["python", "machine learning", "deep learning", "neural networks", "docker"],
}


class CareerService:
    """Provide career path listings and skill-gap reports."""

    def list_careers(self) -> list[str]:
        """Return all available career path names.

        Returns
        -------
        list[str]
            Sorted list of career path names.
        """
        return sorted(CAREER_PATHS.keys())

    def skill_gap(self, career: str, user_skills: list[str]) -> dict:
        """Compute matched and missing skills for *career*.

        Parameters
        ----------
        career:
            One of the keys in CAREER_PATHS.
        user_skills:
            Normalized list of skills the user already has.

        Returns
        -------
        dict
            ``{"matched": list[str], "missing": list[str], "priority": list[str]}``
            where *priority* is the ordered list of missing skills most important
            to acquire (same order as CAREER_PATHS definition).

        Raises
        ------
        ValueError
            If *career* is not a known career path.
        """
        if career not in CAREER_PATHS:
            raise ValueError(
                f"Unknown career path: '{career}'. "
                f"Valid options: {', '.join(sorted(CAREER_PATHS.keys()))}"
            )

        required = CAREER_PATHS[career]
        user_lower = {s.lower().strip() for s in user_skills}

        matched = [s for s in required if s in user_lower]
        missing = [s for s in required if s not in user_lower]

        # Priority: missing skills in the original CAREER_PATHS order
        priority = missing[:]

        return {"matched": matched, "missing": missing, "priority": priority}
