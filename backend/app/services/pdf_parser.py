from __future__ import annotations

import io
import re
from typing import Any, Dict, List, Optional
import pymupdf


class PDFParserError(Exception):
    """Raised when PDF cannot be parsed or is corrupted."""
    pass


class ResumePDFParser:
    """Extracts text and detects sections from PDF resumes using PyMuPDF."""

    # Common section header patterns
    SECTION_PATTERNS = {
        "education": re.compile(
            r"^(?:education|academic\s+background|academics|educational\s+qualifications?|qualifications?)\b",
            re.IGNORECASE | re.MULTILINE,
        ),
        "experience": re.compile(
            r"^(?:experience|work\s+experience|professional\s+experience|employment\s+history|internships?|work\s+history)\b",
            re.IGNORECASE | re.MULTILINE,
        ),
        "projects": re.compile(
            r"^(?:projects|academic\s+projects|personal\s+projects|technical\s+projects|key\s+projects)\b",
            re.IGNORECASE | re.MULTILINE,
        ),
        "skills": re.compile(
            r"^(?:technical\s+skills|skills\s+(?:&|and)\s+abilities|skills|core\s+competencies|technologies)\b",
            re.IGNORECASE | re.MULTILINE,
        ),
        "certifications": re.compile(
            r"^(?:certifications?|certificates?|licenses?\s+(?:&|and)\s+certifications?|courses?\s+(?:&|and)\s+certifications?|achievements?|honors?\s+(?:&|and)\s+awards?)\b",
            re.IGNORECASE | re.MULTILINE,
        ),
        "summary": re.compile(
            r"^(?:professional\s+summary|summary|profile|about\s+me|career\s+objective|objective)\b",
            re.IGNORECASE | re.MULTILINE,
        ),
    }

    EMAIL_REGEX = re.compile(
        r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+",
        re.IGNORECASE,
    )

    PHONE_REGEX = re.compile(
        r"(?:(?:\+?\d{1,3}[-.\s]?)?\(?\d{3,5}\)?[-.\s]?\d{3,5}[-.\s]?\d{4})",
    )

    LINKEDIN_REGEX = re.compile(
        r"(?:https?:\/\/)?(?:www\.)?linkedin\.com\/in\/[a-zA-Z0-9_-]+",
        re.IGNORECASE,
    )

    GITHUB_REGEX = re.compile(
        r"(?:https?:\/\/)?(?:www\.)?github\.com\/[a-zA-Z0-9_-]+",
        re.IGNORECASE,
    )

    @classmethod
    def validate_pdf_bytes(cls, content: bytes) -> bool:
        """Verify content starts with standard PDF header signature."""
        if len(content) < 4:
            return False
        return content.startswith(b"%PDF-") or b"%PDF-" in content[:1024]

    @classmethod
    def extract_text(cls, pdf_bytes: bytes) -> tuple[str, int, bool]:
        """
        Extract text from PDF bytes.
        Returns: (raw_text, page_count, is_scanned)
        """
        if not cls.validate_pdf_bytes(pdf_bytes):
            raise PDFParserError("Invalid file content: Not a valid PDF document.")

        try:
            doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
        except Exception as exc:
            raise PDFParserError(f"Corrupted or unreadable PDF: {str(exc)}") from exc

        page_count = len(doc)
        if page_count == 0:
            doc.close()
            raise PDFParserError("The uploaded PDF has 0 pages.")

        full_text_parts: List[str] = []
        for page_num in range(page_count):
            page = doc[page_num]
            # Use sort=True to enforce top-to-bottom reading order
            text = page.get_text("text", sort=True)
            if text:
                full_text_parts.append(text.strip())

        doc.close()
        combined_text = "\n\n".join(full_text_parts).strip()

        # Check for scanned or image-based PDF
        is_scanned = len(combined_text) < 40
        return combined_text, page_count, is_scanned

    @classmethod
    def parse_sections(cls, raw_text: str) -> Dict[str, Any]:
        """
        Segment raw text into structural resume sections.
        Never hallucinates: missing sections are empty.
        """
        contact_info = cls._extract_contact(raw_text)

        lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
        sections: Dict[str, List[str]] = {
            "summary": [],
            "education": [],
            "skills": [],
            "experience": [],
            "projects": [],
            "certifications": [],
            "other": [],
        }

        current_section = "other"

        for line in lines:
            detected_sec = cls._match_section_header(line)
            if detected_sec:
                current_section = detected_sec
                continue
            sections[current_section].append(line)

        # Structure the detected contents
        education_items = cls._parse_education_lines(sections["education"])
        experience_items = cls._parse_experience_lines(sections["experience"])
        project_items = cls._parse_project_lines(sections["projects"])
        cert_items = sections["certifications"]
        summary_text = " ".join(sections["summary"]).strip()

        detected_sections_list = [
            sec for sec in ["contact", "education", "skills", "experience", "projects", "certifications", "summary"]
            if (sec == "contact" and (contact_info.get("email") or contact_info.get("phone")))
            or (sec != "contact" and len(sections.get(sec, [])) > 0)
        ]

        return {
            "contact": contact_info,
            "summary": summary_text,
            "education": education_items,
            "experience": experience_items,
            "projects": project_items,
            "certifications": cert_items,
            "raw_sections": {k: "\n".join(v) for k, v in sections.items() if v},
            "detected_sections": detected_sections_list,
        }

    @classmethod
    def _match_section_header(cls, line: str) -> Optional[str]:
        # Headers are usually short (under 45 chars) and stand on their own
        if len(line) > 45:
            return None

        # Clean trailing colons, dashes or underlines
        cleaned = re.sub(r"[:\-_|]+$", "", line).strip()

        for sec_name, pattern in cls.SECTION_PATTERNS.items():
            if pattern.match(cleaned):
                return sec_name
        return None

    @classmethod
    def _extract_contact(cls, text: str) -> Dict[str, Any]:
        # Search for email
        email_match = cls.EMAIL_REGEX.search(text)
        email = email_match.group(0) if email_match else None

        # Search for phone
        phone_match = cls.PHONE_REGEX.search(text)
        phone = phone_match.group(0).strip() if phone_match else None

        # Search for LinkedIn
        linkedin_match = cls.LINKEDIN_REGEX.search(text)
        linkedin = linkedin_match.group(0) if linkedin_match else None

        # Search for GitHub
        github_match = cls.GITHUB_REGEX.search(text)
        github = github_match.group(0) if github_match else None

        return {
            "email": email,
            "phone": phone,
            "linkedin": linkedin,
            "github": github,
        }

    @classmethod
    def _parse_education_lines(cls, lines: List[str]) -> List[Dict[str, str]]:
        if not lines:
            return []
        items: List[Dict[str, str]] = []
        current: Dict[str, str] = {}

        for line in lines:
            # Check for degree keywords
            if re.search(r"\b(B\.?Tech|B\.?E\.?|M\.?Tech|B\.?S\.?|Bachelor|Master|Diploma|High School|Class XII|Class X)\b", line, re.I):
                if current:
                    items.append(current)
                current = {"degree": line, "details": ""}
            elif current:
                if current.get("details"):
                    current["details"] += f" | {line}"
                else:
                    current["details"] = line

        if current:
            items.append(current)
        elif lines:
            items.append({"degree": lines[0], "details": " ".join(lines[1:]) if len(lines) > 1 else ""})

        return items

    @classmethod
    def _parse_experience_lines(cls, lines: List[str]) -> List[Dict[str, str]]:
        if not lines:
            return []
        # Group non-empty bullet points or title lines
        items: List[Dict[str, str]] = []
        current_title = ""
        current_desc: List[str] = []

        for line in lines:
            if re.search(r"\b(Intern|Engineer|Developer|Lead|Assistant|Analyst|Specialist|Associate)\b", line, re.I) and not current_title:
                current_title = line
            elif re.search(r"\b(20\d\d|19\d\d|Present|Current|Months?)\b", line, re.I) and not current_title:
                current_title = line
            else:
                current_desc.append(line)

        items.append({
            "title": current_title or (lines[0] if lines else "Experience"),
            "description": " \n".join(current_desc) if current_desc else (lines[1] if len(lines) > 1 else ""),
        })
        return items

    @classmethod
    def _parse_project_lines(cls, lines: List[str]) -> List[Dict[str, str]]:
        if not lines:
            return []
        projects: List[Dict[str, str]] = []
        current_p: Dict[str, str] = {}

        for line in lines:
            # Projects often start with bullet points or title-like lines
            if line.startswith(("-", "•", "*")) or len(projects) == 0:
                clean_line = line.lstrip("-•* ").strip()
                if not current_p:
                    current_p = {"title": clean_line, "description": ""}
                elif len(current_p.get("description", "")) > 100:
                    projects.append(current_p)
                    current_p = {"title": clean_line, "description": ""}
                else:
                    current_p["description"] = (current_p["description"] + " " + clean_line).strip()
            else:
                if current_p:
                    current_p["description"] = (current_p.get("description", "") + " " + line).strip()
                else:
                    current_p = {"title": line, "description": ""}

        if current_p:
            projects.append(current_p)

        return projects
