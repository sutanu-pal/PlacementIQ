from __future__ import annotations

import json
import os
import re
from functools import lru_cache
from typing import Any, Dict, List, Set


class SkillExtractor:
    """Deterministic, high-precision technical skill extractor."""

    def __init__(self, taxonomy_path: str | None = None) -> None:
        if not taxonomy_path:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            taxonomy_path = os.path.join(base_dir, "data", "skill_taxonomy.json")

        self.taxonomy_path = taxonomy_path
        self._load_taxonomy()

    def _load_taxonomy(self) -> None:
        with open(self.taxonomy_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.categories: Dict[str, str] = {}
        # skill_rules: list of (canonical_name, category_id, pattern_list)
        self.rules: List[Dict[str, Any]] = []

        for cat_id, cat_info in data.get("categories", {}).items():
            self.categories[cat_id] = cat_info.get("name", cat_id)
            for skill_entry in cat_info.get("skills", []):
                canonical = skill_entry["name"]
                aliases = skill_entry.get("aliases", [])
                exact_symbols = skill_entry.get("exact_symbols", False)

                compiled_patterns: List[re.Pattern] = []

                all_terms = [canonical] + aliases
                for term in all_terms:
                    pattern = self._build_pattern(term, exact_symbols)
                    if pattern:
                        compiled_patterns.append(pattern)

                self.rules.append({
                    "name": canonical,
                    "category": cat_id,
                    "category_name": self.categories[cat_id],
                    "patterns": compiled_patterns,
                })

    def _build_pattern(self, term: str, exact_symbols: bool) -> re.Pattern | None:
        """Create high-precision regex respecting word boundaries and symbols."""
        cleaned = term.strip()
        if not cleaned:
            return None

        # Special casing for terms with symbols like C++, C#, .NET
        if cleaned.upper() == "C++":
            # Match C++ when followed by space, comma, newline, or end
            return re.compile(r"(?<![a-zA-Z0-9_])C\+\+(?![a-zA-Z0-9_\+])", re.IGNORECASE)
        if cleaned.upper() == "C#":
            return re.compile(r"(?<![a-zA-Z0-9_])C#(?![a-zA-Z0-9_#])", re.IGNORECASE)
        if cleaned.upper() == "C":
            # Standalone single letter 'C' (e.g. "C, C++, Java" or "C programming" or "Language: C")
            return re.compile(
                r"(?<![a-zA-Z0-9_])C(?:\s+programming|\s+language)?(?![a-zA-Z0-9_#\+])",
                re.IGNORECASE
            )
        if cleaned.upper() == "R":
            # Standalone 'R' (e.g. "R language" or "R programming" or "Python, R, SQL")
            return re.compile(
                r"(?<![a-zA-Z0-9_])R(?:\s+programming|\s+language)?(?![a-zA-Z0-9_])",
                re.IGNORECASE
            )
        if cleaned.upper() == "GO":
            # Standalone Go or Golang
            return re.compile(
                r"(?<![a-zA-Z0-9_])(?:Go(?:\s+language|\s+programming)?|Golang)(?![a-zA-Z0-9_])",
                re.IGNORECASE
            )
        if cleaned.startswith("."):
            escaped = re.escape(cleaned)
            return re.compile(rf"(?<![a-zA-Z0-9_]){escaped}(?![a-zA-Z0-9_])", re.IGNORECASE)

        # Standard word boundary pattern
        escaped = re.escape(cleaned)
        # Handle word boundary: \b handles alphanumeric borders
        return re.compile(rf"\b{escaped}\b", re.IGNORECASE)

    def get_category_for_skill(self, skill_name: str) -> str:
        """Find category name for a given skill."""
        target = skill_name.lower().strip()
        for rule in self.rules:
            if rule["name"].lower() == target:
                return rule["category_name"]
            for pat in rule["patterns"]:
                if pat.search(skill_name):
                    return rule["category_name"]
        return "Technical"

    def extract_skills(self, text: str) -> List[Dict[str, str]]:
        """Extract unique normalized skills from freeform text."""
        if not text:
            return []

        found_skills: Dict[str, Dict[str, str]] = {}

        for rule in self.rules:
            canonical = rule["name"]
            category = rule["category"]
            category_name = rule["category_name"]

            # If already matched, skip
            if canonical in found_skills:
                continue

            for pattern in rule["patterns"]:
                if pattern.search(text):
                    found_skills[canonical] = {
                        "name": canonical,
                        "category": category,
                        "category_name": category_name,
                    }
                    break

        # Return sorted by category, then name
        return sorted(list(found_skills.values()), key=lambda x: (x["category"], x["name"]))


@lru_cache
def get_skill_extractor() -> SkillExtractor:
    return SkillExtractor()


skill_extractor = get_skill_extractor()

