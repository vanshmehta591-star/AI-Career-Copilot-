"""Job Readiness Score calculation service."""


class ScoreService:
    """Calculate a Job Readiness Score out of 100.

    Weights
    -------
    - Skill match  : 50 points
    - Interview avg: 50 points
    """

    _SKILL_WEIGHT: int = 50
    _INTERVIEW_WEIGHT: int = 50

    def calculate(self, gap: dict, interview_results: list[dict]) -> dict:
        """Compute the overall readiness score and its breakdown.

        Parameters
        ----------
        gap:
            Output of ``CareerService.skill_gap()``.
            Expected keys: ``matched`` (list), ``missing`` (list).
        interview_results:
            List of ``BobClient.evaluate_answer()`` dicts, each with a
            ``"score"`` key (int 0-10).

        Returns
        -------
        dict
            ``{"total": int, "breakdown": {"skill_match": int, "interview": int}}``
        """
        skill_match_pts = self._calc_skill_match(gap)
        interview_pts = self._calc_interview(interview_results)
        total = skill_match_pts + interview_pts

        return {
            "total": total,
            "breakdown": {
                "skill_match": skill_match_pts,
                "interview": interview_pts,
            },
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _calc_skill_match(self, gap: dict) -> int:
        matched: list = gap.get("matched", [])
        missing: list = gap.get("missing", [])
        total_skills = len(matched) + len(missing)
        if total_skills == 0:
            return 0
        ratio = len(matched) / total_skills
        return round(ratio * self._SKILL_WEIGHT)

    def _calc_interview(self, interview_results: list[dict]) -> int:
        if not interview_results:
            return 0
        scores = [r.get("score", 0) for r in interview_results]
        avg = sum(scores) / len(scores)
        # avg is 0-10; scale to INTERVIEW_WEIGHT
        ratio = avg / 10.0
        return round(ratio * self._INTERVIEW_WEIGHT)
