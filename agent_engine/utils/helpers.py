import re
from datetime import datetime

def slugify(text: str) -> str:
    """Convert text into a clean URL slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    text = re.sub(r"^-+|-+$", "", text)
    return text

def current_utc_date() -> str:
    """Return current UTC date in blog format."""
    return datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S +0000")

def truncate_description(desc: str, max_len: int = 160) -> str:
    """Ensure description fits SEO meta length."""
    if len(desc) <= max_len:
        return desc
    return desc[:max_len].rsplit(" ", 1)[0] + "..."
