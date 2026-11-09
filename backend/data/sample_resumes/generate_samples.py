"""
Generate synthetic sample resumes in PDF format for testing PlacementIQ.
Never uses real student personal data. All names, emails, and data are fictional.
"""
from __future__ import annotations

import os
import pymupdf


def make_pdf(filename: str, lines: list[str]) -> None:
    doc = pymupdf.open()
    page = doc.new_page(width=595, height=842)  # A4 size

    y = 50
    for line in lines:
        if line.startswith("# "):
            page.insert_text((50, y), line[2:], fontsize=16, fontname="helv", color=(0.1, 0.2, 0.5))
            y += 24
        elif line.startswith("## "):
            y += 8
            page.insert_text((50, y), line[3:].upper(), fontsize=12, fontname="helv", color=(0.2, 0.3, 0.7))
            y += 18
        elif line.startswith("- "):
            page.insert_text((65, y), "• " + line[2:], fontsize=10, fontname="helv", color=(0.2, 0.2, 0.2))
            y += 15
        elif line.strip() == "":
            y += 8
        else:
            page.insert_text((50, y), line, fontsize=10, fontname="helv", color=(0.1, 0.1, 0.1))
            y += 15

    out_dir = os.path.dirname(__file__)
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, filename)
    doc.save(out_path)
    doc.close()
    print(f"Generated synthetic test PDF: {out_path}")


def main():
    # 1. Strong Full-Stack & AI Student
    fullstack_resume = [
        "# Alex Morgan (Synthetic Candidate)",
        "Email: alex.morgan.synthetic@college.edu | Phone: +1 555-019-8834",
        "LinkedIn: https://linkedin.com/in/alex-morgan-synthetic | GitHub: https://github.com/alexmorgan-dev",
        "",
        "## Professional Summary",
        "Final-year B.Tech CSE (AI & ML) candidate with demonstrated expertise in full-stack architecture,",
        "distributed backend systems, and applied machine learning models.",
        "",
        "## Education",
        "B.Tech in Computer Science & Engineering (AI & ML Specialization)",
        "Metropolitan Institute of Technology | 2022 - 2026 | CGPA: 9.1 / 10.0",
        "",
        "## Technical Skills",
        "- Programming Languages: Python, C++, Java, JavaScript, TypeScript, SQL",
        "- Frameworks & Web: React, FastAPI, Node.js, Express.js, Tailwind CSS, Next.js",
        "- AI & Machine Learning: PyTorch, Scikit-learn, TensorFlow, Natural Language Processing, Pandas, NumPy",
        "- Databases & Cloud: PostgreSQL, MongoDB, Redis, Docker, AWS, Git, CI/CD, GitHub Actions",
        "",
        "## Key Projects",
        "# 1. Distributed Placement Intelligence Engine",
        "- Developed high-throughput asynchronous microservices in FastAPI and PostgreSQL with SQLAlchemy 2.0.",
        "- Engineered PyMuPDF resume parsing pipeline and integrated dense semantic vectors via Sentence Transformers.",
        "- Deployed multi-container environment with Docker and automated testing via GitHub Actions.",
        "",
        "# 2. Real-Time Algorithmic Code Execution Sandbox",
        "- Built isolated Python subprocess execution harness with memory and CPU time quotas for 20+ DSA challenges.",
        "- Designed real-time testcase assertion telemetry and responsive React 19 UI with Monaco Editor.",
        "",
        "## Practical Experience",
        "# Software Engineering Intern | CyberTech Solutions",
        "- May 2025 - August 2025 | Bengaluru, India",
        "- Engineered RESTful API endpoints and reduced database query latency by 35% through Redis caching.",
        "- Automated integration test suite with Pytest, increasing test coverage from 60% to 92%.",
        "",
        "## Certifications & Achievements",
        "- AWS Certified Cloud Practitioner (2025)",
        "- Ranked top 5% in National Inter-College Coding Hackathon (2025)",
    ]
    make_pdf("synthetic_fullstack_ai_student.pdf", fullstack_resume)

    # 2. Entry Level / Needs Optimization Student
    entry_resume = [
        "# Rohan Verma (Synthetic Candidate)",
        "Email: rohan.v.synthetic@college.edu",
        "",
        "## Education",
        "Bachelor of Technology in Computer Science",
        "City Engineering College, Graduating 2026",
        "",
        "## Skills",
        "- C, Java, HTML, CSS, SQL",
        "",
        "## Projects",
        "# Library Management System",
        "- Created a desktop library database system using Java and SQL.",
        "",
        "# Personal Blog Website",
        "- Designed basic website using HTML and CSS.",
    ]
    make_pdf("synthetic_entry_student.pdf", entry_resume)


if __name__ == "__main__":
    main()
