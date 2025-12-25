# src/agents/kra/tools/serp_import.py
from __future__ import annotations

import requests
import re
from typing import List, Optional, Tuple

from ..config import settings
from ..schemas import KeywordRecord


def _locale_to_hl_gl(locale: str) -> Tuple[str, str]:
    """
    Convert a BCP-47-ish locale like 'en-US' to SerpAPI's hl/gl.
    Fallbacks are reasonable defaults.
    """
    if not locale:
        return "en", "us"

    # naive split: "en-US" -> ("en", "us")
    parts = re.split(r"[-_]", locale)
    if len(parts) == 1:
        return parts[0].lower(), "us"
    hl = parts[0].lower()
    gl = parts[1].lower()
    return hl, gl


def fetch_serp_keywords(
    topic: str,
    product: str,
    locale: str = "en-US",
    max_keywords: int = 50,
) -> List[KeywordRecord]:
    """
    Use SerpAPI to pull search-intent-enriched keywords from Google SERPs.

    Strategy:
      - Build a query from product + topic.
      - Pull organic result titles/snippets.
      - Pull 'People Also Ask' / related searches when present.
      - Deduplicate and normalize into KeywordRecord instances.

    NOTE: Google SERP does not provide search volume/KD/CPC,
    so we leave those fields as None and let your scoring logic
    treat volume=0 or use fallbacks.
    """
    if not settings.SERPAPI_API_KEY:
        raise RuntimeError("SERPAPI_API_KEY is not configured in settings/.env")

    hl, gl = _locale_to_hl_gl(locale)

    query = f"{product} {topic}".strip()
    params = {
        "engine": settings.SERPAPI_ENGINE or "google",
        "q": query,
        "hl": hl,
        "gl": gl,
        "api_key": settings.SERPAPI_API_KEY,
    }

    resp = requests.get("https://serpapi.com/search", params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    keywords: List[str] = []

    # 1) Organic result titles/snippets
    for item in data.get("organic_results", []):
        title = item.get("title") or ""
        if title:
            keywords.append(title)
        snippet = item.get("snippet") or ""
        if snippet:
            # we can split snippet into smaller phrases, but keep it simple for now
            keywords.append(snippet)

    # 2) People Also Ask / related questions
    for item in data.get("related_questions", []) or data.get("people_also_ask", []):
        question = item.get("question") or item.get("title") or ""
        if question:
            keywords.append(question)

    # 3) Related searches
    for item in data.get("related_searches", []):
        rel = item.get("query") or item.get("title") or ""
        if rel:
            keywords.append(rel)

    # Normalize/dedupe
    seen = set()
    normalized_keywords: List[KeywordRecord] = []

    for kw in keywords:
        kw_clean = kw.strip()
        if not kw_clean:
            continue

        # use lowercase for de-duplication
        key = kw_clean.lower()
        if key in seen:
            continue
        seen.add(key)

        normalized_keywords.append(
            KeywordRecord(
                keyword=kw_clean,
                source="serpapi",
                locale=locale,
                volume=None,
                cpc=None,
                kd=None,
                clicks=None,
                url=None,
                competition=None,
                competition_label=None,
            )
        )

        if len(normalized_keywords) >= max_keywords:
            break

    return normalized_keywords
