# AI Career Copilot — Implementation Plan

## Top-Level Overview

Build a single-student, CLI-only AI Career Copilot in Python 3.11+.
The application lets a student enter their current skills, receive an
AI-generated skill-gap analysis against a target career path, practice
interview questions, and obtain a Job Readiness Score.
IBM Bob (via `ibm-generative-ai` SDK) drives every AI step.
Persistence is JSON. No web layer, no database, no authentication.

---

## 1. Final Module / File Structure

```
P1/
├── requirements.txt
├── README.md
├── data/
│   ├── career_paths.json          # seed: all CareerPath + Skill definitions
│   └── students/                  # one JSON file per saved session
│       └── <student_id>.json
├── src/
│   ├── __init__.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── student.py             # Student dataclass
│   │   ├── skill.py               # Skill dataclass
│   │   ├── career_path.py         # CareerPath dataclass
│   │   ├── skill_gap_report.py    # SkillGapReport dataclass
│   │   ├── interview.py           # InterviewQuestion + InterviewAnswer
│   │   └── readiness_score.py     # ReadinessScore dataclass
│   ├── services/
│   │   ├── __init__.py
│   │   ├── bob_client.py          # IBM Bob SDK wrapper (one place for AI calls)
│   │   ├── gap_analyzer.py        # SkillGapAnalyzer — compares student skills to path
│   │   ├── interview_coach.py     # InterviewCoach — generates and grades questions
│   │   ├── score_calculator.py    # ReadinessScoreCalculator — formula lives here
│   │   └── career_path_service.py # loads + queries career_paths.json
│   ├── persistence/
│   │   ├── __init__.py
│   │   └── student_repository.py  # save/load Student sessions to/from JSON
│   ├── exceptions.py              # full custom exception hierarchy
│   ├── validators.py              # all input validation functions
│   └── cli/
│       ├── __init__.py
│       └── main.py                # entry point — all prompts/menus live here
└── tests/
    ├── __init__.py
    ├── test_models.py
    ├── test_validators.py
    ├── test_gap_analyzer.py
    ├── test_score_calculator.py
    ├── test_career_path_service.py
    ├── test_student_repository.py
    └── test_interview_coach.py
```

**Design principle:** `src/models/` has zero imports from `services/` or `cli/`.
`services/` imports only from `models/` and `exceptions/`.
`cli/` imports only from `services/` and `models/`.
This keeps business logic fully testable without the CLI.

---

## 2. Class Diagram (Plain Text)

```
[Student]
  - id: str (uuid4)
  - name: str
  - email: str
  - current_skills: list[Skill]
  - target_career_path_id: str
  - sessions: list[SkillGapReport]
  + to_dict() -> dict
  + from_dict(d: dict) -> Student   [classmethod]

[Skill]
  - name: str                       (normalised to lowercase-stripped)
  - proficiency: int                (1–5)
  + to_dict() -> dict
  + from_dict(d: dict) -> Skill     [classmethod]

[CareerPath]
  - id: str
  - title: str
  - required_skills: list[Skill]    (proficiency = minimum required level)
  - description: str
  + to_dict() -> dict
  + from_dict(d: dict) -> CareerPath [classmethod]

[SkillGapReport]
  - id: str (uuid4)
  - student_id: str
  - career_path_id: str
  - missing_skills: list[Skill]     (skills student lacks entirely)
  - weak_skills: list[Skill]        (skills below required proficiency)
  - strong_skills: list[Skill]      (skills meeting or exceeding requirement)
  - bob_summary: str                (AI-generated narrative)
  - created_at: str                 (ISO-8601)
  + to_dict() -> dict
  + from_dict(d: dict) -> SkillGapReport [classmethod]

[InterviewQuestion]
  - id: str (uuid4)
  - career_path_id: str
  - text: str
  - skill_focus: str                (which skill this question tests)
  + to_dict() -> dict

[InterviewAnswer]
  - question_id: str
  - student_answer: str
  - bob_feedback: str               (AI-generated feedback)
  - score: int                      (1–10, AI-assigned)
  + to_dict() -> dict

[ReadinessScore]
  - student_id: str
  - career_path_id: str
  - skill_coverage_score: float     (0–100)
  - proficiency_score: float        (0–100)
  - interview_score: float          (0–100)
  - composite_score: float          (0–100)
  - band: str                       ("Not Ready" | "Developing" | "Ready" | "Highly Ready")
  - calculated_at: str              (ISO-8601)
  + to_dict() -> dict

Relationships:
  Student "has many" SkillGapReport  (Student.sessions)
  Student "has many" Skill           (Student.current_skills)
  CareerPath "has many" Skill        (CareerPath.required_skills)
  SkillGapReport "belongs to" Student
  SkillGapReport "belongs to" CareerPath
  InterviewAnswer "belongs to" InterviewQuestion
  ReadinessScore "computed from" SkillGapReport + list[InterviewAnswer]

Services (not persistent, stateless):
  BobClient          uses: ibm-generative-ai SDK
  SkillGapAnalyzer   uses: Student, CareerPath -> produces SkillGapReport
  InterviewCoach     uses: CareerPath, SkillGapReport -> produces InterviewQuestion/InterviewAnswer
  ReadinessScoreCalculator uses: SkillGapReport, list[InterviewAnswer] -> ReadinessScore
  CareerPathService  uses: career_paths.json -> produces list[CareerPath]
  StudentRepository  uses: students/<id>.json -> saves/loads Student
```

