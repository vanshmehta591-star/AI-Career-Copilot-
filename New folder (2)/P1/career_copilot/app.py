"""AI Career Copilot — Streamlit UI.

All business logic lives in the services package.
This file only wires the UI to service calls.
"""

import re
import sys
import os

import streamlit as st

# ---------------------------------------------------------------------------
# Make the services package importable when running from this directory
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.dirname(__file__))

from services.bob_client import BobClient
from services.resume_parser import ResumeParser
from services.skill_service import SkillService
from services.career_service import CareerService
from services.course_service import CourseService
from services.interview_service import InterviewService
from services.score_service import ScoreService
from services.persistence import Persistence

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="AI Career Copilot",
    page_icon="🎯",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Service initialisation (cached so they are created only once per session)
# ---------------------------------------------------------------------------

@st.cache_resource
def get_bob() -> BobClient | None:
    """Initialise BobClient once; return None and show a warning on error."""
    try:
        return BobClient()
    except EnvironmentError as exc:
        st.warning(f"⚠️ Bob AI unavailable: {exc}. Skill extraction will be limited.")
        return None


@st.cache_resource
def get_services() -> dict:
    bob = get_bob()

    # Provide a stub BobClient when the key is missing so the app still works
    class _StubBob:
        def extract_skills(self, text: str) -> list[str]:
            # Naive keyword scan as a fallback
            keywords = [
                "python", "java", "javascript", "sql", "docker", "kubernetes",
                "react", "git", "linux", "machine learning", "deep learning",
                "statistics", "typescript", "node.js", "terraform", "ci/cd",
                "rest api", "css", "html", "neural networks", "data visualization",
            ]
            return [kw for kw in keywords if kw in text.lower()]

        def suggest_careers(self, skills: list[str]) -> list[str]:
            return []

        def generate_questions(self, career: str, skills: list[str]) -> list[str]:
            return [
                f"What is your experience with {skills[i % len(skills)] if skills else career}?"
                for i in range(5)
            ]

        def evaluate_answer(self, question: str, answer: str) -> dict:
            score = min(10, max(1, len(answer.split()) // 5))
            return {
                "score": score,
                "feedback": "Answer received (Bob AI offline — stub evaluation).",
                "suggestion": "Connect Bob AI for detailed feedback.",
            }

    effective_bob: BobClient = bob if bob is not None else _StubBob()  # type: ignore[assignment]

    return {
        "skill_service": SkillService(bob=effective_bob),
        "career_service": CareerService(),
        "course_service": CourseService(),
        "interview_service": InterviewService(bob=effective_bob),
        "score_service": ScoreService(),
        "persistence": Persistence(data_dir="data"),
        "resume_parser": ResumeParser(),
    }


# ---------------------------------------------------------------------------
# Input validation helpers
# ---------------------------------------------------------------------------

_GITHUB_USERNAME_RE = re.compile(r"^[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,37}[a-zA-Z0-9])?$")


def _validate_github_username(username: str) -> str | None:
    """Return an error message string, or None if the username is valid."""
    username = username.strip()
    if not username:
        return None  # empty is OK — it's optional
    if not _GITHUB_USERNAME_RE.match(username):
        return (
            "GitHub username may only contain alphanumeric characters and hyphens, "
            "cannot start or end with a hyphen, and must be 1-39 characters."
        )
    return None


# ---------------------------------------------------------------------------
# Sidebar — student name
# ---------------------------------------------------------------------------

def _render_sidebar(persistence: Persistence) -> str:
    with st.sidebar:
        st.title("🎯 AI Career Copilot")
        st.markdown("---")
        username = st.text_input(
            "Your name / student ID",
            value=st.session_state.get("username", ""),
            placeholder="e.g. alice123",
        ).strip()

        if username:
            st.session_state["username"] = username
            profile = persistence.load_profile(username)
            if profile:
                st.success(f"Welcome back, **{username}**!")
            else:
                st.info(f"New profile: **{username}**")
                persistence.save_profile(username, {"name": username})
        else:
            st.session_state["username"] = ""
            st.warning("Enter your name to save progress.")

        st.markdown("---")
        st.caption("Powered by IBM Bob AI & IBM SkillsBuild")
    return username


# ---------------------------------------------------------------------------
# Tab 1 — Input
# ---------------------------------------------------------------------------

def _tab_input(services: dict, username: str) -> None:
    st.header("📄 Resume & Profile Input")

    col1, col2 = st.columns(2)

    with col1:
        uploaded = st.file_uploader(
            "Upload your resume (PDF or TXT, max 5 MB)",
            type=["pdf", "txt"],
        )

    with col2:
        github_username = st.text_input(
            "GitHub username (optional)",
            placeholder="e.g. torvalds",
        )

    if st.button("🔍 Analyse", type="primary"):
        _run_analysis(services, username, uploaded, github_username.strip())

    # Display previously extracted skills
    if "skills" in st.session_state and st.session_state["skills"]:
        st.markdown("### ✅ Extracted Skills")
        skills: list[str] = st.session_state["skills"]
        cols = st.columns(min(len(skills), 5))
        for i, skill in enumerate(skills):
            cols[i % len(cols)].markdown(
                f'<span style="background:#e8f4f8;border-radius:12px;'
                f'padding:4px 10px;font-size:0.85rem">{skill}</span>',
                unsafe_allow_html=True,
            )


def _run_analysis(
    services: dict,
    username: str,
    uploaded: object,
    github_username: str,
) -> None:
    """Validate inputs, extract skills, and store them in session state."""
    skill_service: SkillService = services["skill_service"]
    parser: ResumeParser = services["resume_parser"]
    persistence: Persistence = services["persistence"]

    all_skills: list[str] = []
    has_input = False

    # --- Resume ---
    if uploaded is not None:
        has_input = True
        try:
            file_bytes: bytes = uploaded.read()  # type: ignore[attr-defined]
            filename: str = uploaded.name  # type: ignore[attr-defined]
            text = parser.parse(file_bytes, filename)
            if not text.strip():
                st.error("The uploaded file appears to be empty. Please upload a resume with text content.")
                return
            resume_skills = skill_service.extract_from_text(text)
            all_skills.extend(resume_skills)
            st.success(f"Resume parsed — found {len(resume_skills)} skill(s).")
        except ValueError as exc:
            st.error(f"File error: {exc}")
            return
        except Exception as exc:
            st.error(f"Failed to process resume: {exc}")
            return

    # --- GitHub ---
    if github_username:
        err = _validate_github_username(github_username)
        if err:
            st.error(f"Invalid GitHub username: {err}")
            return
        has_input = True
        try:
            gh_skills = skill_service.extract_from_github(github_username)
            all_skills.extend(gh_skills)
            st.success(f"GitHub profile scanned — found {len(gh_skills)} skill(s).")
        except Exception as exc:
            st.warning(f"Could not fetch GitHub data: {exc}")

    if not has_input:
        st.error("Please upload a resume or enter a GitHub username.")
        return

    # Normalise and deduplicate across sources
    combined = skill_service.normalize(all_skills)
    st.session_state["skills"] = combined

    if username:
        persistence.save_profile(username, {"name": username, "skills": combined})

    if not combined:
        st.warning("No skills detected. Try a more detailed resume.")


# ---------------------------------------------------------------------------
# Tab 2 — Career & Gap
# ---------------------------------------------------------------------------

def _tab_career(services: dict, username: str) -> None:
    st.header("🗺️ Career Path & Skill Gap")

    career_service: CareerService = services["career_service"]
    course_service: CourseService = services["course_service"]
    persistence: Persistence = services["persistence"]

    careers = career_service.list_careers()
    selected = st.selectbox(
        "Select a target career path",
        options=["— select —"] + careers,
    )

    user_skills: list[str] = st.session_state.get("skills", [])

    if not user_skills:
        st.info("Go to the **Input** tab first to extract your skills.")

    if st.button("📊 Generate Report", type="primary"):
        if selected == "— select —":
            st.error("Please select a career path.")
            return
        if not user_skills:
            st.error("No skills found. Please analyse your resume first.")
            return

        try:
            gap = career_service.skill_gap(selected, user_skills)
        except ValueError as exc:
            st.error(str(exc))
            return
        except Exception as exc:
            st.error(f"Error generating report: {exc}")
            return

        st.session_state["gap"] = gap
        st.session_state["selected_career"] = selected

        if username:
            persistence.save_report(username, {"career": selected, "gap": gap})

    # --- Display gap report ---
    if "gap" in st.session_state and st.session_state["gap"]:
        gap = st.session_state["gap"]
        career_label = st.session_state.get("selected_career", "")

        st.markdown(f"### Skill Gap Report — *{career_label}*")

        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("#### ✅ Matched Skills")
            if gap["matched"]:
                for s in gap["matched"]:
                    st.markdown(f"- 🟢 {s}")
            else:
                st.markdown("_None matched_")

        with col_b:
            st.markdown("#### ❌ Missing Skills")
            if gap["missing"]:
                for s in gap["missing"]:
                    st.markdown(f"- 🔴 {s}")
            else:
                st.markdown("_None — you have all required skills!_")

        st.markdown("#### 🏆 Priority Order (Most Important First)")
        for i, skill in enumerate(gap["priority"], 1):
            st.markdown(f"{i}. **{skill}**")

        # --- Course recommendations ---
        st.markdown("---")
        st.markdown("### 📚 Recommended IBM SkillsBuild Courses")
        courses = course_service.recommend(gap["missing"])
        if courses:
            import pandas as pd  # type: ignore
            df = pd.DataFrame(courses)[["skill", "title", "duration", "url"]]
            df.columns = ["Skill", "Course", "Duration", "Link"]
            # Render clickable links
            def _make_link(row: "pd.Series") -> str:  # type: ignore
                return f'<a href="{row["Link"]}" target="_blank">🔗 Open</a>'
            df["Link"] = df.apply(_make_link, axis=1)
            st.write(df.to_html(escape=False, index=False), unsafe_allow_html=True)
        else:
            st.info("No courses found for the missing skills.")


# ---------------------------------------------------------------------------
# Tab 3 — Mock Interview
# ---------------------------------------------------------------------------

def _tab_interview(services: dict, username: str) -> None:
    st.header("🎤 Mock Interview")

    interview_service: InterviewService = services["interview_service"]
    persistence: Persistence = services["persistence"]

    user_skills: list[str] = st.session_state.get("skills", [])
    career: str = st.session_state.get("selected_career", "")
    gap: dict = st.session_state.get("gap", {})

    if not career:
        st.info("Complete the **Career & Gap** tab first to select a career.")
        return

    focus_skills = gap.get("missing", user_skills)[:5] or user_skills[:5]

    if st.button("🚀 Start Interview", type="primary"):
        try:
            questions = interview_service.generate_questions(career, focus_skills)
            if not questions:
                st.warning("No questions generated. Try again.")
                return
            # Keep exactly 5
            questions = questions[:5]
            while len(questions) < 5:
                questions.append(f"Describe your experience relevant to {career}.")
            st.session_state["questions"] = questions
            st.session_state["interview_results"] = []
            st.session_state["answers"] = {}
        except Exception as exc:
            st.error(f"Failed to generate questions: {exc}")
            return

    questions: list[str] = st.session_state.get("questions", [])
    if not questions:
        return

    interview_results: list[dict] = st.session_state.get("interview_results", [])

    st.markdown(f"**Career:** {career}  |  **Focus skills:** {', '.join(focus_skills)}")
    st.markdown("---")

    for i, question in enumerate(questions):
        st.markdown(f"**Q{i+1}:** {question}")

        answer_key = f"answer_{i}"
        answer = st.text_area(
            f"Your answer to Q{i+1}",
            key=answer_key,
            height=100,
            label_visibility="collapsed",
        )

        if st.button(f"✅ Submit Q{i+1}", key=f"submit_{i}"):
            if not answer.strip():
                st.error(f"Answer to Q{i+1} cannot be empty.")
            else:
                try:
                    evaluation = interview_service.evaluate_answer(question, answer.strip())
                    # Store by index
                    results_map = st.session_state.get("results_map", {})
                    results_map[i] = evaluation
                    st.session_state["results_map"] = results_map
                except Exception as exc:
                    st.error(f"Evaluation failed: {exc}")

        # Show feedback if already evaluated
        results_map: dict = st.session_state.get("results_map", {})
        if i in results_map:
            ev = results_map[i]
            st.markdown(
                f"> **Score:** {ev['score']}/10  \n"
                f"> **Feedback:** {ev['feedback']}  \n"
                f"> **Suggestion:** {ev['suggestion']}"
            )

        st.markdown("---")

    # Persist combined results when at least one answer evaluated
    results_map = st.session_state.get("results_map", {})
    if results_map and username:
        combined = [results_map[k] for k in sorted(results_map.keys())]
        st.session_state["interview_results"] = combined
        persistence.save_interview(username, combined)


# ---------------------------------------------------------------------------
# Tab 4 — Readiness Score
# ---------------------------------------------------------------------------

def _tab_score(services: dict, username: str) -> None:
    st.header("🏅 Job Readiness Score")

    score_service: ScoreService = services["score_service"]
    persistence: Persistence = services["persistence"]

    gap: dict = st.session_state.get("gap", {})
    # Use results_map so partial submissions also count
    results_map: dict = st.session_state.get("results_map", {})
    interview_results: list[dict] = [results_map[k] for k in sorted(results_map.keys())]

    if not gap:
        st.info("Complete the **Career & Gap** tab first.")
        return

    if st.button("📈 Calculate Score", type="primary"):
        try:
            result = score_service.calculate(gap, interview_results)
        except Exception as exc:
            st.error(f"Score calculation failed: {exc}")
            return

        st.session_state["score_result"] = result

        if username:
            persistence.save_report(
                username,
                {
                    "career": st.session_state.get("selected_career", ""),
                    "gap": gap,
                    "score": result,
                },
            )

    score_result: dict = st.session_state.get("score_result", {})
    if not score_result:
        return

    total: int = score_result["total"]
    breakdown: dict = score_result["breakdown"]

    # Big score display
    col_score, col_detail = st.columns([1, 2])

    with col_score:
        color = "#27ae60" if total >= 70 else ("#f39c12" if total >= 40 else "#e74c3c")
        st.markdown(
            f'<div style="text-align:center;font-size:4rem;font-weight:bold;'
            f'color:{color}">{total}<span style="font-size:1.5rem">/100</span></div>',
            unsafe_allow_html=True,
        )
        st.progress(total / 100)
        if total >= 70:
            st.success("Great job! You're well prepared.")
        elif total >= 40:
            st.warning("Getting there — keep practising!")
        else:
            st.error("More work needed — focus on the priority skills.")

    with col_detail:
        st.markdown("### Score Breakdown")

        sm = breakdown["skill_match"]
        iv = breakdown["interview"]

        st.markdown(f"**Skill Match** ({sm} / 50 pts)")
        st.progress(sm / 50)

        st.markdown(f"**Interview Performance** ({iv} / 50 pts)")
        st.progress(iv / 50 if iv else 0)

        if not interview_results:
            st.info("Complete the Mock Interview to earn interview points.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    services = get_services()
    persistence: Persistence = services["persistence"]

    username = _render_sidebar(persistence)

    tab1, tab2, tab3, tab4 = st.tabs(
        ["📄 Input", "🗺️ Career & Gap", "🎤 Mock Interview", "🏅 Readiness Score"]
    )

    with tab1:
        _tab_input(services, username)

    with tab2:
        _tab_career(services, username)

    with tab3:
        _tab_interview(services, username)

    with tab4:
        _tab_score(services, username)


if __name__ == "__main__":
    main()
