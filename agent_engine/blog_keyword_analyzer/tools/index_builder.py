# src/agent_engine/kra/blog_index_builder.py
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml  # pip install pyyaml

from ..config import settings, platform_PATTERNS


class FrontMatterError(Exception):
    """Custom exception for front matter parsing issues."""
    pass


# -------------------------------------------------------------------
# platform detection
# -------------------------------------------------------------------

def detect_platforms_from_front_matter(fm: Dict[str, Any]) -> List[str]:
    """
    Detect platforms from various front-matter fields:
    - title, seoTitle, description, summary, url
    - tags (list)
    - categories (list)
    """
    chunks: List[str] = []

    # String fields
    for key in ("title", "seoTitle", "description", "summary", "url"):
        value = fm.get(key)
        if isinstance(value, str):
            chunks.append(value)

    # List fields
    for key in ("tags", "categories"):
        value = fm.get(key)
        if isinstance(value, list):
            chunks.extend(str(item) for item in value)

    combined = " ".join(chunks).lower()

    detected: List[str] = []
    for fw, patterns in platform_PATTERNS.items():
        for p in patterns:
            if p in combined:
                detected.append(fw)
                break  # stop on first match for this platform

    # De-duplicate while preserving order
    seen: set[str] = set()
    unique: List[str] = []
    for fw in detected:
        if fw not in seen:
            seen.add(fw)
            unique.append(fw)

    if settings.DEBUG:
        # Optional: uncomment if you want to debug per-post
        # print("DEBUG platforms combined text:", combined)
        # print("DEBUG platforms detected:", unique)
        pass

    return unique

# -------------------------------------------------------------------
# Front matter parsing & metadata
# -------------------------------------------------------------------
def _read_front_matter(md_path: Path) -> Dict[str, Any]:
    """
    Extract YAML front matter from an index.md file.

    Expected structure:

    ---
    key: value
    ...
    ---
    <markdown content>
    """
    text = md_path.read_text(encoding="utf-8")

    if not text.lstrip().startswith("---"):
        raise FrontMatterError(f"No front matter starting with '---' in {md_path}")

    lines = text.splitlines()
    if not lines:
        raise FrontMatterError(f"Empty file: {md_path}")

    start_idx: Optional[int] = None
    end_idx: Optional[int] = None

    for idx, line in enumerate(lines):
        if line.strip() == "---":
            if start_idx is None:
                start_idx = idx
            else:
                end_idx = idx
                break

    if start_idx is None or end_idx is None or end_idx <= start_idx:
        raise FrontMatterError(f"Could not find closing '---' for front matter in {md_path}")

    yaml_block = "\n".join(lines[start_idx + 1 : end_idx])

    try:
        data = yaml.safe_load(yaml_block) or {}
        if not isinstance(data, dict):
            raise FrontMatterError(f"Front matter is not a mapping in {md_path}")
    except yaml.YAMLError as exc:
        raise FrontMatterError(f"YAML parsing error in {md_path}: {exc}") from exc

    # Make sure date is JSON-friendly
    if "date" in data:
        data["date"] = str(data["date"])

    return data


def _derive_metadata(md_path: Path, content_root: Path) -> Dict[str, Any]:
    """
    Derive additional metadata from the file path:
      - slug: parent folder name (e.g. '2025-10-10-convert-txt-to-csv-in-python')
      - product: folder just above slug (e.g. 'cells')
      - rel_path: path relative to BLOG_CONTENT_ROOT
    """
    slug = md_path.parent.name

    product: Optional[str] = None
    try:
        # e.g. C:\aspose-blog\content\Aspose.Blog\cells\2025-10-10-...\index.md
        rel_parts = md_path.parent.parent.relative_to(content_root).parts
        if rel_parts:
            product = rel_parts[0]
    except Exception:
        # path did not match expected structure
        pass

    rel_path = md_path.relative_to(content_root)

    return {
        "slug": slug,
        "product": product,
        "rel_path": str(rel_path),
        "abs_path": str(md_path.resolve()),
    }


def build_blog_index() -> List[Dict[str, Any]]:
    """
    Walk BLOG_CONTENT_ROOT, find all index.md, extract front matter and derived fields.

    Each entry will look like:

    {
      "title": "...",
      "seoTitle": "...",
      "description": "...",
      "date": "...",
      "draft": false,
      "url": "/cells/convert-txt-file-to-csv-in-python/",
      "author": "Muzammil Khan",
      "summary": "...",
      "tags": [...],
      "categories": [...],

      "slug": "...",
      "product": "cells",
      "rel_path": "cells/2025-10-10-convert-txt-to-csv-in-python/index.md",
      "abs_path": "...",

      "platforms": ["python"],
      "primary_platform": "python"
    }
    """
    # 👇 Convert env string to Path
    content_root = Path(settings.BLOG_CONTENT_ROOT).expanduser().resolve()

    if settings.DEBUG:
        print("DEBUG BLOG_CONTENT_ROOT raw:", repr(settings.BLOG_CONTENT_ROOT))
        print("DEBUG content_root resolved:", content_root)

    if not content_root.exists():
        raise FileNotFoundError(f"Blog content root does not exist: {content_root}")

    index_files = list(content_root.rglob("index.md"))
    if settings.DEBUG:
        print(f"DEBUG: Found {len(index_files)} index.md files under {content_root}")

    blog_entries: List[Dict[str, Any]] = []

    for md_path in index_files:
        try:
            fm = _read_front_matter(md_path)
        except FrontMatterError as exc:
            if settings.DEBUG:
                print(f"[WARN] Skipping {md_path}: {exc}")
            continue

        derived = _derive_metadata(md_path, content_root)

        # 🔍 Detect platforms using front-matter
        platforms = detect_platforms_from_front_matter(fm)
        primary_platform: Optional[str] = platforms[0] if platforms else None

        entry: Dict[str, Any] = {
            **derived,
            **fm,
            "platforms": platforms,
            "primary_platform": primary_platform,
        }

        blog_entries.append(entry)

    return blog_entries


def save_blog_index(entries: List[Dict[str, Any]]) -> Path:
    """
    Save the blog index as JSON to BLOG_INDEX_JSON.
    """
    out_path = Path(settings.BLOG_INDEX_JSON).expanduser().resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with out_path.open("w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)

    return out_path


def main() -> None:
    """
    Standalone entrypoint.

    Usage (from project root):

        python -m agents.kra.blog_index_builder
    """
    print(f"📂 Scanning blog content root: {settings.BLOG_CONTENT_ROOT}")
    entries = build_blog_index()
    print(f"✅ Found {len(entries)} posts with valid front matter")

    out_path = save_blog_index(entries)
    print(f"💾 Blog index written to: {out_path}")


if __name__ == "__main__":
    main()