---

## 3. Exact Data Models

### Student
| Field | Type | Constraints |
|---|---|---|
| id | str | uuid4, auto-generated |
| name | str | 2–80 chars, letters/spaces/hyphens only |
| email | str | matches basic email regex |
| current_skills | list[Skill] | 1–30 items |
| target_career_path_id | str | must exist in career_paths.json |
| sessions | list[SkillGapReport] | may be empty |

### Skill
| Field | Type | Constraints |
|---|---|---|
| name | str | 1–60 chars, stored lowercase-stripped |
| proficiency | int | 1–5 inclusive |

### CareerPath
| Field | Type | Constraints |
|---|---|---|
| id | str | snake_case identifier, unique |
| title | str | 2–80 chars |
| required_skills | list[Skill] | 1–20 items |
| description | str | 10–500 chars |

### SkillGapReport
| Field | Type | Constraints |
|---|---|---|
| id | str | uuid4, auto-generated |
| student_id | str | must reference a valid Student.id |
| career_path_id | str | must reference a valid CareerPath.id |
| missing_skills | list[Skill] | computed, may be empty |
| weak_skills | list[Skill] | computed, may be empty |
| strong_skills | list[Skill] | computed, may be empty |
| bob_summary | str | AI-generated, non-empty after analysis |
| created_at | str | ISO-8601 datetime string |

### InterviewQuestion
| Field | Type | Constraints |
|---|---|---|
| id | str | uuid4 |
| career_path_id | str | valid path id |
| text | str | non-empty |
| skill_focus | str | one of the path's required skill names |

### InterviewAnswer
| Field | Type | Constraints |
|---|---|---|
| question_id | str | matches a valid InterviewQuestion.id |
| student_answer | str | 10–2000 chars |
| bob_feedback | str | AI-generated |
| score | int | 1–10, AI-assigned, validated before storing |

### ReadinessScore
| Field | Type | Constraints |
|---|---|---|
| student_id | str | valid Student.id |
| career_path_id | str | valid CareerPath.id |
| skill_coverage_score | float | 0.0–100.0 |
| proficiency_score | float | 0.0–100.0 |
| interview_score | float | 0.0–100.0 |
| composite_score | float | 0.0–100.0 |
| band | str | one of four fixed band labels |
| calculated_at | str | ISO-8601 |

---

## 4. IBM Bob Call Sites

All Bob calls are isolated inside `src/services/bob_client.py`.
No other file imports `ibm_genai` directly.

| Method on BobClient | Called by | Prompt responsibility |
|---|---|---|
| `generate_gap_summary(student, career_path, report)` | `SkillGapAnalyzer.analyze()` | Receives a structured context (student name, missing/weak skills list, career path title) and returns a 150–200 word plain-English narrative explaining the gap and top 3 recommended learning actions. |
| `generate_interview_questions(career_path, gap_report, n=5)` | `InterviewCoach.generate_questions()` | Receives career path title and the student's weak/missing skills; returns exactly `n` behavioural interview questions as a JSON array with fields `text` and `skill_focus`. |
| `grade_interview_answer(question, answer)` | `InterviewCoach.grade_answer()` | Receives the question text and the student's typed answer; returns a JSON object with fields `score` (int 1–10) and `feedback` (string, 50–150 words). |

