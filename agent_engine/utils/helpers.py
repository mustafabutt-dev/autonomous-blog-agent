import re, ast, json, sys
from datetime import datetime
import requests

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


def sanitize_for_hugo(text):
    """Remove or replace characters that break Hugo/Markdown rendering"""
    if not text:
        return text
    
    replacements = {
        '\u2013': '-',      # en dash
        '\u2014': '-',      # em dash
        '\u2015': '-',      # horizontal bar
        '\u2212': '-',      # minus sign
        '\u201c': '"',      # left double quote
        '\u201d': '"',      # right double quote
        '\u2018': "'",      # left single quote
        '\u2019': "'",      # right single quote
        '\u2026': '...',    # ellipsis
        '\u00a0': ' ',      # non-breaking space
        '\u200b': '',       # zero-width space
        '\u200c': '',       # zero-width non-joiner
        '\u200d': '',       # zero-width joiner
        '\ufeff': '',       # zero-width no-break space (BOM)
    }
    
    result = text
    for old, new in replacements.items():
        result = result.replace(old, new)
    
    # Remove any remaining non-ASCII characters that might cause issues
    # (optional - only if you want strict ASCII)
    # result = result.encode('ascii', 'ignore').decode('ascii')
    
    return result

def sanitize_keywords(keywords_dict):
    """Recursively sanitize all keyword strings in the structure"""
    if isinstance(keywords_dict, dict):
        return {k: sanitize_keywords(v) for k, v in keywords_dict.items()}
    elif isinstance(keywords_dict, list):
        return [sanitize_keywords(item) for item in keywords_dict]
    elif isinstance(keywords_dict, str):
        return sanitize_for_hugo(keywords_dict)
    else:
        return keywords_dict

def parse_keywords_response(content):
    """Safely parse keywords from MCP response with multiple fallback strategies"""
    
    # Strategy 1: Direct dict access
    if hasattr(content, "data") and isinstance(content.data, dict):
        return content.data
    
    # Strategy 2: Parse text content
    if hasattr(content, "text") and content.text:
        text = content.text.strip()
        
        # Remove markdown code blocks
        if text.startswith("```"):
            parts = text.split("```")
            if len(parts) >= 2:
                text = parts[1]
                # Remove language identifier (json, python, etc.)
                if text.startswith(("json", "python", "py")):
                    text = text.split("\n", 1)[1] if "\n" in text else text[4:]
        
        text = text.strip()
        
        # Try multiple parsing strategies
        strategies = [
            # Standard JSON
            lambda: json.loads(text),
            # Python literal (handles single quotes)
            lambda: ast.literal_eval(text),
            # JSON with relaxed parsing (allows trailing commas, comments)
            lambda: json.loads(re.sub(r',(\s*[}\]])', r'\1', text)),
            # Remove any leading/trailing non-JSON text
            lambda: json.loads(re.search(r'\{.*\}', text, re.DOTALL).group())
        ]
        
        for strategy in strategies:
            try:
                return strategy()
            except (json.JSONDecodeError, ValueError, SyntaxError, AttributeError):
                continue
        
        # If all strategies fail, log the raw text for debugging
        print(f"PARSE ERROR - Raw text: {repr(text)}")
        raise ValueError(f"Unable to parse keywords response: {text[:200]}...")
    
    raise ValueError("No valid content found in response")

def extract_first_topic(response: dict) -> dict:
    # Ensure 'topics' exists and has at least one item
    topics = response.get("topics", [])
    if not topics:
        return {}
    
    first_topic = topics[0]
    
    # Extract data
    topic_title = first_topic.get("title", "")
    primary_keywords = [first_topic.get("primary_keyword", "")] if first_topic.get("primary_keyword") else []
    secondary_keywords = first_topic.get("supporting_keywords", [])
    topic_outline = first_topic.get("outline", [])
    
    return {
        "topic": topic_title,
        "keywords": {
            "primary": primary_keywords,
            "secondary": secondary_keywords
        },
        "outline": topic_outline
    }


