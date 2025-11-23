"""
Optimized Two-Tier RSS Reader MCP Server with Topic Relevance
Tier 1: RSS metadata scan (fast) with topic matching
Tier 2: Content fetch (accurate fallback)
"""
from fastmcp import FastMCP, Context
from typing import List, Dict, Optional, Tuple
import httpx
from bs4 import BeautifulSoup
import re
import sys
import requests
from collections import Counter
import math

# Initialize FastMCP server
mcp = FastMCP("Related Links Reader")

# -------------------------
# Topic Relevance Scoring
# -------------------------
STOP_WORDS = {
    'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
    'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
    'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'should',
    'could', 'can', 'may', 'might', 'must', 'shall', 'using', 'use', 'used'
}

def extract_keywords(text: str) -> List[str]:
    """Extract meaningful keywords from text, removing stop words and normalizing"""
    if not text:
        return []
    
    # Convert to lowercase and split
    text = text.lower()
    # Remove special characters but keep + for c++
    text = re.sub(r'[^\w\s\+\-\.]', ' ', text)
    words = text.split()
    
    # Filter stop words and short words
    keywords = [w for w in words if w not in STOP_WORDS and len(w) > 2]
    return keywords

def calculate_topic_similarity(title1: str, title2: str) -> Tuple[float, Dict]:
    """
    Calculate similarity between two titles using keyword overlap and scoring.
    Returns (similarity_score, debug_info)
    """
    keywords1 = extract_keywords(title1)
    keywords2 = extract_keywords(title2)
    
    if not keywords1 or not keywords2:
        return 0.0, {"keywords1": keywords1, "keywords2": keywords2, "common": []}
    
    # Convert to sets for comparison
    set1 = set(keywords1)
    set2 = set(keywords2)
    
    # Find common keywords
    common = set1.intersection(set2)
    
    if not common:
        # Check for partial matches (substring matching for compound words)
        partial_score = 0
        for w1 in set1:
            for w2 in set2:
                if len(w1) >= 4 and len(w2) >= 4:
                    if w1 in w2 or w2 in w1:
                        partial_score += 0.5
        
        if partial_score > 0:
            return partial_score, {
                "keywords1": keywords1,
                "keywords2": keywords2,
                "common": [],
                "partial_matches": partial_score
            }
        
        return 0.0, {"keywords1": keywords1, "keywords2": keywords2, "common": []}
    
    # Calculate Jaccard similarity
    jaccard = len(common) / len(set1.union(set2))
    
    # Calculate weighted score based on keyword importance
    # Give higher weight to exact matches and technical terms
    weighted_score = 0
    technical_terms = {'convert', 'create', 'generate', 'export', 'import', 'parse', 
                      'read', 'write', 'save', 'load', 'download', 'upload', 'render',
                      'pdf', 'png', 'jpeg', 'jpg', 'svg', 'html', 'xml', 'json', 'csv'}
    
    for word in common:
        if word in technical_terms:
            weighted_score += 2.0  # Technical terms get double weight
        else:
            weighted_score += 1.0
    
    # Normalize by the smaller set size
    normalized_score = weighted_score / min(len(set1), len(set2))
    
    # Combine Jaccard and normalized score
    final_score = (jaccard * 0.4) + (normalized_score * 0.6)
    
    return final_score, {
        "keywords1": keywords1,
        "keywords2": keywords2,
        "common": list(common),
        "jaccard": jaccard,
        "weighted": normalized_score,
        "final": final_score
    }

