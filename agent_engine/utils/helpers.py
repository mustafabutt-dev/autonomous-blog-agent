import re
from datetime import datetime

def slugify(text: str) -> str:
    """Convert text into a clean URL slug with C# → csharp normalization."""

    if not text:
        return ""

    # Normalize C# → CSharp BEFORE lowercasing
    text = text.replace("C#", "CSharp").replace("c#", "CSharp")

    # Continue with normal slugify steps
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)      # remove invalid chars
    text = re.sub(r"[\s_-]+", "-", text)      # collapse spaces/underscores
    text = re.sub(r"^-+|-+$", "", text)       # trim hyphens

    return text

def sanitize_markdown_title(title: str) -> str:
    """
    Removes special characters that can break Markdown formatting,
    such as ':', '|', '`', '*', etc., while keeping letters,
    numbers, spaces, and basic punctuation.
    """
    # Remove markdown-breaking characters
    sanitized = re.sub(r'[:`*>|\\/\[\](){}_~]', '', title)
    
    # Replace multiple spaces with a single space
    sanitized = re.sub(r'\s+', ' ', sanitized)
    
    # Trim extra spaces at the ends
    sanitized = sanitized.strip()
    
    return sanitized

def current_utc_date() -> str:
    """Return current UTC date in blog format."""
    return datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S +0000")

def truncate_description(desc: str, max_len: int = 160) -> str:
    """Ensure description fits SEO meta length."""
    if len(desc) <= max_len:
        return desc
    return desc[:max_len].rsplit(" ", 1)[0] + "..."

def format_related_posts(related_links):
    # If it's a dict ({"related_posts": [...]})
    if isinstance(related_links, dict):
        related_posts = related_links.get("related_posts", [])
    else:
        related_posts = related_links

    formatted_lines = []

    for post in related_posts:
        if isinstance(post, dict):
            title = post.get("title", "")
            url = post.get("url", "")
            formatted_lines.append(f"- [{title}]({url})")

        elif isinstance(post, str):  # handle raw string URLs
            formatted_lines.append(f"- [Related Post]({post})")

    return "\n".join(formatted_lines)

def get_productInfo(product_name:str, platform:str, products) -> str:
    base_name = product_name.strip()
    platform_clean = platform.strip()

    # Build expected product name EXACTLY as in your data
    if(platform == "cloud"):
        expected_name = f"{base_name} {platform_clean}"
    else: 
        expected_name = f"{base_name} for {platform_clean}"

    # Case-insensitive matching
    product_info = next(
        (p for p in products
        if p["ProductName"].lower() == expected_name.lower()),
        None
    )

    if not product_info:
        raise ValueError(
            f"No product found for '{product_name}' with platform '{platform}'"
        )

    return product_info

def prepare_context(product_info) -> str:
    context=''
    # Prepare context
    for k, v in product_info.items():
        context += f"\n{k}: {v}"
    return context