def extract_all_complete_code_snippets(markdown_content: str) -> dict:
    """
    Extract ALL complete code snippets from Complete Code Example sections
    Stores the exact matched text for replacement later
    Returns:
        dict: {
            "task1": {
                "language": "java", 
                "code": "...", 
                "task_name": "...",
                "matched_text": "<!--[CODE_SNIPPET_START_COMPLETE]-->...<!--[CODE_SNIPPET_END_COMPLETE]-->",
                "filename": "convert_ppt_to_html.java"
            }
        }
    """
    import re
    
    section_pattern = r'##\s+(.+?)\s*-\s*Complete Code Example(.*?)(?=##|\Z)'
    sections = re.finditer(section_pattern, markdown_content, re.DOTALL | re.IGNORECASE)
    
    snippets = {}
    snippet_index = 1
    
    for section in sections:
        task_name = section.group(1).strip()
        section_content = section.group(2)
        
        matched_text = None
        language = None
        code = None
        
        # Try COMPLETE_CODE_SNIPPET tags first
        code_pattern_complete = r'<!--\[CODE_SNIPPET_START_COMPLETE\]-->\s*```([\w#+-]*)\s*(.*?)\s*```\s*<!--\[CODE_SNIPPET_END_COMPLETE\]-->'
        match = re.search(code_pattern_complete, section_content, re.DOTALL)
        
        if match:
            matched_text = match.group(0)
            language = match.group(1).strip() or 'text'
            code = match.group(2).strip()
        
        # Fallback to regular CODE_SNIPPET tags
        if not match:
            code_pattern_regular = r'<!--\[CODE_SNIPPET_START\]-->\s*```([\w#+-]*)\s*(.*?)\s*```\s*<!--\[CODE_SNIPPET_END\]-->'
            match = re.search(code_pattern_regular, section_content, re.DOTALL)
            
            if match:
                matched_text = match.group(0)
                language = match.group(1).strip() or 'text'
                code = match.group(2).strip()
        
        # Final fallback: just get first code block without tags
        if not match:
            code_pattern_plain = r'```([\w#+-]*)\s*(.*?)\s*```'
            match = re.search(code_pattern_plain, section_content, re.DOTALL)
            
            if match:
                matched_text = match.group(0)
                language = match.group(1).strip() or 'text'
                code = match.group(2).strip()
        
        if match and matched_text:
            # Create a clean, safe filename
            safe_task_name = re.sub(r'[^\w\s-]', '', task_name)
            safe_task_name = re.sub(r'[-\s]+', '_', safe_task_name)
            safe_task_name = safe_task_name.lower()[:50]
            
            # Get proper file extension
            extension = get_file_extension(language)
            
            key = f"snippet_{snippet_index}_{safe_task_name}"
            filename = f"{safe_task_name}.{extension}"
            
            snippets[key] = {
                "language": language,
                "extension": extension,  # Store extension separately
                "code": code,
                "task_name": task_name,
                "matched_text": matched_text,
                "filename": filename
            }
            snippet_index += 1
    
    return snippets


