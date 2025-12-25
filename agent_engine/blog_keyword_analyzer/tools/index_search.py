from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..config import settings, platform_PATTERNS

def _get_index_path() -> Path:
    """
    Resolve the blog index JSON file path.

    We expect an env var BLOG_INDEX_JSON, e.g.:
        BLOG_INDEX_JSON=./src/data/blog_index.json

    If you didn't add BLOG_INDEX_JSON to Settings, you can instead
    point this to settings.KRA_OUTPUT_DIR / "blog_index.json".
    """
    # If you already defined BLOG_INDEX_JSON in Settings:
    if hasattr(settings, "BLOG_INDEX_JSON"):
        raw = getattr(settings, "BLOG_INDEX_JSON")
        path = Path(raw)
    else:
        # Fallback: under KRA_OUTPUT_DIR/blog_index.json
        path = Path(settings.KRA_OUTPUT_DIR) / "blog_index.json"

    return path.expanduser().resolve()


def load_blog_index() -> List[Dict[str, Any]]:
    """
    Load the blog index JSON into memory.

    Returns:
        List of blog entries (dicts).
    """
    index_path = _get_index_path()

    if not index_path.is_file():
        raise FileNotFoundError(f"Blog index JSON not found at: {index_path}")

    with index_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError(f"Expected a list in blog index JSON, got: {type(data)}")

    return data


def search_blog_index(
    product: str,
    platform: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Filter blog entries by product and (optionally) platform.

    Args:
        product: product code / folder (e.g. "cells", "words", "pdf").
        platform: optional canonical platform name (e.g. "python", "java", "csharp").
                   If None, no platform filtering is applied.

    Returns:
        List of matching blog entries (dicts).
    """
    entries = load_blog_index()

    product_norm = product.lower().strip()
    platform_norm = platform.lower().strip() if platform else None

    results: List[Dict[str, Any]] = []

    for entry in entries:
        entry_product = str(entry.get("product") or "").lower().strip()
        if entry_product != product_norm:
            continue

        if platform_norm:
            platforms = entry.get("platforms") or []
            platforms_norm = [str(f).lower().strip() for f in platforms]

            # Very small safety: allow "c#" / "csharp" mismatch by normalizing
            if platform_norm in {"c#", "c-sharp"}:
                platform_norm_cmp = "csharp"
            else:
                platform_norm_cmp = platform_norm

            if platform_norm_cmp not in platforms_norm:
                continue

        results.append(entry)

    return results


def main() -> None:
    """
    Simple CLI test to verify the search feature.

    Usage examples (from project root):

        # All 'cells' posts
        python -m agent_engine.kra.blog_index_search --product cells

        # Only 'cells' + 'python'
        python -m agent_engine.kra.blog_index_search --product cells --platform python

        # Only 'cells' + 'java'
        python -m agent_engine.kra.blog_index_search --product cells --platform java
    """
    parser = argparse.ArgumentParser(
        description="Test blog index search by product and optional platform."
    )
    parser.add_argument(
        "--product",
        required=True,
        help="Product code/folder, e.g. cells, words, pdf"
    )
    parser.add_argument(
        "--platform",
        required=False,
        help="Optional platform filter, e.g. python, java, csharp"
    )

    args = parser.parse_args()

    matches = search_blog_index(args.product, args.platform)

    fw_display = args.platform or "ANY"
    print(f"🔎 Found {len(matches)} posts for product='{args.product}' platform='{fw_display}'\n")

    # Print a small summary list
    for entry in matches:
        title = entry.get("title") or "(no title)"
        url = entry.get("url") or "(no url)"
        platforms = entry.get("platforms") or []
        print(f"- {title}\n  url={url}\n  platforms={platforms}\n")


if __name__ == "__main__":
    main()
