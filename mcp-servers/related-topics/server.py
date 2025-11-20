"""
Optimized Two-Tier RSS Reader MCP Server
Tier 1: RSS metadata scan (fast)
Tier 2: Content fetch (accurate fallback)
"""
from fastmcp import FastMCP, Context
from typing import List, Dict, Optional, Tuple
import httpx
from bs4 import BeautifulSoup
import re
import sys
import requests

# Initialize FastMCP server
mcp = FastMCP("Related Links Reader")

# -------------------------
# Product language extraction
# -------------------------
def extract_language_from_product(product_name: str) -> Optional[str]:

    if not product_name:
        return None

    text = product_name.lower().strip()
    text = re.sub(r"\s+", " ", text)

    # 1) "for <lang> via <other>"
    match_via = re.search(r"for\s+([a-z0-9\.\+#\- ]+?)\s+via\b", text)
    if match_via:
        lang = match_via.group(1).strip()

        # SPECIAL CASE:
        # Case: "Node.js via Java" -> JavaScript
        lang_raw = lang
        via_raw = text.split("via")[1].strip()
        if ("node" in lang_raw or "node.js" in lang_raw) and "java" in via_raw:
            return "javascript"

        # normalize
        if "python" in lang:
            return "python"
        if "java" in lang:
            return "java"
        if "node" in lang or "node.js" in lang:
            return "nodejs"
        if "javascript" in lang:
            return "javascript"
        if "c++" in lang or "cpp" in lang:
            return "c++"
        if ".net" in lang or lang == "net":
            return "c#"
        return lang

    # 2) "for <lang>" at end
    match_simple = re.search(r"for\s+([a-z0-9\.\+#\- ]+?)\s*$", text)
    if match_simple:
        lang = match_simple.group(1).strip()
        if lang in [".net", "net"] or ".net" in lang:
            return "c#"
        if "python" in lang:
            return "python"
        if "java" in lang:
            return "java"
        if "node" in lang or "node.js" in lang:
            return "nodejs"
        if "javascript" in lang:
            return "javascript"
        if "c++" in lang or "cpp" in lang:
            return "c++"
        return lang

    return None

# -------------------------
# LANGUAGE PATTERNS (safe)
# Keys use normalized language ids: 'java','python','c#','c++','nodejs','javascript'
# Avoid overly-generic tokens that appear in many posts.
# -------------------------
LANGUAGE_PATTERNS = {
    "java": [
        "public class",
        "import java",
        "maven",
        "jar",
        "gradle",
        "springframework",
        "junit"
    ],
    "python": [
        r"\bpip install\b",
        r"\bimport\b",
        r"\bfrom\b",
        r"\bdef\b",
        r"\bprint\(",
        "pandas",
        "numpy"
    ],
    "c#": [
        r"\bc#\b",
        "csharp",
        "nuget",
        r"\busing\s+system\b",
        r"\bconsole\.writeline\b"
    ],
    "c++": [
        r"\bc\+\+\b",
        r"\b#include\b",
        r"\bstd::\b",
        r"\bcout\b",
        "iostream"
    ],
    "nodejs": [
        "npm install",
        r"\brequire\(",
        r"\bmodule\.exports\b",
        r"\bconsole\.log\b",
        r"\bconst\b"
    ],
    "javascript": [
        r"\bjavascript\b",
        r"\bnode\.js\b",
        r"\bconsole\.log\b"
    ]
}

