from __future__ import annotations

import argparse
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
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
    chunks: List[str] = []

    for key in ("title", "seoTitle", "description", "summary", "url"):
        value = fm.get(key)
        if isinstance(value, str):
            chunks.append(value)

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
                break

    seen: set[str] = set()
    unique: List[str] = []
    for fw in detected:
        if fw not in seen:
            seen.add(fw)
            unique.append(fw)

    return unique


# -------------------------------------------------------------------
# Date parsing for sorting
# -------------------------------------------------------------------

def _date_sort_key(value: Any) -> float:
    """
    Convert a date value to a sortable float (timestamp).

    Supports:
    - RFC 2822 style: 'Fri, 10 Oct 2025 01:28:57 +0000'
    - ISO style: '2025-10-10T01:28:57+00:00' / '2025-10-10 01:28:57'

    Returns:
        Unix timestamp (float). If parsing fails, returns +inf so undated
        posts appear at the end in ascending order.
    """
    if isinstance(value, str):
        # Try RFC 2822
        try:
            dt = parsedate_to_datetime(value)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.timestamp()
        except Exception:
            pass

        # Try ISO-like formats
        try:
            dt = datetime.fromisoformat(value)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.timestamp()
        except Exception:
            pass

    # Put unknown/missing dates at the end
    return float("inf")


# -------------------------------------------------------------------
# Front matter parsing & metadata from filesystem
# -------------------------------------------------------------------

def read_front_matter(md_path: Path) -> Dict[str, Any]:
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

    if "date" in data:
        data["date"] = str(data["date"])

    return data


def derive_metadata(md_path: Path, content_root: Path) -> Dict[str, Any]:
    slug = md_path.parent.name

    product: Optional[str] = None
    try:
        rel_parts = md_path.parent.parent.relative_to(content_root).parts
        if rel_parts:
            product = rel_parts[0]
    except Exception:
        pass

    rel_path = md_path.relative_to(content_root)

    return {
        "slug": slug,
        "product": product,
        "rel_path": str(rel_path),
        "abs_path": str(md_path.resolve()),
    }


# -------------------------------------------------------------------
# Search directly from directory
# -------------------------------------------------------------------

def search_from_directory(
    product: str,
    platform: Optional[str] = None,
) -> List[Dict[str, Any]]:
    content_root = Path(settings.BLOG_CONTENT_ROOT).expanduser().resolve()

    if settings.DEBUG:
        print("DEBUG BLOG_CONTENT_ROOT raw:", repr(settings.BLOG_CONTENT_ROOT))
        print("DEBUG content_root resolved:", content_root)

    if not content_root.exists():
        raise FileNotFoundError(f"Blog content root does not exist: {content_root}")

    index_files = list(content_root.rglob("index.md"))
    if settings.DEBUG:
        print(f"DEBUG: Found {len(index_files)} index.md files under {content_root}")

    product_norm = product.lower().strip()
    platform_norm = platform.lower().strip() if platform else None

    results: List[Dict[str, Any]] = []

    for md_path in index_files:
        try:
            fm = read_front_matter(md_path)
        except FrontMatterError as exc:
            if settings.DEBUG:
                print(f"[WARN] Skipping {md_path}: {exc}")
            continue

        meta = derive_metadata(md_path, content_root)
        entry_product = (meta.get("product") or "").lower().strip()
        if entry_product != product_norm:
            continue

        platforms = detect_platforms_from_front_matter(fm)
        primary_platform: Optional[str] = platforms[0] if platforms else None

        if platform_norm:
            platforms_norm = [f.lower().strip() for f in platforms]
            if platform_norm not in platforms_norm:
                continue

        entry: Dict[str, Any] = {
            **meta,
            **fm,
            "platforms": platforms,
            "primary_platform": primary_platform,
        }
        results.append(entry)

    # 🔽 Sort ascending by date (oldest first)
    results.sort(key=lambda e: _date_sort_key(e.get("date")))

    return results


# -------------------------------------------------------------------
# CLI entrypoint for quick testing
# -------------------------------------------------------------------

def main() -> None:
    """
    Usage examples (from project root):

        # All Cells posts (any platform), sorted by date ascending
        python -m agents.kra.blog_frontmatter_search --product cells

        # Cells + Python only
        python -m agents.kra.blog_frontmatter_search --product cells --platform python
    """
    parser = argparse.ArgumentParser(
        description="Search blog posts directly from directory based on front matter."
    )
    parser.add_argument(
        "--product",
        required=True,
        help="Product code/folder, e.g. cells, words, pdf",
    )
    parser.add_argument(
        "--platform",
        required=False,
        help="Optional platform filter, e.g. python, java, csharp",
    )

    args = parser.parse_args()

    matches = search_from_directory(args.product, args.platform)
    fw_display = args.platform or "ANY"
    print(f"🔎 Found {len(matches)} posts for product='{args.product}' platform='{fw_display}'\n")

    for entry in matches:
        title = entry.get("title") or "(no title)"
        url = entry.get("url") or "(no url)"
        platforms = entry.get("platforms") or []
        date_str = entry.get("date") or "(no date)"
        print(f"- {date_str} | {title}")
        print(f"  url={url}")
        print(f"  platforms={platforms}")
        print(f"  rel_path={entry.get('rel_path')}")
        print()


if __name__ == "__main__":
    main()
