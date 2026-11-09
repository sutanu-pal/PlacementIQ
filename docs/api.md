# PlacementIQ — API Reference

**Base URL:** `http://localhost:8000/api/v1`

All protected endpoints require `Authorization: Bearer <access_token>` header.

---

## Authentication (`/auth`)

### `POST /auth/register`
Register a new student account. Never sets `is_admin = True`.

**Body:**
```json
{
  "email": "student@example.com",
  "password": "SecurePass123!",
  "full_name": "Rahul Sharma",
  "college": "NIT Rourkela",
  "branch": "CSE (AI & ML)",
  "semester": 7
}
```
**Response:** `201 Created` → `{ access_token, refresh_token, token_type, user }`

---

### `POST /auth/login`
Authenticate and receive JWT tokens.

**Body:** `{ "email": "...", "password": "..." }`
**Response:** `200 OK` → `{ access_token, refresh_token, token_type, user }`

---

### `POST /auth/refresh`
Exchange a valid refresh token for a new access token.

**Body:** `{ "refresh_token": "..." }`
**Response:** `200 OK` → `{ access_token, refresh_token, token_type, user }`

---

### `GET /auth/me`
Get current authenticated user's profile.
**Auth:** Required | **Response:** `UserResponse`

---

### `PUT /auth/me`
Update profile fields (full_name, college, branch, semester).
**Auth:** Required | **Body:** Partial `UserUpdate` | **Response:** `UserResponse`

---

### `GET /auth/admin/users` *(Admin Only)*
List all registered platform users.
**Auth:** Admin | **Response:** `List[UserResponse]`

---

### `GET /auth/admin/stats` *(Admin Only)*
Platform telemetry: total students, resumes analyzed, job matches, DSA submissions, interview counts, roadmap count, readiness tier distribution.
**Auth:** Admin | **Response:** Telemetry dict

---

### `PUT /auth/admin/users/{user_id}/toggle-status` *(Admin Only)*
Toggle a user's `is_active` flag (enable/disable account).
**Auth:** Admin | **Response:** `UserResponse`

---

## AI Resume Analyzer (`/resumes`)

### `POST /resumes/upload`
Upload a PDF resume for AI analysis.

- Extracts text using PyMuPDF with layout preservation
- Detects sections: Education, Experience, Projects, Skills, Certifications
- Extracts skills across 6 categories via deterministic regex taxonomy
- Computes explainable score: Structure(25) + Skills(25) + Projects(20) + Education(15) + Experience(15)
- Generates Gemini 2.5 Flash actionable feedback with PII sanitization

**Auth:** Required | **Content-Type:** `multipart/form-data` | **Field:** `file` (PDF)
**Response:** `201 Created` → `ResumeDetailResponse`

---

### `GET /resumes/`
List all resume versions for the authenticated user.
**Auth:** Required | **Response:** `{ resumes: [...], total: int }`

---

### `GET /resumes/{resume_id}`
Get resume metadata and summary.
**Auth:** Required (owner only) | **Response:** `ResumeDetailResponse`

---

### `GET /resumes/{resume_id}/analysis`
Get full analysis: score breakdown, extracted skills, project summary, section flags, Gemini suggestions.
**Auth:** Required (owner only) | **Response:** `ResumeDetailResponse`

---

### `DELETE /resumes/{resume_id}`
Delete a resume version.
**Auth:** Required (owner only) | **Response:** `200 OK`

---

## Intelligent Job Matching (`/jobs`)

### `GET /jobs/`
Browse active job opportunities with filtering and search. Auto-seeds 10 synthetic benchmark jobs on first call.

**Auth:** Required | **Query Params:**
- `search` — Full-text search (title, company, keywords)
- `experience_level`, `location`, `employment_type`, `skill` — Filters
- `is_active` (default: `true`), `limit`, `offset`

**Response:** `{ items: [JobResponse], total: int }`

---

### `GET /jobs/{job_id}`
Get full job details including required/preferred skills.
**Auth:** Required | **Response:** `JobResponse`

---

### `POST /jobs/` *(Admin Only)*
Create a new job posting. Automatically generates embedding for semantic matching.
**Auth:** Admin | **Body:** `JobCreate` | **Response:** `201 Created` → `JobResponse`

---

### `PUT /jobs/{job_id}` *(Admin Only)*
Update a job posting.
**Auth:** Admin | **Body:** `JobUpdate` (partial) | **Response:** `JobResponse`

---

