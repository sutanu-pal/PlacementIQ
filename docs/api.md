# PlacementIQ — API Documentation & Integration Guide

## Overview

PlacementIQ provides an asynchronous RESTful API built on **Python FastAPI**, **SQLAlchemy 2.0 (Async)**, and **PostgreSQL** (with SQLite local development support).

- **Base URL:** `/api/v1`
- **Interactive OpenAPI Documentation (Swagger UI):** `http://localhost:8000/docs`
- **ReDoc Documentation:** `http://localhost:8000/redoc`
- **Authentication Scheme:** `Bearer <JWT_ACCESS_TOKEN>`

---

## 1. Authentication Endpoints (`/api/v1/auth`)

### 1.1 Register Candidate
- **Endpoint:** `POST /api/v1/auth/register`
- **Auth:** Public
- **Request Body (`application/json`):**
  ```json
  {
    "email": "student@college.edu",
    "password": "strongPassword123",
    "full_name": "Sutanu Ghosh",
    "college": "Institute of Technology",
    "branch": "CSE (AI & ML)",
    "semester": 7
  }
  ```
- **Response (`201 Created`):**
  ```json
  {
    "access_token": "eyJhbGciOi...",
    "refresh_token": "eyJhbGciOi...",
    "token_type": "bearer",
    "user": {
      "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "email": "student@college.edu",
      "full_name": "Sutanu Ghosh",
      "college": "Institute of Technology",
      "branch": "CSE (AI & ML)",
      "semester": 7,
      "is_active": true,
      "is_admin": false,
      "created_at": "2026-11-08T22:00:00Z"
    }
  }
  ```

### 1.2 Login
- **Endpoint:** `POST /api/v1/auth/login`
- **Auth:** Public
- **Request Body (`application/json`):**
  ```json
  {
    "email": "student@college.edu",
    "password": "strongPassword123"
  }
  ```
- **Response (`200 OK`):** Same as Register.

### 1.3 Refresh Access Token
- **Endpoint:** `POST /api/v1/auth/refresh`
- **Auth:** Public
- **Request Body (`application/json`):**
  ```json
  {
    "refresh_token": "eyJhbGciOi..."
  }
  ```
- **Response (`200 OK`):** Fresh `access_token` and `refresh_token`.

### 1.4 Get Profile
- **Endpoint:** `GET /api/v1/auth/me`
- **Auth:** Required (`Bearer`)
- **Response (`200 OK`):** User object.

---

## 2. Health & Telemetry (`/api/v1/health`)

- **Endpoint:** `GET /api/v1/health`
- **Auth:** Public
- **Response (`200 OK`):**
  ```json
  {
    "status": "healthy",
    "app": "PlacementIQ",
    "environment": "development",
    "database": "connected",
    "timestamp": "2026-11-08T22:30:00Z"
  }
  ```

---

## 3. Module 1: AI Resume Analyzer (`/api/v1/resumes`)

### 3.1 Upload & Analyze Resume
- **Endpoint:** `POST /api/v1/resumes/upload`
- **Auth:** Required (`Bearer`)
- **Content-Type:** `multipart/form-data`
- **Parameters:**
  - `file`: PDF binary file (max size 5MB)
- **Pipeline:**
  1. Validates `%PDF-` signature & size.
  2. PyMuPDF extraction with reading order sort (`sort=True`).
  3. Scanned PDF detection (< 40 characters flagged with `is_scanned: true`).
  4. Regex section classification (Contact, Education, Skills, Projects, Experience, Certifications).
  5. High-precision deterministic skill taxonomy matching across 6 categories.
  6. Transparent explainable scoring (Structure: 25, Skills: 25, Projects: 20, Education: 15, Experience: 15).
  7. Gemini 2.5 Flash actionable suggestions (with PII sanitization) or rule-based fallback.
  8. Auto-increments candidate resume version (`version: N+1`).
  9. Stores PDF privately on disk under `uploads/resumes/{user_id}/{uuid}.pdf`.
- **Response (`201 Created`):**
  ```json
  {
    "id": "c1f7a6b8-3e44-49c0-9fa2-8b6c085b3765",
    "user_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "filename": "sutanu_resume.pdf",
    "version": 1,
    "file_size_bytes": 104522,
    "status": "analyzed",
    "page_count": 1,
    "is_scanned": false,
    "overall_score": 86.0,
    "score_breakdown": {
      "structure_score": 25.0,
      "skills_score": 22.0,
      "projects_score": 19.0,
      "education_score": 10.0,
      "experience_score": 10.0
    },
    "strengths": [
      "GitHub profile link included for technical review.",
      "Well-structured resume covering essential standard engineering sections.",
      "Strong technical skill footprint with 14 detected skills."
    ],
    "improvement_areas": [
      "Mention your CGPA/percentage and expected graduation year in Education."
    ],
    "extracted_skills": [
      {"name": "Python", "category": "programming_languages", "category_name": "Programming Languages"},
      {"name": "React", "category": "frameworks_and_libraries", "category_name": "Frameworks & Libraries"},
      {"name": "PostgreSQL", "category": "databases", "category_name": "Databases & Storage"}
    ],
    "parsed_data": {
      "contact": {"email": "student@college.edu", "github": "https://github.com/..."},
      "education": [{"degree": "B.Tech CSE"}],
      "projects": [{"title": "PlacementIQ", "description": "..."}]
    },
    "ai_feedback": {
      "summary": "Well-balanced candidate resume with strong technical coverage and structured presentation.",
      "actionable_tips": ["Quantify project impact using metrics."],
      "ats_recommendations": ["Use standard section headers."],
      "formatting_advice": ["Keep layout to 1 page."],
      "is_ai_generated": false,
      "model": "PlacementIQ Rule-Based Advisor (Deterministic Fallback)"
    },
    "disclaimer": "This score evaluates resume formatting, structural completeness, and technical keyword coverage. It is an algorithmic readiness signal and does not predict recruitment success.",
    "created_at": "2026-11-08T22:30:00Z",
    "updated_at": "2026-11-08T22:30:00Z"
  }
  ```

### 3.2 List Resume Versions
- **Endpoint:** `GET /api/v1/resumes/`
- **Auth:** Required (`Bearer`)
- **Description:** Returns all previous resume versions uploaded by the authenticated student.
- **Tenant Isolation:** Users can only view their own uploaded resumes.

### 3.3 Get Resume Detail
- **Endpoint:** `GET /api/v1/resumes/{id}`
- **Auth:** Required (`Bearer`)
- **Status Codes:**
  - `200 OK`: Resume details.
  - `403 Forbidden`: User attempts to access a resume belonging to another candidate.
  - `404 Not Found`: Resume does not exist.

### 3.4 Get Full Analysis
- **Endpoint:** `GET /api/v1/resumes/{id}/analysis`
- **Auth:** Required (`Bearer`)

### 3.5 Delete Resume Version
- **Endpoint:** `DELETE /api/v1/resumes/{id}`
- **Auth:** Required (`Bearer`)
- **Description:** Deletes the database record and removes the physical PDF file from the private server directory.

---

## 4. Synthetic Test Resumes

Pre-generated synthetic resumes for evaluation and testing are available under:
- `backend/data/sample_resumes/synthetic_fullstack_ai_student.pdf`
- `backend/data/sample_resumes/synthetic_entry_student.pdf`

Generate additional synthetic resumes at any time:
```bash
python backend/data/sample_resumes/generate_samples.py
```
*(No real student personal data is ever used in test fixtures or synthetic files).*
