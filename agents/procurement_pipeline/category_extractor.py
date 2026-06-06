"""
agents/procurement_pipeline/category_extractor.py
==================================================
Phase 1 — Smart Procurement Pipeline (PRD v2.1 Extension)

Reads a client email and extracts:
 - Project name + reference ID
 - Products grouped by trade category (Plumbing, Electrical, Hardware etc.)

Uses the existing PixtralClient LLM (same as rest of codebase).
ADDITIVE ONLY — no existing files modified.
"""
import json
import logging
import re
from datetime import datetime
from typing import Dict, List

logger = logging.getLogger(__name__)


class CategoryExtractor:
    """
    AI Agent that reads a client email and extracts procurement items
    grouped by trade category.

    Usage:
        extractor = CategoryExtractor()
        result = extractor.extract(email_subject, email_body, sender_name)
    """

    SYSTEM_PROMPT = """You are a Senior Procurement Analyst for a construction/trades company.

Your job is to read a client's email and extract:
1. A short, professional project name (e.g. "Greenfield Office Fitout", "Site B Plumbing Works")
2. A project reference code (e.g. "PRJ-2024-001") — invent one based on date and topic if none provided
3. All products/materials the client is requesting, each with:
   - item_name: clear product name
   - quantity: e.g. "20 units", "50m", "1 lot" — use "TBD" if not specified
   - category: the trade category this item belongs to. 
     Use ONLY these categories: Plumbing, Electrical, Hardware, Timber, 
     Concrete, Paint, Safety/PPE, Lifting/Rigging, Welding, Tools, Building Materials, Other

CRITICAL: Each item must be assigned to EXACTLY ONE category.
A plumber does NOT receive electrical items. An electrician does NOT receive plumbing items.

Return ONLY valid JSON in this exact format (no markdown, no explanation):
{
  "project_name": "...",
  "project_reference": "...",
  "client_name": "...",
  "items": [
    {"item_name": "...", "quantity": "...", "category": "..."},
    ...
  ]
}

If the email is NOT a procurement request, return:
{"error": "not_procurement", "reason": "brief explanation"}
"""

    def __init__(self):
        try:
            from models.pixtral_client import PixtralClient
            self.llm = PixtralClient()
            self._llm_available = True
        except Exception as e:
            logger.warning(f"[CategoryExtractor] LLM not available, using fallback: {e}")
            self._llm_available = False

    def extract(self, email_subject: str, email_body: str, sender_name: str = "") -> Dict:
        """
        Main entry point. Returns structured procurement data.

        Returns dict with keys:
            project_name, project_reference, client_name, items[]
        Or dict with key 'error' if not a procurement email.
        """
        prompt = f"""CLIENT EMAIL:
From: {sender_name}
Subject: {email_subject}

Body:
{email_body}

Extract all procurement items with their trade categories."""

        if self._llm_available:
            result = self._call_llm(prompt)
        else:
            result = self._fallback_extract(email_subject, email_body, sender_name)

        return result

    def _call_llm(self, prompt: str) -> Dict:
        """Call LLM and parse JSON response."""
        try:
            raw = self.llm.generate(
                system_prompt=self.SYSTEM_PROMPT,
                user_prompt=prompt,
                temperature=0.1
            )

            # Handle different return formats from PixtralClient
            if isinstance(raw, dict):
                if "findings" in raw or "error" in raw:
                    # LLM returned its own format, try to extract JSON from text
                    text = str(raw)
                else:
                    return raw
            elif isinstance(raw, str):
                text = raw
            else:
                text = str(raw)

            # Try to parse JSON from response text
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())

        except Exception as e:
            logger.error(f"[CategoryExtractor] LLM call failed: {e}")

        return self._fallback_extract("", "", "")

    def _fallback_extract(self, subject: str, body: str, sender: str) -> Dict:
        """
        Rule-based fallback when LLM is unavailable.
        Scans for common product keywords and assigns categories.
        """
        logger.info("[CategoryExtractor] Using rule-based fallback extraction")

        CATEGORY_KEYWORDS = {
            "Plumbing":         ["pipe", "pvc", "fitting", "valve", "tap", "faucet", "drain", "sewer", "water"],
            "Electrical":       ["cable", "wire", "conduit", "switch", "socket", "circuit", "led", "light", "electrical"],
            "Hardware":         ["bolt", "screw", "anchor", "bracket", "hinge", "lock", "handle", "door"],
            "Timber":           ["timber", "wood", "plywood", "mdf", "board", "beam", "joist"],
            "Concrete":         ["concrete", "cement", "mortar", "grout", "block", "brick"],
            "Safety/PPE":       ["helmet", "glove", "boot", "vest", "goggle", "harness", "ppe", "safety"],
            "Tools":            ["drill", "saw", "grinder", "hammer", "wrench", "tool"],
            "Paint":            ["paint", "primer", "sealer", "coating", "varnish"],
            "Building Materials": ["steel", "aluminium", "insulation", "membrane", "roofing"],
        }

        items = []
        body_lower = body.lower()

        # Simple line-by-line scan
        for line in body.split('\n'):
            line_clean = line.strip()
            if not line_clean or len(line_clean) < 5:
                continue
            line_lower = line_clean.lower()

            assigned_category = "Other"
            for cat, keywords in CATEGORY_KEYWORDS.items():
                if any(kw in line_lower for kw in keywords):
                    assigned_category = cat
                    break

            # Only add lines that look like product requests (have a keyword match or numbers)
            has_number = bool(re.search(r'\d+', line_clean))
            has_keyword = any(kw in line_lower for keywords in CATEGORY_KEYWORDS.values() for kw in keywords)

            if has_keyword or has_number:
                items.append({
                    "item_name": line_clean[:120],
                    "quantity": "TBD",
                    "category": assigned_category
                })

        # Limit to 20 items max in fallback
        items = items[:20]

        ref_date = datetime.now().strftime("%Y-%m")
        project_name = subject.replace("RE:", "").replace("FWD:", "").strip()[:60] or "Procurement Request"

        return {
            "project_name": project_name,
            "project_reference": f"PRJ-{ref_date}-AUTO",
            "client_name": sender or "Unknown Client",
            "items": items,
            "_source": "fallback"
        }

    def group_by_category(self, extraction_result: Dict) -> Dict[str, List[Dict]]:
        """
        Groups items by trade category.

        Returns: {"Plumbing": [{item_name, quantity}], "Electrical": [...], ...}
        """
        grouped: Dict[str, List[Dict]] = {}
        for item in extraction_result.get("items", []):
            cat = item.get("category", "Other")
            grouped.setdefault(cat, []).append({
                "item_name": item.get("item_name", ""),
                "quantity": item.get("quantity", "TBD")
            })
        return grouped