### `DELETE /jobs/{job_id}` *(Admin Only)*
Delete a job posting.
**Auth:** Admin | **Response:** `200 OK`

---

### `POST /jobs/{job_id}/match`
Compute NLP-powered match score between the student's latest resume and this job.

**Algorithm:**
```
Match Score = 50% × Skill Coverage + 30% × Semantic Similarity + 20% × Project Relevance
```

**Auth:** Required | **Body (optional):** `{ "resume_id": "..." }` (defaults to latest)
**Response:** `JobMatchResponse` including:
- `match_score` — Overall weighted score (0–100)
- `skill_score`, `semantic_score`, `project_score` — Component breakdowns
- `matched_skills`, `missing_required_skills`, `missing_preferred_skills`
- `explanations` — Human-readable match reasoning
- `recommendations` — Targeted improvement suggestions

> ⚠️ **Academic Note:** Match score is an educational indicator only, not an employment probability.

---

## Job Match History (`/job-matches`)

### `GET /job-matches/`
List historical match evaluations for the authenticated student.

**Auth:** Required | **Query:** `job_id` (filter), `limit`, `offset`
**Response:** `{ items: [JobMatchResponse], total: int }`

---

### `GET /job-matches/{match_id}`
Get detailed match breakdown. Enforces student ownership.
**Auth:** Required (owner only) | **Response:** `JobMatchResponse`

---

## DSA Assessment Engine (`/dsa`)

### `GET /dsa/questions`
List active DSA coding challenges. Auto-seeds 10 benchmark problems on first call.

**Auth:** Required | **Query:** `category`, `difficulty`, `limit`, `offset`
**Response:** `{ items: [DsaQuestionListItem], total: int }`

**Available categories:** Arrays, Strings, Linked Lists, Trees, Graphs, Dynamic Programming, Greedy, Recursion
**Difficulty levels:** Easy, Medium, Hard

---

### `GET /dsa/questions/{id_or_slug}`
Get full question detail with visible test cases. Hidden test cases are not returned.
**Auth:** Required | **Response:** `DsaQuestionDetail`

---

### `POST /dsa/questions/{question_id}/submit`
Submit Python solution for automated evaluation.

**Security Pipeline:**
1. Static AST analysis — blocks `os`, `sys`, `subprocess`, `eval`, `open`, `socket`, etc.
2. Subprocess with `-I` isolated flag in temp directory
3. 2.5s timeout with process kill
4. Host path scrubbing from tracebacks

**Auth:** Required | **Body:** `{ "code": "def solution(...):\n    ..." }`
**Response:** `DsaSubmitResponse` with:
- `status` — `Accepted` / `Wrong Answer` / `Time Limit Exceeded` / `Runtime Error` / `Security Violation`
- `passed_cases`, `total_cases`, `execution_time_ms`

---

### `GET /dsa/submissions`
List student's submission history.
**Auth:** Required | **Query:** `question_id`, `limit`, `offset`
**Response:** `{ items: [...], total: int }`

---

### `GET /dsa/submissions/{id}`
Get individual submission details. Enforces ownership.
**Auth:** Required (owner only) | **Response:** `DsaSubmitResponse`

---

### `GET /dsa/analytics`
Get topic-wise DSA performance metrics.
**Auth:** Required | **Response:**
```json
{
  "total_solved": 4,
  "total_questions": 10,
  "overall_solve_pct": 40.0,
  "total_submissions": 7,
  "overall_accuracy_pct": 71.4,
  "topic_breakdown": [
    { "category": "Arrays", "total_questions": 3, "solved_questions": 2, "accuracy_pct": 85.0 }
  ],
  "weakness_areas": ["Dynamic Programming", "Graphs"],
  "recommendations": ["Focus practice on Dynamic Programming..."]
}
```

---

### `POST /dsa/questions` *(Admin Only)*
Create a new DSA coding assessment question.
**Auth:** Admin | **Body:** `DsaQuestionCreate` | **Response:** `201 Created`

---

### `PUT /dsa/questions/{id}` *(Admin Only)*
Update an existing DSA question.
**Auth:** Admin | **Body:** `DsaQuestionUpdate` (partial) | **Response:** `DsaQuestionDetail`

---

### `DELETE /dsa/questions/{id}` *(Admin Only)*
Delete a DSA question.
**Auth:** Admin | **Response:** `200 OK`

---

## AI Mock Interview (`/interviews`)

### `POST /interviews/start`
Start a new AI-powered mock interview session.

