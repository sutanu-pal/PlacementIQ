# PlacementIQ 🎯

**AI-Powered Placement Intelligence Platform**

> A comprehensive platform that helps students assess and improve their placement readiness through AI-powered resume analysis, intelligent job matching, DSA assessment, mock interviews, and personalized learning roadmaps.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 19 + Vite 6 + Tailwind CSS 4 |
| Backend | Python FastAPI |
| Database | PostgreSQL 16 + SQLAlchemy 2.1 |
| Auth | JWT (PyJWT) |
| AI/ML | Sentence Transformers, Scikit-learn, Gemini API, PyMuPDF |

## Modules Status

1. ✅ **AI Resume Analyzer** (Module 1) — **Fully Functional & Tested**
   - PyMuPDF text extraction with layout and spatial order preservation
   - Scanned PDF detection & corrupted document rejection
   - High-precision deterministic skill taxonomy across 6 technical categories
   - Explainable scoring engine (Structure 25, Skills 25, Projects 20, Education 15, Experience 15)
   - Multi-version resume management per candidate with tenant isolation
   - Gemini 2.5 Flash actionable feedback with PII sanitization and rule-based fallback
   - Interactive drag-and-drop React frontend with score radar, skill badges, and section viewer
2. ⏳ **Intelligent Job Matching** (Module 2) — Scheduled for Phase 2 (Sentence Transformers NLP)
3. ⏳ **DSA Assessment Engine** (Module 3) — Scheduled for Phase 2 (Sandboxed code execution)
4. ⏳ **AI Mock Interview** (Module 4) — Scheduled for Phase 2 (Multi-turn Gemini interview dialogue)
5. ⏳ **Personalized Learning Roadmap** (Module 5) — Scheduled for Phase 2 (Gap synthesis & milestones)
6. ⏳ **Placement Readiness Engine** (Phase 3) — Weighted composite readiness scoring

## Testing Suite

Run backend test suite (14 comprehensive tests):
```bash
cd backend
.\venv\Scripts\pytest -v
```

Build production frontend:
```bash
cd frontend
npm run build
```

Generate synthetic sample resumes for demonstration:
```bash
cd backend
.\venv\Scripts\python data/sample_resumes/generate_samples.py
```
*(Files created under `backend/data/sample_resumes/` without any real student personal data).*

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+
- PostgreSQL 16 (or use SQLite for local dev)

### Backend Setup

```bash
cd backend
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt

# Copy and configure environment
cp ../.env.example ../.env
# Edit .env with your values

# Run migrations
alembic upgrade head

# Start server
uvicorn app.main:app --reload --port 8000
```

### Frontend Setup

```bash
cd frontend
npm install

# Start dev server
npm run dev
```

### Docker (Full Stack)

```bash
docker compose up --build
```

## API Documentation

Once the backend is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Project Structure

```
placementIQ/
├── frontend/          # React + Vite + Tailwind
├── backend/           # Python FastAPI
│   ├── app/
│   │   ├── models/    # SQLAlchemy ORM
│   │   ├── schemas/   # Pydantic DTOs
│   │   ├── routers/   # API endpoints
│   │   ├── services/  # Business logic
│   │   └── ai/        # AI/ML modules
│   ├── data/          # Seed data
│   └── tests/         # Pytest tests
└── docs/              # Documentation
```

## Team

Built as a 7th-semester CSE (AI & ML) major project.

## License

MIT