**Prompt engineering rule:** Every prompt is a module-level constant string in
`bob_client.py` with a `{placeholder}` for dynamic data.
No prompt text lives in service or CLI code.

**Model:** Use the default IBM Granite chat model available via `ibm-generative-ai`.
The model ID is set once in `bob_client.py` via an environment variable
`BOB_MODEL_ID` with a sensible default.

---

## 5. Job Readiness Score — Formula and Weights

### Component Scores

**A. Skill Coverage Score (SCS)**
Measures what fraction of required skills the student has at all.

```
SCS = (count(strong_skills) + count(weak_skills)) / count(required_skills) * 100
```

Range: 0–100. A missing skill contributes 0; any presence (even weak) contributes.

**B. Proficiency Score (PS)**
Measures average proficiency adequacy across all required skills.

For each required skill `r`:
```
skill_ratio = min(student_proficiency, required_proficiency) / required_proficiency
              (0 if student does not have skill at all)
PS = mean(skill_ratio for all r in required_skills) * 100
```

Range: 0–100.

**C. Interview Score (IS)**
Normalise the mean of all answer scores (each 1–10) to 0–100.

```
IS = (mean(answer.score for all answers) / 10) * 100
```

If no interview was taken, IS = 0.

### Composite Score
```
composite_score = 0.40 * SCS + 0.35 * PS + 0.25 * IS
```

Weights: skill coverage 40 %, proficiency adequacy 35 %, interview 25 %.

### Band thresholds
| composite_score | band |
|---|---|
| 0 – 39 | Not Ready |
| 40 – 59 | Developing |
| 60 – 79 | Ready |
| 80 – 100 | Highly Ready |

All formula logic lives exclusively in `src/services/score_calculator.py`.

---

## 6. Skill-to-Career-Path Mapping Strategy

### Where the data lives
`data/career_paths.json` — loaded once at startup by `CareerPathService`.
The file is **bundled seed data**, not user-editable at runtime.

### Structure of career_paths.json
```json
[
  {
    "id": "data_scientist",
    "title": "Data Scientist",
    "description": "...",
    "required_skills": [
      { "name": "python", "proficiency": 4 },
      { "name": "machine learning", "proficiency": 3 },
      { "name": "statistics", "proficiency": 4 },
      { "name": "sql", "proficiency": 2 }
    ]
  },
  ...
]
```

Minimum viable seed data: **5 career paths**, each with **4–8 required skills**.
Suggested paths: Data Scientist, Backend Developer, Frontend Developer,
DevOps Engineer, Cybersecurity Analyst.

### Matching strategy
`SkillGapAnalyzer` does an exact lowercase-normalised string match between
`Student.current_skills[*].name` and `CareerPath.required_skills[*].name`.
No fuzzy matching — if the student types "Python" it is stored as "python"
(normalised at input time by `validators.py`), so exact match is safe.

---

## 7. Validation Rules for Every User Input

All rules are pure functions in `src/validators.py`.
Each function returns the cleaned value on success or raises the appropriate
custom exception on failure.

| Input | Rule | Exception raised |
|---|---|---|
| Student name | 2–80 chars; only letters, spaces, hyphens, apostrophes; strip whitespace | `InvalidNameError` |
| Student email | strip; match `^[\w.+-]+@[\w-]+\.[a-z]{2,}$` (case-insensitive) | `InvalidEmailError` |
| Skill name | strip; lowercase; 1–60 chars; only letters, digits, spaces, `+`, `#`, `.` | `InvalidSkillNameError` |
| Skill proficiency | must be int or digit-string; value in {1, 2, 3, 4, 5} | `InvalidProficiencyError` |
| Career path selection | must be a valid integer index from the displayed list | `InvalidCareerPathSelectionError` |
| Interview answer | strip; 10–2000 chars | `InvalidAnswerError` |
| Bob AI score response | must parse to int; value in 1–10 (guard against bad AI output) | `AIResponseParseError` |

---

## 8. Custom Exception Hierarchy

Defined entirely in `src/exceptions.py`.

