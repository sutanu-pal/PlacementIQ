# PlacementIQ — Academic Viva Q&A

Prepared for 7th Semester CSE (AI & ML) Major Project Defence.

---

## 1. Project Overview

**Q: What is PlacementIQ and what problem does it solve?**

PlacementIQ is an AI-powered placement intelligence platform that helps engineering students benchmark their placement readiness across five dimensions: Resume quality, Job matching fit, DSA problem-solving, mock interview performance, and learning roadmap execution. The platform identifies specific skill gaps, explains why a job matches or doesn't match a candidate, provides sandboxed coding assessment, conducts adaptive AI interviews using Gemini 2.5 Flash, and generates a personalized 4-week preparation curriculum.

**Q: Why is this relevant to AI & ML?**

The project applies three distinct AI/ML paradigms:
1. **NLP Semantic Similarity** — `all-MiniLM-L6-v2` Sentence Transformer to encode resume and job description text into 384-dimensional vectors, then compute cosine similarity.
2. **Large Language Models** — Gemini 2.5 Flash for adaptive interview question generation and 4-axis rubric evaluation with structured JSON output.
3. **Deterministic ML Pipeline** — Regex-based skill taxonomy, weighted scoring formulas, and AST-based program analysis.

---

## 2. Technical Architecture

**Q: Explain your project's tech stack and why these choices were made.**

- **FastAPI** (backend): Native async/await support, automatic OpenAPI docs, Pydantic validation
- **SQLAlchemy 2.0 async**: Type-safe ORM with async session management; PostgreSQL-compatible with SQLite for development
- **React 19 + Vite 6**: Component-based UI with extremely fast HMR; Tailwind CSS for consistent dark-theme design system
- **Alembic**: Schema versioning with 7 sequential migrations; avoids destructive manual ALTER TABLE commands
- **JWT (HS256)**: Stateless auth — access token (30 min) + refresh token (7 days); no server-side session storage required

**Q: How does async FastAPI improve performance?**

Async allows the FastAPI event loop to handle other requests while waiting for I/O (database queries, Gemini API calls, file reads). This means a slow Gemini API call (2–5 seconds) does not block other students from using the platform. With `asyncio` + `asyncpg` (PostgreSQL driver) or `aiosqlite`, all DB operations yield control rather than blocking threads.

**Q: Why SQLAlchemy 2.0 over raw SQL or Django ORM?**