**Auth:** Required | **Body:**
```json
{
  "role_title": "Software Development Engineer",
  "interview_type": "Technical",
  "total_questions": 4,
  "job_id": "optional-job-id"
}
```
**interview_type:** `Technical` | `Behavioral` | `System Design`
**Response:** `InterviewSessionResponse` with the first question populated.

---

### `POST /interviews/{session_id}/answer`
Submit an answer to the current interview question.

Triggers Gemini 2.5 Flash rubric evaluation across:
- **Technical Accuracy** (35%) — Correctness, depth, examples
- **Communication Clarity** (25%) — Articulation, structure, STAR method
- **Problem Solving** (25%) — Approach, edge cases, trade-offs
- **Role Relevance** (15%) — Domain alignment, terminology

**Auth:** Required (owner only) | **Body:** `{ "answer_text": "..." }`
**Response:** `InterviewTurnResponse` with:
- `evaluation` — Per-axis scores and feedback
- `next_question` — Adaptive follow-up (or null if complete)
- `is_completed` — Whether session is finished
- `session` — Full updated session state

---

### `GET /interviews/`
List historical interview sessions.
**Auth:** Required | **Query:** `limit`, `offset`
**Response:** `{ items: [InterviewSessionListItem], total: int }`

---

### `GET /interviews/{session_id}`
Get full session transcript with all messages and evaluation rubric.
**Auth:** Required (owner only) | **Response:** `InterviewSessionResponse`

---

## Personalized Learning Roadmap (`/roadmap`)

### `GET /roadmap/`
Get the current personalized learning roadmap. Auto-generates a default one if none exists.

**Auth:** Required | **Response:** `RoadmapResponse` with:
- `milestones` — 4-week structured curriculum
- `completion_pct` — Progress percentage (0–100)
- `current_streak_days` — Consecutive days with task completions
- Each task includes: `triggered_by` explanation, `resource_url`, `estimated_hours`, `priority`

---

### `POST /roadmap/generate`
Regenerate roadmap from latest cross-module signals.

Harvests from: Resume skill gaps → Job missing skills → DSA weak topics → Interview improvement areas

**Auth:** Required | **Body:** `{ "target_role": "Full Stack Engineer" }`
**Response:** `RoadmapResponse`

---

### `POST /roadmap/tasks/{task_id}/toggle`
Toggle a task's completion status. Updates `completion_pct` and `current_streak_days`.
**Auth:** Required | **Response:** Full `RoadmapResponse`

---

## Placement Readiness Engine (`/readiness`)

### `GET /readiness/`
Compute (and save) the explainable placement readiness score.

**Formula:**
```
Readiness Score = 25% × Resume + 25% × Job Matching + 25% × DSA + 15% × Interview + 10% × Roadmap
```

Provisional scoring applies when fewer than all 5 dimensions have data.

**Auth:** Required | **Response:**
```json
{
  "overall_score": 72.4,
  "provisional_score": 72.4,
  "evaluated_dimensions_count": 4,
  "total_dimensions_count": 5,
  "readiness_tier": "Approaching Placement Readiness",
  "dimension_scores": {
    "Resume Quality": { "score": 78.5, "weight": 0.25, "available": true, "status_message": "...", "metric_summary": "..." }
  },
  "strengths": ["Strong core CS foundations in Data Structures"],
  "weaknesses": ["DSA coverage below 60%"],
  "recommendations": ["Practice 2 DP problems per day"],
  "formula_documentation": "...",
  "disclaimer": "Scores are educational indicators..."
}
```

**Readiness Tiers:**
- `≥ 75%` → **High Placement Potential**
- `≥ 50%` → **Approaching Placement Readiness**
- `< 50%` → **Needs Preparation**

---

### `GET /readiness/history`
Retrieve up to 20 historical readiness snapshots to track progress over time.
**Auth:** Required | **Response:** `List[{ id, overall_score, provisional_score, readiness_tier, created_at }]`

---

## Health Check (`/health`)

### `GET /health`
API and database connectivity check.
**Auth:** None | **Response:** `{ status: "ok", database: "connected", ... }`

---

## Error Responses

All errors follow standard HTTP semantics:

| Code | Meaning |
|------|---------|
| `400` | Bad request / validation error |
| `401` | Missing or invalid/expired JWT |
| `403` | Forbidden — insufficient permissions or ownership mismatch |
| `404` | Resource not found |
| `422` | Pydantic validation failure (request schema) |
| `500` | Internal server error |

**Error body format:**
```json
{ "detail": "Human-readable error message" }
```