```
CareerCopilotError (base, inherits Exception)
├── ValidationError (base for all input problems)
│   ├── InvalidNameError
│   ├── InvalidEmailError
│   ├── InvalidSkillNameError
│   ├── InvalidProficiencyError
│   ├── InvalidCareerPathSelectionError
│   └── InvalidAnswerError
├── PersistenceError (base for file I/O problems)
│   ├── StudentSaveError
│   └── StudentLoadError
├── DataError (base for seed data problems)
│   └── CareerPathNotFoundError
└── AIError (base for Bob-related problems)
    ├── AIConnectionError
    └── AIResponseParseError
```

### Where each exception is raised
| Exception | Raised in |
|---|---|
| `InvalidNameError` | `validators.validate_name()` |
| `InvalidEmailError` | `validators.validate_email()` |
| `InvalidSkillNameError` | `validators.validate_skill_name()` |
| `InvalidProficiencyError` | `validators.validate_proficiency()` |
| `InvalidCareerPathSelectionError` | `validators.validate_career_path_selection()` |
| `InvalidAnswerError` | `validators.validate_answer()` |
| `StudentSaveError` | `StudentRepository.save()` |
| `StudentLoadError` | `StudentRepository.load()` |
| `CareerPathNotFoundError` | `CareerPathService.get_by_id()` |
| `AIConnectionError` | `BobClient` on SDK network/auth failure |
| `AIResponseParseError` | `BobClient` when AI JSON cannot be parsed or score out of range |

All exceptions are caught and shown as friendly messages in `cli/main.py`.
They are never silently swallowed.

---

## 9. Persistence Format and File Layout

### Format: JSON (UTF-8, indent=2)

### File layout

**`data/career_paths.json`** — static seed, read-only at runtime.
Array of CareerPath dicts (see Section 6 for schema).

**`data/students/<student_id>.json`** — one file per saved student session.
```json
{
  "id": "550e8400-...",
  "name": "Jane Smith",
  "email": "jane@example.com",
  "target_career_path_id": "data_scientist",
  "current_skills": [
    { "name": "python", "proficiency": 3 },
    { "name": "sql", "proficiency": 2 }
  ],
  "sessions": [
    {
      "id": "...",
      "student_id": "...",
      "career_path_id": "data_scientist",
      "missing_skills": [...],
      "weak_skills": [...],
      "strong_skills": [...],
      "bob_summary": "...",
      "created_at": "2025-01-01T12:00:00"
    }
  ]
}
```

**`StudentRepository`** is the only module that reads or writes these files.
It exposes: `save(student)`, `load(student_id)`, `list_saved_ids()`.

---

## 10. Build Order

Build in this exact order because each layer depends only on the one below it.

| Step | What to build | Why first |
|---|---|---|
| 1 | `src/exceptions.py` | Zero dependencies; everything else imports from here. |
| 2 | `src/models/` (all 6 dataclasses) | Pure data, no service logic; needed by every other layer. |
| 3 | `data/career_paths.json` (seed data) | Needed to test `CareerPathService` and `SkillGapAnalyzer`. |
| 4 | `src/validators.py` | Depends only on exceptions; needed by CLI and services. |
| 5 | `src/persistence/student_repository.py` | Depends on models; can be tested with a tmp directory. |
| 6 | `src/services/career_path_service.py` | Depends on models + seed data; no AI needed. |
| 7 | `src/services/score_calculator.py` | Pure math; depends only on models. Fully unit-testable. |
| 8 | `src/services/bob_client.py` | Isolates all SDK code; mock this in tests for steps 9–10. |
| 9 | `src/services/gap_analyzer.py` + `src/services/interview_coach.py` | Depend on BobClient (mockable). |
| 10 | `src/cli/main.py` | Integrates everything; built last. |
| 11 | `tests/` | Write tests alongside or immediately after each step. |

---

## 11. pytest Test Suite — Test by Test

### `tests/test_models.py`
1. `test_skill_normalises_name_to_lowercase` — Skill("Python", 3).name == "python"
2. `test_skill_to_dict_and_back` — round-trip serialisation
3. `test_student_to_dict_and_back` — round-trip serialisation
4. `test_career_path_to_dict_and_back` — round-trip serialisation
5. `test_skill_gap_report_to_dict_and_back`
6. `test_readiness_score_band_field_is_string`