SQLAlchemy 2.0 supports `select()` compositional style with type hints, async sessions, and PostgreSQL-to-SQLite compatibility through the same code. Django ORM lacks native async support. Raw SQL loses schema portability and type safety. Alembic (SQLAlchemy's migration tool) tracks all schema changes with version control.

---

## 3. Module 1: AI Resume Analyzer

**Q: How does your resume skill extractor work?**

It uses a `SkillExtractor` class with a curated taxonomy of ~200+ technical skill patterns organized into 6 categories: Programming Languages, Web Frameworks, Databases, Cloud & DevOps, AI/ML Tools, and CS Fundamentals. Each skill has a regex pattern compiled at class initialization. During extraction, the full resume text is lowercased and each pattern is applied. This deterministic approach avoids LLM hallucination of non-existent skills.

**Q: How is the resume score computed?**

Five weighted components (each 0–100):
- Structure (25%): Section completeness (Education, Experience, Projects, Skills, Certifications)
- Skills (25%): Count of extracted skills, normalized, with diminishing returns above 20
- Projects (20%): Count of projects × quality signals (GitHub links, metric descriptions, tech mentions)
- Education (15%): Degree level, GPA/percentage, institution tier heuristics
- Experience (15%): Internships, work experience, duration

The final score is `Σ(component × weight)`.

**Q: Why PyMuPDF instead of PDFMiner or pdfplumber?**

PyMuPDF is significantly faster and handles multi-column layouts, embedded fonts, and CJK characters better. It preserves reading order spatially. pdfplumber is accurate but slower; PDFMiner requires more post-processing. For our use case (fast upload → extract → analyze pipeline), PyMuPDF's performance is superior.

---

## 4. Module 2: Intelligent Job Matching

**Q: Explain the NLP job matching formula.**

```
Match Score = 50% × Skill Coverage + 30% × Semantic Similarity + 20% × Project Relevance
```

- **Skill Coverage**: `covered_required / total_required × 2 + covered_preferred / total_preferred × 1` normalized — required skills weighted 2× because they gate hiring eligibility
- **Semantic Similarity**: Cosine similarity between `encode(resume_text)` and `encode(job_description)`. Ranges -1 to 1; we scale to 0–100
- **Project Relevance**: Keyword intersection between extracted project mentions and job required skills

**Q: What is Sentence Transformers' all-MiniLM-L6-v2?**

It's a lightweight 22M parameter sentence embedding model trained on Natural Language Inference and semantic similarity datasets. It outputs 384-dimensional normalized vectors where semantically similar sentences have high cosine similarity. "L6" refers to 6 Transformer layers; "MiniLM" is a distillation of larger BERT variants. It runs on CPU in reasonable time (~50ms per sentence pair on modern hardware).

**Q: How is the embedding model loaded efficiently?**

`EmbeddingService` is a module-level singleton. The model is loaded once at application startup via Python's module import system (single import → single load). Subsequent requests reuse the loaded model without re-initialization. The model files (~80MB) are cached in `backend/models_cache/` after first download.

**Q: Is cosine similarity the same as probability of getting hired?**

No — this is explicitly stated in the platform. Cosine similarity measures textual-semantic alignment between resume and job description. It does not account for location preference, compensation expectations, cultural fit, interview performance, or company-specific criteria. The score is an educational indicator to guide skill development.

---

## 5. Module 3: DSA Assessment Engine

**Q: How does the code execution sandbox work?**

Three-layer security:
1. **Static AST Analysis**: The student's code is parsed into an Abstract Syntax Tree. All `Import`, `ImportFrom`, and `Call` nodes are inspected against blocklists. Forbidden modules include `os`, `sys`, `subprocess`, `socket`, `urllib`, `requests`, `ctypes`, `eval`, `open`, etc. If any forbidden construct is found, execution is rejected *before any code runs*.
2. **Subprocess Isolation**: Code is written to a temp file and executed as a child process with `python -I` (isolated mode — ignores `PYTHONPATH`, `PYTHONSTARTUP`, site packages outside venv). The working directory is a fresh temp directory.
3. **Timeout Kill**: subprocess has a 2.5-second hard timeout. If exceeded, `process.kill()` is called and `TLE` is returned. Host paths are scrubbed from tracebacks.

**Q: Why not use Docker containers for code execution?**

For a student major project scope, Docker-per-submission adds significant orchestration complexity (container lifecycle management, networking, volumes). Our AST + subprocess `-I` + timeout approach is effective for the Python-only scope. In production at scale (e.g., Codeforces/LeetCode), Docker or Firecracker microVMs would be used for stronger isolation.

**Q: What categories of DSA problems are included?**

Arrays, Strings, Linked Lists, Trees, Graphs, Dynamic Programming, Greedy, Recursion. 10 curated problems currently; admin can add more via the Admin Dashboard. Problems include both visible examples and hidden test cases.

---

## 6. Module 4: AI Mock Interview

**Q: How does the adaptive interview work?**

1. `POST /interviews/start` sends role title and type to the `InterviewService`
2. Gemini is prompted to generate a contextual opening question appropriate for the role
3. Student submits answer via `POST /interviews/{id}/answer`
4. Gemini evaluates the answer on 4 axes (Technical, Communication, Problem Solving, Role Relevance) and returns structured JSON scores + feedback
5. If `current_question_index < total_questions`, Gemini generates a follow-up question based on the conversation history (adaptive — it can probe weak answers deeper)
6. When complete, Gemini synthesizes an executive feedback report

**Q: What is the fallback when Gemini API is unavailable?**

`InterviewService` catches all Gemini exceptions and falls back to a deterministic rubric evaluator that scores based on:
- Answer length (proxy for depth)
- Keyword presence matching the question domain
- Sentence count (proxy for structured response)
This ensures the platform works even without API quota.

**Q: What is STAR method and why is it evaluated?**

STAR = **S**ituation, **T**ask, **A**ction, **R**esult. It's the industry-standard framework for behavioral interview answers. The Communication Clarity axis in our rubric rewards structured STAR-method responses because they demonstrate organized thinking, which hiring managers specifically look for.

---

## 7. Module 5: Personalized Learning Roadmap

**Q: What are "cross-module signals" in the roadmap generator?**

The `RoadmapService` queries across four data sources for the same user:
1. **Resume**: `missing_key_sections` and `low_skill_coverage_areas` from the latest resume analysis
2. **Job Matching**: `missing_required_skills` aggregated across the user's top match results
3. **DSA**: `weakness_areas` (categories with < 40% accuracy or 0 solved)
4. **Interview**: `improvement_areas` from the latest completed session's evaluation

These signals are merged, deduplicated, and prioritized by cross-module frequency to generate 4 weekly milestones targeting the highest-impact preparation gaps.

**Q: Are the resource URLs real?**

Yes — all URLs in the roadmap are real, publicly accessible resources on platforms like LeetCode, YouTube (official edu channels), GeeksforGeeks, freeCodeCamp, and MDN. They are hardcoded per topic pattern in `roadmap_service.py` and verified during development. We never fabricate or hallucinate resource URLs.

---

## 8. Placement Readiness Engine

**Q: What is the composite readiness formula?**

```
Readiness = 0.25 × Resume + 0.25 × Job Matching + 0.25 × DSA + 0.15 × Interview + 0.10 × Roadmap
```

Each dimension is normalized to 0–100 before weighting.

**Q: What is "provisional scoring"?**

If a student hasn't used all 5 modules, we still compute a score using only the available dimensions, then clearly label it "Provisional." The provisional score = `Σ(available_scores × weights) / Σ(available_weights)`. This prevents students who have only used 2 modules from seeing 0% — they see a fair estimate from their completed work.

**Q: What are the placement tiers?**

- **High Placement Potential** (≥ 75%): Ready for top-tier placement drives
- **Approaching Placement Readiness** (50–74%): 1–2 weeks of focused improvement needed
- **Needs Preparation** (< 50%): Foundational curriculum review required

---

## 9. Security & Data Privacy

**Q: How is admin escalation prevented?**

The public registration endpoint (`POST /auth/register`) hardcodes `is_admin = False`. There is no API endpoint to promote a user to admin. Admin promotion must be done by a database administrator directly in the PostgreSQL/SQLite users table. No production code path allows self-promotion or public admin grant.

**Q: How is cross-user data isolation enforced?**

Every protected route that accesses user-owned data includes an ownership check: `if resource.user_id != current_user.id and not current_user.is_admin: raise 403`. This covers resumes, job matches, DSA submissions, interview sessions, roadmaps, and readiness snapshots. Admins can read all records for platform management.

**Q: Are uploaded resumes stored securely?**

Resumes are stored in `backend/uploads/{user_id}/` (server-local). The directory is gitignored. Files are never served raw to the client — only extracted text, metadata, and analysis results are returned via API. PII fields (like phone numbers, addresses) in raw text are not stored in the database.

---

## 10. Testing & Quality

**Q: How many tests do you have and what do they cover?**

38 backend tests across 8 test files, all passing with 0 failures:
- Authentication (5): Registration, login, JWT, admin guard
- Health (2): API status, DB connectivity
- Resume (7): Upload mock, extraction, scoring, Gemini mock
- Job Matching (7): NLP match flow, skill coverage, admin CRUD, permissions
- DSA (7): Question CRUD, code execution (accepted/WA/TLE/security), analytics
- Interview (3): Session start, answer submit, history
- Roadmap (4): Generation, task toggle, streak
- Readiness (3): Composite scoring, provisional, tier

**Q: How do you test without real PDF files or real Gemini API?**

- Resume tests create a minimal in-memory PDF using PyMuPDF's `fitz.open()` API
- Gemini calls are either mocked (test monkeypatching) or fall back to the deterministic fallback automatically
- Job matching tests use a lightweight text corpus to test the matching logic without loading the full Sentence Transformer model (the embedding service handles graceful degradation)

**Q: How is the test database isolated?**

We use SQLite in-memory mode with `StaticPool` (single connection, same session reused for tests). The `conftest.py` fixture creates all tables fresh at the start of each test session. The same `AsyncSession` is shared between the test client and fixtures — this is essential because in-memory SQLite only exists in the connection that created it.

---

## 11. Limitations & Future Work

**Q: What are the current limitations of your system?**

1. **Code execution**: Only Python is supported. Java/C++ would require additional language runtimes and more complex sandboxing.
2. **Semantic matching accuracy**: Sentence Transformer cosine similarity can produce high scores for topically similar but technically mismatched text (e.g., a data science resume matching a web dev job if both use ML buzzwords).
3. **Resume parsing**: Scanned PDFs (image-based) cannot be parsed — PyMuPDF reads embedded text only. OCR (Tesseract/Google Vision) would be needed for scanned documents.
4. **LLM rate limits**: Heavy Gemini API usage may hit quota limits; fallback is deterministic but less nuanced.
5. **Single server**: No horizontal scaling, rate limiting, or message queue for heavy AI workloads.

**Q: What would you improve with more time?**

- Docker Compose with PostgreSQL for production deployment
- WebSocket-based real-time interview streaming (instead of polling)
- OCR integration for scanned PDFs
- Multi-language code execution using Docker microcontainers
- GitHub Actions CI/CD pipeline with automated test gates
- Rate limiting on AI-heavy endpoints (FastAPI `slowapi`)