def calculate_composite_score(
    language_score: int,
    topic_similarity: float,
    language_weight: float = 0.4,
    topic_weight: float = 0.6
) -> float:
    """
    Calculate composite score combining language detection and topic relevance.
    
    Args:
        language_score: Raw language detection score (0-10+)
        topic_similarity: Topic similarity score (0-1)
        language_weight: Weight for language component
        topic_weight: Weight for topic component
    
    Returns:
        Composite score (0-10)
    """
    # Normalize language score to 0-1 scale (assume max is 10)
    normalized_lang = min(language_score / 10.0, 1.0)
    
    # Calculate weighted composite
    composite = (normalized_lang * language_weight) + (topic_similarity * topic_weight)
    
    # Scale back to 0-10 for easier interpretation
    return composite * 10

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
    tier1_limit: int = 30,
    topic_weight: float = 0.6,
    min_topic_score: float = 0.15
) -> Dict:
    """
    Main entry: returns related posts for given topic/product/category.
    Uses two-tier detection with both language matching and topic relevance.
    
    Args:
        topic: The title/topic to find related posts for (e.g., "convert png to pdf in Java")
        product_name: Product name containing language info
        category_url: Category page URL to scrape
        required_count: Number of related posts to return
        tier1_limit: Max articles to scan in tier 1
        topic_weight: Weight for topic similarity in composite score (0-1)
        min_topic_score: Minimum topic similarity score to consider (0-1)
    """
    # 1) product language is authoritative
    target_language = extract_language_from_product(product_name)
    print(f"[get_category_related_posts] topic={topic}", file=sys.stderr, flush=True)
    print(f"[get_category_related_posts] product_name={product_name} -> target_language={target_language}", file=sys.stderr, flush=True)

    if not target_language:
        return {"error": f"Could not detect language from product: {product_name}", "related_posts": [], "target_language": None}

    # 2) Fetch candidate articles from category
    category_articles = await fetch_category_articles(category_url, required= tier1_limit if tier1_limit>0 else 30, max_limit=tier1_limit)
    if not category_articles:
        return {"error": f"No articles found at category URL: {category_url}", "related_posts": [], "target_language": target_language}

    # Tier 1: metadata scan with topic matching
    tier1_matches = []
    tier1_uncertain = []
    tier1_scanned = 0

    for article in category_articles:
        tier1_scanned += 1
        
        # Skip if it's the exact same topic
        if article['title'].lower() == topic.lower():
            continue

        # Calculate topic similarity
        topic_sim, topic_debug = calculate_topic_similarity(topic, article['title'])
        
        # Skip if topic similarity is too low
        if topic_sim < min_topic_score:
            print(f"[TIER1] Skipping '{article['title']}' - topic score too low: {topic_sim:.3f}", file=sys.stderr)
            continue

        # Detect language from metadata
        search_text = f"{article['title']} {article['url']} {article.get('description','')}"
        is_match, lang_score = detect_language_from_text(search_text, target_language)

        # Calculate composite score
        composite = calculate_composite_score(lang_score, topic_sim, 
                                              language_weight=1.0-topic_weight, 
                                              topic_weight=topic_weight)

        article['language'] = target_language if is_match else 'unknown'
        article['language_score'] = lang_score
        article['topic_similarity'] = round(topic_sim, 3)
        article['composite_score'] = round(composite, 3)
        article['tier'] = 1
        
        print(f"[TIER1] '{article['title'][:50]}' - Lang:{lang_score} Topic:{topic_sim:.3f} Composite:{composite:.3f}", 
              file=sys.stderr)

        # High confidence if composite score is high
        if composite >= 5.0:  # Threshold for high confidence
            tier1_matches.append(article)
        else:
            tier1_uncertain.append(article)

        if len(tier1_matches) >= required_count:
            break

    # Sort tier1_matches by composite score
    tier1_matches.sort(key=lambda x: x['composite_score'], reverse=True)

    # If enough high-confidence matches: return
    if len(tier1_matches) >= required_count:
        final_results = tier1_matches[:required_count]
        return {
            "target_language": target_language,
            "product_name": product_name,
            "topic": topic,
            "related_posts": final_results,
            "total_found": len(final_results),
            "scan_stats": {
                "tier1_scanned": tier1_scanned, 
                "tier2_scanned": 0, 
                "method": "metadata_with_topic"
            }
        }

    # Tier 2: check uncertain ones by fetching content
    tier2_scanned = 0
    tier2_limit = min(20, len(tier1_uncertain))
    
    # Sort uncertain by composite score before tier 2
    tier1_uncertain.sort(key=lambda x: x['composite_score'], reverse=True)
    
    for article in tier1_uncertain[:tier2_limit]:
        if len(tier1_matches) >= required_count:
            break
        
        tier2_scanned += 1
        content = await fetch_article_content(article['url'])
        
        if content:
            # Re-check language with full content
            is_match, lang_score = detect_language_from_text(content, target_language)
            
            # Recalculate composite with content-based language score
            topic_sim = article['topic_similarity']
            composite = calculate_composite_score(lang_score, topic_sim,
                                                 language_weight=1.0-topic_weight,
                                                 topic_weight=topic_weight)
            
            print(f"[TIER2] '{article['title'][:50]}' - Lang:{lang_score} Topic:{topic_sim:.3f} Composite:{composite:.3f}", 
                  file=sys.stderr)
            
            if composite >= 4.0:  # Slightly lower threshold for tier 2
                article['language'] = target_language if is_match else 'mixed'
                article['language_score'] = lang_score
                article['composite_score'] = round(composite, 3)
                article['tier'] = 2
                tier1_matches.append(article)

    # Sort all matches by composite score
    tier1_matches.sort(key=lambda x: x['composite_score'], reverse=True)
    final_results = tier1_matches[:required_count]

    # If we have enough, return
    if len(final_results) >= required_count:
        return {
            "target_language": target_language,
            "product_name": product_name,
            "topic": topic,
            "related_posts": final_results,
            "total_found": len(final_results),
            "scan_stats": {
                "tier1_scanned": tier1_scanned,
                "tier2_scanned": tier2_scanned,
                "method": "content_with_topic"
            }
        }

    # Smart fallback: validate remaining articles with content check
    used_urls = {a['url'] for a in final_results}
    candidates = [a for a in category_articles if a['url'] not in used_urls and a['title'].lower() != topic.lower()]

    # Add topic similarity to candidates that don't have it yet
    for article in candidates:
        if 'topic_similarity' not in article:
            topic_sim, _ = calculate_topic_similarity(topic, article['title'])
            article['topic_similarity'] = round(topic_sim, 3)
    
    # Sort candidates by topic similarity
    candidates.sort(key=lambda x: x.get('topic_similarity', 0), reverse=True)

    # First pass: try articles with decent topic relevance
    for article in candidates:
        if len(final_results) >= required_count:
            break

        # Only consider articles with some topic relevance
        if article['topic_similarity'] < min_topic_score:
            continue

        # Try content check
        content = await fetch_article_content(article['url'])
        if content:
            is_match, lang_score = detect_language_from_text(content, target_language)
            topic_sim = article['topic_similarity']
            composite = calculate_composite_score(lang_score, topic_sim,
                                                 language_weight=1.0-topic_weight,
                                                 topic_weight=topic_weight)
            
            # Accept with lower threshold in fallback
            if composite >= 2.5:
                article['language'] = target_language if is_match else 'mixed'
                article['language_score'] = lang_score
                article['composite_score'] = round(composite, 3)
                article['tier'] = 3
                article['is_fallback'] = True
                final_results.append(article)

    # CRITICAL: If we still don't have enough articles, add remaining ones regardless of score
    if len(final_results) < required_count:
        print(f"[FALLBACK] Only found {len(final_results)} articles, need {required_count}. Adding remaining articles...", 
              file=sys.stderr, flush=True)
        
        # Get all remaining candidates (including those below min_topic_score)
        remaining_candidates = [a for a in candidates if a['url'] not in {r['url'] for r in final_results}]
        
        # Calculate composite scores for remaining articles (using metadata only to save time)
        for article in remaining_candidates:
            if 'composite_score' not in article:
                # Quick metadata-based scoring
                search_text = f"{article['title']} {article['url']}"
                is_match, lang_score = detect_language_from_text(search_text, target_language)
                topic_sim = article.get('topic_similarity', 0)
                composite = calculate_composite_score(lang_score, topic_sim,
                                                     language_weight=1.0-topic_weight,
                                                     topic_weight=topic_weight)
                
                article['language'] = target_language if is_match else 'unknown'
                article['language_score'] = lang_score
                article['composite_score'] = round(composite, 3)
                article['tier'] = 4  # Tier 4 indicates forced fallback
                article['is_fallback'] = True
        
        # Sort remaining by composite score
        remaining_candidates.sort(key=lambda x: x.get('composite_score', 0), reverse=True)
        
        # Add as many as needed to reach required_count
        needed = required_count - len(final_results)
        final_results.extend(remaining_candidates[:needed])
        
        print(f"[FALLBACK] Added {min(needed, len(remaining_candidates))} articles to reach required count", 
              file=sys.stderr, flush=True)

    # Sort final results by composite score
    final_results.sort(key=lambda x: x.get('composite_score', 0), reverse=True)
    
    # Take top required_count (in case we added extras)
    final_results = final_results[:required_count]

    return {
        "target_language": target_language,
        "product_name": product_name,
        "topic": topic,
        "related_posts": final_results,
        "total_found": len(final_results),
        "category_url": category_url,
        "scan_stats": {
            "tier1_scanned": tier1_scanned,
            "tier2_scanned": tier2_scanned,
            "method": "content_with_topic" if tier2_scanned > 0 else "metadata_with_topic",
            "fallback_used": any(a.get('is_fallback', False) for a in final_results),
            "forced_fallback": any(a.get('tier', 0) == 4 for a in final_results)
        }
    }

# Run the server
if __name__ == "__main__":
    mcp.run()