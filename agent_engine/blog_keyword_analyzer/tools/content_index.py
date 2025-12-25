from __future__ import annotations

from typing import List, Optional

# adjust this import to match your actual package path
from .directory_search import search_from_directory

from ..schemas import ExistingPost


def get_existing_posts(
    product: Optional[str] = None,
    platform: Optional[str] = None,
) -> List[ExistingPost]:
    """
    Thin wrapper around Content Index Service directory search.

    Both product and platform are optional, to match the CLI:
      python -m src.content_index_service.directory_search --product ... --platform ...

    If they are None, we just pass them through as None.
    """

    raw_matches = search_from_directory(
        product=product,
        platform=platform,
    )

    posts: List[ExistingPost] = [
        ExistingPost(
            title=entry.get("title") or "",
            slug=entry.get("slug") or "",
            url=entry.get("url") or "",
            product=entry.get("product"),
            platform=entry.get("platform"),
            rel_path=entry.get("rel_path"),
        )
        for entry in raw_matches
    ]

    return posts