# -------------------------
# Robust content-based detector
# -------------------------
def detect_language_from_text(text: str, target_language: str = None) -> Tuple[bool, int]:
    """
    Safely detect language indicators inside text.
    Returns (is_match, score). Uses regex word boundaries and conservative scoring to avoid false positives.
    """
    if not text or not target_language:
        return False, 0

    text_lower = text.lower()

    # normalize incoming target language to our keys
    target = target_language.lower()

    # if target uses alternate keys (e.g., ".net"), normalize to "c#"
    if target in [".net", "net"]:
        target = "c#"

    # get patterns list, if none use literal target token
    patterns = LANGUAGE_PATTERNS.get(target, [target])

    score = 0

    # pattern matching with safe regex
    for p in patterns:
        try:
            # treat patterns that look like regex already (we used r"" for some)
            regex = p if p.startswith(r"\b") or "(" in p else r"\b" + re.escape(p) + r"\b"
            if re.search(regex, text_lower, flags=re.IGNORECASE):
                # weight code-like tokens a bit higher
                if "public class" in p or "def" in p or "import java" in p or r"\b#include\b" in p:
                    score += 3
                else:
                    score += 2
        except re.error:
            # fallback to substring match if regex fails
            if p in text_lower:
                score += 1

    # Extra check: explicit language mentions (only for safe tokens)
    if target in ["python", "java", "nodejs", "javascript", "c++", "c#"]:
        # avoid using ".net" as direct indicator because it matches domains
        if target == "c#":
            # match either 'c#' or 'csharp'
            if re.search(r"\bc#\b", text_lower) or re.search(r"\bcsharp\b", text_lower):
                score += 3
        else:
            if re.search(r"\b" + re.escape(target) + r"\b", text_lower):
                score += 3

    return (score > 0, score)

# -------------------------
# Category pagination & scraping (unchanged logic, returns title+url)
# -------------------------
async def fetch_category_articles(url, required, max_limit=300):
    """
    Scrape category pages and stop immediately once `required` relevant links are found.
    Works with Aspose Hugo category pages.
    """
    results = []
    next_page = url

    while next_page and len(results) < required and len(results) < max_limit:
        print(f"[fetch_category_articles] Fetching: {next_page}", file=sys.stderr, flush=True)

        resp = requests.get(next_page, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Accept-Language": "en-US,en;q=0.9"
        })
        if resp.status_code != 200:
            break

        soup = BeautifulSoup(resp.text, "html.parser")

        # Extract posts
        for article in soup.select("article.post-entry"):
            if len(results) >= required:
                break  # early stop

            title_tag = article.select_one("header.entry-header h2")
            link_tag = article.select_one("a.entry-link")
            if title_tag and link_tag:
                title = title_tag.get_text(strip=True)
                href = link_tag.get("href")
                # normalize absolute URL if necessary
                if href and href.startswith("/"):
                    parsed = requests.utils.urlparse(next_page)
                    href = f"{parsed.scheme}://{parsed.netloc}{href}"
                results.append({"title": title, "url": href})

                if len(results) >= required:
                    break

        # move to next page
        if len(results) >= required:
            break

        next_link = soup.select_one("nav.pagination a.next")
        next_page = next_link.get("href") if next_link else None

    print(f"[fetch_category_articles] collected {len(results)} items", file=sys.stderr, flush=True)
    return results