### `tests/test_validators.py`
7. `test_validate_name_valid` — "Jane Smith" passes
8. `test_validate_name_too_short` — raises InvalidNameError
9. `test_validate_name_invalid_chars` — "Jane123" raises InvalidNameError
10. `test_validate_email_valid` — "a@b.com" passes
11. `test_validate_email_invalid` — "notanemail" raises InvalidEmailError
12. `test_validate_skill_name_strips_and_lowercases`
13. `test_validate_skill_name_empty_raises`
14. `test_validate_proficiency_valid_range` — 1 through 5 each pass
15. `test_validate_proficiency_out_of_range` — 0 and 6 each raise InvalidProficiencyError
16. `test_validate_proficiency_non_integer` — "abc" raises InvalidProficiencyError
17. `test_validate_answer_too_short` — raises InvalidAnswerError
18. `test_validate_answer_too_long` — 2001-char string raises InvalidAnswerError

### `tests/test_gap_analyzer.py`
19. `test_skill_classified_as_missing_when_not_in_student_skills`
20. `test_skill_classified_as_weak_when_below_required_proficiency`
21. `test_skill_classified_as_strong_when_meets_required_proficiency`
22. `test_analyze_returns_skill_gap_report_type`
23. `test_analyze_calls_bob_generate_gap_summary_once` — mock BobClient

### `tests/test_score_calculator.py`
24. `test_skill_coverage_score_all_missing_is_zero`
25. `test_skill_coverage_score_all_present_is_100`
26. `test_proficiency_score_all_exact_match_is_100`
27. `test_proficiency_score_partial_credit_for_weak_skill`
28. `test_interview_score_normalised_correctly` — mean score 7 -> IS = 70.0
29. `test_composite_score_uses_correct_weights`
30. `test_band_not_ready_below_40`
31. `test_band_developing_40_to_59`
32. `test_band_ready_60_to_79`
33. `test_band_highly_ready_80_and_above`
34. `test_no_interview_answers_gives_is_zero`

### `tests/test_career_path_service.py`
35. `test_load_returns_list_of_career_path_objects`
36. `test_get_by_id_returns_correct_path`
37. `test_get_by_id_unknown_raises_career_path_not_found_error`
38. `test_list_all_returns_all_seeded_paths`

### `tests/test_student_repository.py`
39. `test_save_creates_json_file_in_students_dir` — uses tmp_path fixture
40. `test_load_returns_student_equal_to_saved` — round-trip
41. `test_load_nonexistent_raises_student_load_error`
42. `test_list_saved_ids_returns_saved_student_ids`

### `tests/test_interview_coach.py`
43. `test_generate_questions_returns_correct_count` — mock BobClient
44. `test_generate_questions_each_has_text_and_skill_focus` — mock BobClient
45. `test_grade_answer_returns_interview_answer` — mock BobClient
46. `test_grade_answer_score_out_of_range_raises_ai_response_parse_error` — mock returns score=11

**Total: 46 tests**

---

## 12. Assumptions and Scope Recommendations

### Assumptions
- One student per CLI run. No login, no multi-user.
- `ibm-generative-ai` SDK is installed and `BOB_API_KEY` + `BOB_MODEL_ID`
  environment variables are set by the user before running.
- Career path seed data is trusted (no runtime schema validation of
  `career_paths.json` beyond what `CareerPathService` does on load).
- Interview session is exactly 5 questions per run, not configurable at CLI.
- Proficiency scale is always 1–5; no fractional levels.
- Student sessions accumulate in the JSON file (old reports are not deleted).

### Scope — Keep These
- CLI only, single-student, JSON persistence, 5 career paths.
- 3 Bob calls (gap summary, question generation, answer grading).
- Job Readiness Score with 3 components.
- 46 unit tests, all pure (mocking Bob calls).

### Flag as Scope Creep — Cut for Beginner Version
| Feature | Why to cut |
|---|---|
| Fuzzy skill name matching (e.g. difflib) | Adds complexity; normalisation at input is sufficient. |
| Resume PDF parsing | Requires third-party PDF library; out of scope. |
| Web UI / REST API | Flask/FastAPI is a separate project; CLI is enough. |
| Multi-user / session login | Requires auth; not needed for a single-student demo. |
| Dynamic career path editing via CLI | Editing seed JSON manually is sufficient. |
| Async/streaming Bob responses | Adds concurrency complexity; synchronous calls are fine. |
| Leaderboard / comparative scoring | Requires multi-student data; out of scope. |
| Email or report export (PDF) | Scope creep; printing to console is sufficient. |