async def upload_to_gist(
    files_dict: dict,  # {"file1.java": "code1", "file2.py": "code2"}
    description: str = "",
    token: str = "",
    gist_name: str = ""
) -> dict:
    """
    Upload code to GitHub Gist - handles single or multiple files intelligently
    
    Args:
        files_dict: Dictionary of {filename: code_content}
        description: Gist description
        token: GitHub token
        gist_name: Gist owner name
    
    Returns:
        dict: {
            "gist_id": "abc123",
            "shortcodes": {
                "file1.java": "{{< gist ... >}}",
                "file2.py": "{{< gist ... >}}"
            }
        }
    """
    print(f"Uploading {len(files_dict)} file(s) to gist...", flush=True, file=sys.stderr)
    
    # --- Token Check ---
    if not token:
        return {"error": "GITHUB_TOKEN environment variable not set"}
    
    print(f"🔑 GITHUB_TOKEN found", flush=True, file=sys.stderr)
    
    # --- Build files object for gist ---
    gist_files = {
        filename: {"content": content} 
        for filename, content in files_dict.items()
    }
    
    # --- Send Request ---
    response = requests.post(
        "https://api.github.com/gists",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json"
        },
        json={
            "description": description,
            "public": True,
            "files": gist_files
        }
    )
    
    # --- Handle Response ---
    if response.ok:
        gist = response.json()
        gist_id = gist['id']
        
        # Generate shortcodes for each file
        shortcodes = {}
        for file_name in gist['files'].keys():
            shortcodes[file_name] = f'{{{{< gist "{gist_name}" "{gist_id}" "{file_name}" >}}}}'
            print(f"✓ Created shortcode for {file_name}", flush=True, file=sys.stderr)
        
        print(f"✓ Gist created: {gist_id} with {len(shortcodes)} file(s)", flush=True, file=sys.stderr)
        
        return {
            "success": True,
            "gist_id": gist_id,
            "shortcodes": shortcodes,
            "gist_url": gist['html_url']
        }
    
    error_msg = f"Error {response.status_code}: {response.text}"
    print(f"❌ {error_msg}", flush=True, file=sys.stderr)
    return {
        "success": False,
        "error": error_msg
    }

def replace_code_snippets_with_gists(markdown_content: str, snippets: dict, shortcodes_map: dict) -> str:
    """
    Replace all code snippets with their corresponding gist shortcodes
    
    Args:
        markdown_content: Original markdown
        snippets: Output from extract_all_complete_code_snippets()
        shortcodes_map: {filename: gist_shortcode} from gist upload
    
    Returns:
        Updated markdown with gist shortcodes
    """
    updated_content = markdown_content
    
    for key, data in snippets.items():
        filename = data['filename']
        matched_text = data['matched_text']
        
        # Get the corresponding gist shortcode
        if filename in shortcodes_map:
            gist_shortcode = shortcodes_map[filename]
            
            # Replace the matched code block with gist shortcode
            updated_content = updated_content.replace(matched_text, gist_shortcode, 1)
            
            print(f"✓ Replaced {filename} with gist", flush=True, file=sys.stderr)
        else:
            print(f"⚠ No gist found for {filename}", flush=True, file=sys.stderr)
    
    return updated_content


def get_file_extension(language: str) -> str:
    """
    Map code language to proper file extension
    
    Args:
        language: Language identifier from code block (e.g., 'java', 'csharp', 'python')
    
    Returns:
        File extension (e.g., 'java', 'cs', 'py')
    """
    language = language.lower().strip()
    
    # Language to extension mapping
    extension_map = {
        # Java
        'java': 'java',
        
        # C#/.NET
        'csharp': 'cs',
        'cs': 'cs',
        'c#': 'cs',
        'dotnet': 'cs',
        '.net': 'cs',
        
        # Python
        'python': 'py',
        'py': 'py',
        
        # JavaScript/TypeScript
        'javascript': 'js',
        'js': 'js',
        'typescript': 'ts',
        'ts': 'ts',
        
        # C/C++
        'c': 'c',
        'cpp': 'cpp',
        'c++': 'cpp',
        
        # Web
        'html': 'html',
        'css': 'css',
        'php': 'php',
        
        # Ruby
        'ruby': 'rb',
        'rb': 'rb',
        
        # Go
        'go': 'go',
        'golang': 'go',
        
        # Rust
        'rust': 'rs',
        'rs': 'rs',
        
        # Swift
        'swift': 'swift',
        
        # Kotlin
        'kotlin': 'kt',
        'kt': 'kt',
        
        # Shell/Bash
        'bash': 'sh',
        'sh': 'sh',
        'shell': 'sh',
        
        # SQL
        'sql': 'sql',
        
        # XML/JSON/YAML
        'xml': 'xml',
        'json': 'json',
        'yaml': 'yaml',
        'yml': 'yml',
        
        # Default fallback
        'text': 'txt',
        '': 'txt'
    }
    
    return extension_map.get(language, language or 'txt')