# -------------------------
# Fetch article content (existing)
# -------------------------
async def fetch_article_content(url: str, timeout: int = 6) -> Optional[str]:
    """
    Fetch full article content for deep language detection
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=timeout, follow_redirects=True)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                # remove noise
                for element in soup(['script', 'style', 'nav', 'header', 'footer']):
                    element.decompose()
                # code blocks
                code_blocks = soup.find_all(['code', 'pre'])
                code_text = ' '.join([block.get_text() for block in code_blocks])
                # main article content
                article = soup.find('article')
                if article:
                    content = article.get_text(separator=' ')
                else:
                    content = soup.get_text(separator=' ')
                return f"{code_text} {content}"[:6000]
    except Exception as e:
        print(f"[fetch_article_content] Error: {e}", file=sys.stderr)
    return None

# -------------------------
# MCP tool
# -------------------------
@mcp.tool()
async def get_category_related_posts(
    ctx: Context,
    topic: str,
    product_name: str,
    category_url: str,
    required_count: int = 3,
    tier1_limit: int = 30
) -> Dict:
    """
    Main entry: returns related posts for given topic/product/category.
    Uses two-tier detection and conservative fallback to avoid wrong-language hits.
    """
    # 1) product language is authoritative
    target_language = extract_language_from_product(product_name)
    print(f"[get_category_related_posts] product_name={product_name} -> target_language={target_language}", file=sys.stderr, flush=True)

    if not target_language:
        return {"error": f"Could not detect language from product: {product_name}", "related_posts": [], "target_language": None}

    # 2) Fetch candidate articles from category (only small set initially)
    category_articles = await fetch_category_articles(category_url, required= tier1_limit if tier1_limit>0 else 30, max_limit=tier1_limit)
    if not category_articles:
        return {"error": f"No articles found at category URL: {category_url}", "related_posts": [], "target_language": target_language}

    # Tier 1: metadata scan
    tier1_matches = []
    tier1_uncertain = []
    tier1_scanned = 0

    for article in category_articles:
        tier1_scanned += 1
        if article['title'].lower() == topic.lower():
            continue

        search_text = f"{article['title']} {article['url']} {article.get('description','')}"
        is_match, confidence = detect_language_from_text(search_text, target_language)

        if is_match:
            article['language'] = target_language
            article['confidence'] = confidence
            article['tier'] = 1
            # treat higher scores as high confidence
            if confidence >= 4:
                tier1_matches.append(article)
            else:
                tier1_uncertain.append(article)

        if len(tier1_matches) >= required_count:
            break

    # If enough high-confidence: return
    if len(tier1_matches) >= required_count:
        final_results = tier1_matches[:required_count]
        # cleanup
        for a in final_results:
            a.pop('confidence', None)
        return {
            "target_language": target_language,
            "product_name": product_name,
            "related_posts": final_results,
            "total_found": len(final_results),
            "scan_stats": {"tier1_scanned": tier1_scanned, "tier2_scanned": 0, "method": "metadata_only"}
        }

    # Tier 2: check uncertain ones by fetching content
    tier2_scanned = 0
    tier2_limit = min(20, len(tier1_uncertain))
    for article in tier1_uncertain[:tier2_limit]:
        if len(tier1_matches) >= required_count:
            break
        tier2_scanned += 1
        content = await fetch_article_content(article['url'])
        if content:
            is_match, confidence = detect_language_from_text(content, target_language)
            if is_match and confidence >= 3:
                article['language'] = target_language
                article['confidence'] = confidence
                article['tier'] = 2
                tier1_matches.append(article)

    # After tier2, if enough, return
    final_results = tier1_matches[:required_count]
    if len(final_results) >= required_count:
        for a in final_results:
            a.pop('confidence', None)
        return {
            "target_language": target_language,
            "product_name": product_name,
            "related_posts": final_results,
            "total_found": len(final_results),
            "scan_stats": {"tier1_scanned": tier1_scanned, "tier2_scanned": tier2_scanned, "method": "content_analysis"}
        }

    # Smart fallback: attempt to validate remaining category articles by fetching content and verifying target language
    used_urls = {a['url'] for a in final_results}
    candidates = [a for a in category_articles if a['url'] not in used_urls and a['title'].lower() != topic.lower()]

    for article in candidates:
        if len(final_results) >= required_count:
            break

        # Try content check to avoid adding clearly wrong-language posts
        content = await fetch_article_content(article['url'])
        if content:
            is_match, confidence = detect_language_from_text(content, target_language)
            # accept weak matches (score >=2) as fallback-preferred
            if is_match and confidence >= 2:
                article['language'] = target_language
                article['tier'] = 3
                article['is_fallback'] = True
                final_results.append(article)
                continue
        # If no content or no match, skip for now

    # Last resort: if still not enough, append remaining articles (but mark them)
    if len(final_results) < required_count:
        for article in candidates:
            if len(final_results) >= required_count:
                break
            if article['url'] in used_urls:
                continue
            article['language'] = 'unknown'
            article['tier'] = 0
            article['is_fallback'] = True
            final_results.append(article)

    # Cleanup confidences before returning
    for a in final_results:
        a.pop('confidence', None)

    return {
        "target_language": target_language,
        "product_name": product_name,
        "related_posts": final_results,
        "total_found": len(final_results),
        "category_url": category_url,
        "scan_stats": {
            "tier1_scanned": tier1_scanned,
            "tier2_scanned": tier2_scanned,
            "method": "content_analysis" if tier2_scanned > 0 else "metadata_only",
            "fallback_used": any(a.get('is_fallback', False) for a in final_results)
        }
    }

# Run the server
if __name__ == "__main__":
    mcp.run()
