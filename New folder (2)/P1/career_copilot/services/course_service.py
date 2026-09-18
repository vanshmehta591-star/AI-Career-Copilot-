"""IBM SkillsBuild course recommendations mapped to skills."""

SKILLSBUILD_COURSES: dict[str, dict] = {
    "python": {"title": "Python for Data Science", "url": "https://skills.ibm.com/", "duration": "6h"},
    "machine learning": {"title": "Machine Learning with Python", "url": "https://skills.ibm.com/", "duration": "8h"},
    "deep learning": {"title": "Deep Learning Fundamentals", "url": "https://skills.ibm.com/", "duration": "10h"},
    "sql": {"title": "SQL and Relational Databases", "url": "https://skills.ibm.com/", "duration": "4h"},
    "docker": {"title": "Docker Essentials", "url": "https://skills.ibm.com/", "duration": "3h"},
    "kubernetes": {"title": "Kubernetes & Container Orchestration", "url": "https://skills.ibm.com/", "duration": "5h"},
    "react": {"title": "React Basics", "url": "https://skills.ibm.com/", "duration": "5h"},
    "javascript": {"title": "JavaScript Essentials", "url": "https://skills.ibm.com/", "duration": "6h"},
    "typescript": {"title": "TypeScript for Developers", "url": "https://skills.ibm.com/", "duration": "4h"},
    "node.js": {"title": "Node.js Application Development", "url": "https://skills.ibm.com/", "duration": "5h"},
    "git": {"title": "Git and GitHub Fundamentals", "url": "https://skills.ibm.com/", "duration": "2h"},
    "linux": {"title": "Linux Commands & Shell Scripting", "url": "https://skills.ibm.com/", "duration": "4h"},
    "statistics": {"title": "Statistics for Data Science", "url": "https://skills.ibm.com/", "duration": "5h"},
    "data visualization": {"title": "Data Visualization with Python", "url": "https://skills.ibm.com/", "duration": "4h"},
    "ci/cd": {"title": "CI/CD with Jenkins", "url": "https://skills.ibm.com/", "duration": "4h"},
    "terraform": {"title": "Infrastructure as Code with Terraform", "url": "https://skills.ibm.com/", "duration": "6h"},
    "css": {"title": "CSS for Web Developers", "url": "https://skills.ibm.com/", "duration": "3h"},
    "html": {"title": "HTML5 & Web Fundamentals", "url": "https://skills.ibm.com/", "duration": "2h"},
    "rest api": {"title": "REST API Design", "url": "https://skills.ibm.com/", "duration": "3h"},
    "neural networks": {"title": "Neural Networks and Deep Learning", "url": "https://skills.ibm.com/", "duration": "8h"},
}


class CourseService:
    """Recommend IBM SkillsBuild courses for a list of missing skills."""

    def recommend(self, missing_skills: list[str]) -> list[dict]:
        """Return course entries for each skill in *missing_skills* that has a match.

        Parameters
        ----------
        missing_skills:
            Lowercased skill names that the user still needs to acquire.

        Returns
        -------
        list[dict]
            Each entry has keys: ``skill``, ``title``, ``url``, ``duration``.
        """
        recommendations: list[dict] = []
        for skill in missing_skills:
            key = skill.lower().strip()
            course = SKILLSBUILD_COURSES.get(key)
            if course:
                recommendations.append(
                    {
                        "skill": skill,
                        "title": course["title"],
                        "url": course["url"],
                        "duration": course["duration"],
                    }
                )
        return recommendations
