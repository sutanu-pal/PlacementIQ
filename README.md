# PlacementIQ 🎯

**AI-Powered Engineering Placement Intelligence Platform**

> **7th Semester CSE (AI & ML) Major Project** — A complete full-stack platform integrating 5 specialized intelligence modules to analyze, benchmark, and accelerate engineering student placement readiness.

[![Backend Tests](https://img.shields.io/badge/Backend%20Tests-38%20Passed-brightgreen)](backend/tests/)
[![Frontend Build](https://img.shields.io/badge/Frontend%20Build-Passing-brightgreen)](frontend/)
[![Python](https://img.shields.io/badge/Python-3.11%2B-blue)](https://www.python.org/)
[![React](https://img.shields.io/badge/React-19-61DAFB)](https://react.dev/)

---

## 📋 Module Status

| # | Module | Status | Description |
|---|--------|--------|-------------|
| 1 | AI Resume Analyzer | ✅ **Live** | PyMuPDF, skill taxonomy, explainable scoring, Gemini feedback |
| 2 | Intelligent Job Matching | ✅ **Live** | Sentence Transformers (all-MiniLM-L6-v2), cosine similarity, skill gap |
| 3 | DSA Assessment Engine | ✅ **Live** | AST-sandboxed Python execution, test case evaluation, analytics |
| 4 | AI Mock Interview | ✅ **Live** | Multi-turn Gemini 2.5 Flash, 4-axis rubric, transcript history |
| 5 | Personalized Learning Roadmap | ✅ **Live** | Cross-module signal harvesting, 4-week milestones, verified URLs |
| + | Placement Readiness Engine | ✅ **Live** | Composite weighted score across all 5 dimensions, provisional scoring |
| + | Admin Dashboard | ✅ **Live** | Platform telemetry, user roster, job/DSA management |

---

## 🏗️ Architecture

```
placementIQ/
├── backend/                   # FastAPI async backend
│   ├── app/
│   │   ├── models/            # SQLAlchemy 2.0 models
│   │   │   ├── user.py        # User authentication model
│   │   │   ├── resume.py      # Resume & analysis
│   │   │   ├── job.py         # Job, JobSkill, JobMatch
│   │   │   ├── dsa.py         # DsaQuestion, DsaSubmission
│   │   │   ├── interview.py   # InterviewSession, InterviewMessage
│   │   │   ├── roadmap.py     # Roadmap, Milestone, Task
│   │   │   └── readiness.py   # PlacementReadinessSnapshot
│   │   ├── routers/           # API route handlers
│   │   ├── schemas/           # Pydantic request/response schemas
│   │   ├── services/          # Business logic layer
│   │   │   ├── resume_service.py
│   │   │   ├── job_matching_service.py    # 50% skill + 30% semantic + 20% project
│   │   │   ├── code_executor.py           # AST-sandboxed Python execution
│   │   │   ├── interview_service.py       # Gemini multi-turn + fallback
│   │   │   ├── roadmap_service.py         # Cross-module signal synthesis
│   │   │   └── readiness_service.py       # 5-dimension composite scoring
│   │   └── ai/
│   │       ├── embedding_service.py       # Sentence Transformers singleton
│   │       ├── skill_extractor.py         # Deterministic taxonomy regex
│   │       ├── pdf_parser.py              # PyMuPDF extraction
│   │       └── gemini_service.py          # Gemini API + fallback
│   ├── alembic/               # Database migration history
│   ├── data/
│   │   ├── sample_jobs.json   # 10 synthetic benchmark job postings
│   │   └── dsa_questions.json # 10 curated DSA placement problems
│   └── tests/                 # pytest suite (38 tests, 0 failures)
│
├── frontend/                  # React 19 + Vite 6 + Tailwind 4
│   └── src/
│       ├── pages/             # Feature pages for each module
│       ├── components/        # Shared UI: Navbar, Sidebar, ProtectedRoute
│       ├── context/           # AuthContext (JWT + user state)
│       └── api/client.js      # Axios API client (all modules)
│
├── docker-compose.yml         # PostgreSQL + Backend + Frontend
├── .env.example               # Environment variable template
└── README.md
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | React 19, Vite 6, Tailwind CSS 4, Lucide Icons |
| **Backend** | Python 3.11+, FastAPI (async), Uvicorn |
| **Database** | PostgreSQL 16 / SQLite (dev), SQLAlchemy 2.0 async |
| **Migrations** | Alembic (7 migration files, all applied) |
| **Auth** | PyJWT (HS256), bcrypt, Bearer token |
| **AI/ML** | Sentence Transformers (all-MiniLM-L6-v2), Scikit-learn |
| **NLP** | PyMuPDF (text extraction), regex taxonomy (skill extraction) |
| **LLM** | Google Gemini 2.5 Flash API + deterministic fallback |
| **Code Sandbox** | Python AST analysis + subprocess `-I` isolated mode |
| **Testing** | pytest-asyncio, 38 backend tests |
| **Containers** | Docker, Docker Compose |

---

## ⚡ Quick Start

### Prerequisites
- Python 3.11+
- Node.js 20+
- PostgreSQL 16 *(or SQLite for local dev — the default)*

### 1. Environment Setup

```bash
cp .env.example .env
# Edit .env — set SECRET_KEY, GEMINI_API_KEY (optional but enhances AI quality)
```

### 2. Backend Setup

```bash
cd backend

# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS/Linux

pip install -r requirements.txt

# Run all Alembic migrations
alembic upgrade head

# Start development server (SQLite by default)
uvicorn app.main:app --reload --port 8000
```

The API will be live at: http://localhost:8000
Interactive docs: http://localhost:8000/docs

### 3. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend will be at: http://localhost:5173

### 4. Docker Compose (Full Stack with PostgreSQL)

```bash
# Start all 3 services: PostgreSQL, Backend, Frontend
docker-compose up --build

# Run migrations inside the container
docker-compose exec backend alembic upgrade head
```

---

## 🧪 Testing

### Backend Tests (38 tests, 0 failures)

```bash
cd backend
venv\Scripts\python.exe -m pytest tests/ -v
```

**Test Coverage:**

| Test File | Tests | What It Covers |
|-----------|-------|----------------|
| `test_auth.py` | 5 | Registration, login, JWT, admin auth |
| `test_health.py` | 2 | API health, DB connectivity |
| `test_resume_analyzer.py` | 7 | PDF parsing, skill extraction, scoring |
| `test_job_matching.py` | 7 | NLP matching, skill coverage, admin CRUD |
| `test_dsa.py` | 7 | DSA CRUD, code execution, analytics |
| `test_interview.py` | 3 | Session lifecycle, evaluation rubric |
| `test_roadmap.py` | 4 | Roadmap generation, task toggle, streak |
| `test_readiness.py` | 3 | Composite scoring, provisional, tiers |

### Frontend Build

```bash
cd frontend
npm run build   # Must complete with 0 errors
```

---

## 🔐 Security Architecture

| Concern | Mitigation |
|---------|-----------|
| **Code Execution** | Python AST static analysis blocks `os`, `sys`, `subprocess`, `eval`, `open`, `socket` and 20+ other forbidden modules before code ever runs |
| **Subprocess Isolation** | `-I` isolated mode, temp directory sandbox, process timeout kill |
| **Admin Escalation** | Public registration never sets `is_admin=True`; promotion only via direct DB access |
| **Data Ownership** | All student routes enforce `user_id == current_user.id`; admins see all |
| **Resume PII** | Uploaded PDFs stored in `backend/uploads/` (gitignored); never served raw |
| **API Keys** | `.env` gitignored; Gemini key never exposed to frontend |
| **Scores** | All scores computed deterministically or by LLM; never hardcoded as fake results |

---

## 🤖 AI & ML Technical Details

### Module 2 — Intelligent Job Matching

**Formula:**
```
Match Score = 50% × Skill Coverage + 30% × Semantic Similarity + 20% × Project Relevance
```

- **Skill Coverage**: Required skills weighted 2× over preferred skills
- **Semantic Similarity**: `all-MiniLM-L6-v2` embeddings with cosine similarity (CPU-compatible)
- **Project Relevance**: Extracted project keywords vs. job requirements overlap
- **Model Cache**: Singleton `EmbeddingService` loads model once at startup; never on every request

> ⚠️ **Academic Disclaimer**: Match scores are educational indicators, not predictions of employment probability.

### Module 3 — DSA Code Execution Sandbox

```
Student Code → AST Security Scan → Fail (security error)
                                 ↓ Pass
                         Temp Directory
                         Python -I subprocess
                         Timeout: 2.5s
                         → Test Cases Evaluated
                         → Verdict: Accepted / Wrong Answer / TLE / Runtime Error
```

### Module 4 — AI Mock Interview

- **Gemini 2.5 Flash** generates contextual opening and adaptive follow-up questions
- 4 evaluation axes: Technical Accuracy (35%), Communication Clarity (25%), Problem Solving (25%), Role Relevance (15%)
- **Deterministic fallback**: Returns structured rubric from keyword analysis when Gemini API unavailable

### Module 5 — Learning Roadmap

- Harvests signals from: resume skill gaps → job missing skills → DSA weak topics → interview improvement areas
- Generates 4-week milestone plan with verified public resource URLs (Leetcode, YouTube, freeCodeCamp, GeeksforGeeks)
- Each task tagged with `triggered_by` for full explainability

---

## 📊 Database Schema (ER Overview)

```
User ──┬── Resume (versions)
       ├── JobMatch → Job ──── JobSkill
       ├── DsaSubmission → DsaQuestion
       ├── InterviewSession ──── InterviewMessage
       ├── Roadmap ──── RoadmapMilestone ──── RoadmapTask
       └── PlacementReadinessSnapshot
```

**Migrations applied** (Alembic at head `f83e0a31614a`):
1. `bb79ed82b250` — Initial schema (users, base tables)
2. `d748431c08c5` — Resumes table
3. `b69379427ce1` — Jobs, JobSkills, JobMatches
4. `1960895b3f4c` — DSA Questions & Submissions
5. `1181212295d1` — Interview Sessions & Messages
6. `97deda757db9` — Roadmap, Milestones, Tasks
7. `f83e0a31614a` — Placement Readiness Snapshots

---

## 🌐 API Reference

See [`docs/api.md`](docs/api.md) for the complete endpoint reference.

**Base URL:** `http://localhost:8000/api/v1`

| Group | Prefix | Endpoints |
|-------|--------|-----------|
| Auth | `/auth` | POST login, register, refresh; GET/PUT me; Admin users |
| Resume | `/resumes` | POST upload; GET list, detail, analysis; DELETE |
| Jobs | `/jobs` | GET list, detail; POST/PUT/DELETE (admin); POST match |
| Job Matches | `/job-matches` | GET list, detail |
| DSA | `/dsa` | GET/POST questions; POST submit; GET submissions, analytics |
| Interview | `/interviews` | POST start; POST answer; GET sessions, detail |
| Roadmap | `/roadmap` | GET current; POST generate; POST toggle task |
| Readiness | `/readiness` | GET current; GET history |
| Health | `/health` | GET status |

---

## 📌 Project Information

**Course:** AI & ML Major Project — 7th Semester, CSE  
**Team Size:** 3-4 students  
**Repository:** https://github.com/sutanu-pal/PlacementIQ

**Academic Note:** All synthetic job postings and DSA problems are clearly labeled for development and educational demonstration. No real company hiring data is presented. Similarity scores and readiness indices are computed by deterministic algorithms and are educational indicators only, not predictions of career outcomes.

---

## 🚀 Future Roadmap

- [ ] PostgreSQL production deployment via Docker Compose
- [ ] Rate limiting on AI endpoints (resume upload, interview answer)
- [ ] WebSocket real-time interview session streaming
- [ ] Batch student performance exports for faculty review
- [ ] Resume parsing improvements for scanned PDFs (OCR integration)
- [ ] GitHub Actions CI/CD pipeline with automated test gates