---

## Sub-Tasks

### Sub-Task 1 — Exceptions and Models
**Intent:** Define the error hierarchy and all pure data classes.
No AI, no I/O, no CLI. Everything else builds on top of this.
**Expected outcomes:**
- `src/exceptions.py` with full hierarchy.
- `src/models/` with all 6 dataclasses including `to_dict` / `from_dict`.
- `tests/test_models.py` all passing.
**Todo:**
- [ ] Create `src/exceptions.py`
- [ ] Create `src/models/skill.py`
- [ ] Create `src/models/student.py`
- [ ] Create `src/models/career_path.py`
- [ ] Create `src/models/skill_gap_report.py`
- [ ] Create `src/models/interview.py`
- [ ] Create `src/models/readiness_score.py`
- [ ] Create all `__init__.py` files
- [ ] Write `tests/test_models.py` (tests 1–6)
**Status:** `[ ] pending`

---

### Sub-Task 2 — Seed Data and Validators
**Intent:** Provide the career_paths.json seed file and all validation logic.
**Expected outcomes:**
- `data/career_paths.json` with 5 paths, 4–8 skills each.
- `src/validators.py` with all 7 validate functions.
- `tests/test_validators.py` (tests 7–18) passing.
**Todo:**
- [ ] Create `data/career_paths.json`
- [ ] Create `src/validators.py`
- [ ] Write `tests/test_validators.py`
**Status:** `[ ] pending`

---

### Sub-Task 3 — Persistence Layer
**Intent:** Implement `StudentRepository` so the student's profile and session
history can be saved and reloaded between runs.
**Expected outcomes:**
- `src/persistence/student_repository.py` with `save`, `load`, `list_saved_ids`.
- `tests/test_student_repository.py` (tests 39–42) passing.
**Todo:**
- [ ] Create `data/students/` directory (add `.gitkeep`)
- [ ] Implement `StudentRepository`
- [ ] Write `tests/test_student_repository.py`
**Status:** `[ ] pending`

---

### Sub-Task 4 — Career Path Service and Score Calculator
**Intent:** Implement the two pure-Python services (no AI calls needed).
**Expected outcomes:**
- `src/services/career_path_service.py` loads and queries the seed JSON.
- `src/services/score_calculator.py` implements the formula exactly as in Section 5.
- `tests/test_career_path_service.py` (tests 35–38) passing.
- `tests/test_score_calculator.py` (tests 24–34) passing.
**Todo:**
- [ ] Implement `CareerPathService`
- [ ] Implement `ReadinessScoreCalculator`
- [ ] Write both test files
**Status:** `[ ] pending`

---

### Sub-Task 5 — Bob Client and AI Services
**Intent:** Wrap the IBM Bob SDK and implement the two AI-driven services.
**Expected outcomes:**
- `src/services/bob_client.py` with 3 methods and all prompt constants.
- `src/services/gap_analyzer.py` and `src/services/interview_coach.py`.
- `tests/test_gap_analyzer.py` and `tests/test_interview_coach.py` passing
  (Bob calls mocked with `unittest.mock.patch`).
**Todo:**
- [ ] Implement `BobClient` with environment variable config
- [ ] Implement `SkillGapAnalyzer`
- [ ] Implement `InterviewCoach`
- [ ] Write test files mocking `BobClient`
**Status:** `[ ] pending`

---

### Sub-Task 6 — CLI Entry Point
**Intent:** Wire everything together into a working CLI flow.
**Expected outcomes:**
- `src/cli/main.py` complete with: welcome, student profile entry, career path
  selection, skill entry, gap analysis, interview practice, score display,
  save/load session.
- Manual end-to-end smoke test described in README.
- `requirements.txt` and `README.md` created.
**Todo:**
- [ ] Implement `cli/main.py` menu loop
- [ ] Create `requirements.txt`
- [ ] Create `README.md` with setup and run instructions
**Status:** `[ ] pending`
