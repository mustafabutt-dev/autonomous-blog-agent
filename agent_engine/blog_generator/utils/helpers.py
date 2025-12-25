import re, ast, json, sys, os
from datetime import datetime
import requests
from typing import Dict, Any, Optional

def parse_markdown_topics(markdown_content: str) -> Dict[str, Any]:
    """
    Parse markdown file containing blog topics and extract metadata.
    
    Args:
        markdown_content: Full markdown content string
        
    Returns:
        Dictionary with metadata (brand, product, platform) and list of topics
    """
    # Extract metadata from header
    brand_match = re.search(r'\*\*Brand:\*\*\s*(.+)', markdown_content)
    product_match = re.search(r'\*\*Product:\*\*\s*(.+)', markdown_content)
    platform_match = re.search(r'\*\*Platform:\*\*\s*(.+)', markdown_content)
    run_id_match = re.search(r'\*\*Run ID:\*\*\s*(.+)', markdown_content)
    
    metadata = {
        "brand": brand_match.group(1).strip() if brand_match else None,
        "product": product_match.group(1).strip() if product_match else None,
        "platform": platform_match.group(1).strip() if platform_match else None,
        "run_id": run_id_match.group(1).strip() if run_id_match else None,
    }
    
    # Extract all topic sections
    topic_pattern = r'##\s+\d+\.\s+(.+?)\n(.*?)(?=##\s+\d+\.|$)'
    topics = []
    
    for match in re.finditer(topic_pattern, markdown_content, re.DOTALL):
        topic_title = match.group(1).strip()
        topic_details = match.group(2).strip()
        
        parsed_topic = parse_topic_details(topic_title, topic_details, metadata)
        topics.append(parsed_topic)
    
    return {
        "metadata": metadata,
        "topics": topics
    }


def parse_topic_details(
    topic_title: str, 
    details: str, 
    metadata: Dict[str, Optional[str]]
) -> Dict[str, Any]:
    """
    Parse individual topic details into structured format.
    
    Args:
        topic_title: Title of the topic
        details: Details string containing persona, angle, keywords, and outline
        metadata: Dictionary containing brand, product, platform info
        
    Returns:
        Dictionary with topic, product, platform, keywords, and outline
    """
    result = {
        "topic": topic_title.strip(),
        "product": metadata.get("product"),
        "platform": metadata.get("platform"),
        "keywords": {
            "primary": [],
            "secondary": []
        },
        "outline": []
    }
    
    # Extract cluster ID
    cluster_match = re.search(r'\*\*Cluster ID:\*\*\s*`([^`]+)`', details)
    if cluster_match:
        result["cluster_id"] = cluster_match.group(1).strip()
    
    # Extract target persona
    persona_match = re.search(r'\*\*Target persona:\*\*\s*(.+?)(?=\n-|\n\*\*|$)', details)
    if persona_match:
        result["target_persona"] = persona_match.group(1).strip()
    
    # Extract angle
    angle_match = re.search(r'\*\*Angle:\*\*\s*(.+?)(?=\n-|\n\*\*|$)', details)
    if angle_match:
        result["angle"] = angle_match.group(1).strip()
    
    # Extract primary keyword
    primary_match = re.search(r'\*\*Primary keyword:\*\*\s*`([^`]+)`', details)
    if primary_match:
        result["keywords"]["primary"].append(primary_match.group(1).strip())
    
    # Extract supporting keywords
    supporting_match = re.search(
        r'\*\*Supporting keywords:\*\*\s*(.+?)(?=\n\n|\n\*\*|$)',
        details,
        re.DOTALL
    )
    
    if supporting_match:
        keywords_text = supporting_match.group(1)
        # Extract all keywords within backticks
        keywords = re.findall(r'`([^`]+)`', keywords_text)
        result["keywords"]["secondary"] = [kw.strip() for kw in keywords if kw.strip()]
    
    # Extract outline items
    outline_match = re.search(
        r'\*\*Suggested outline:\*\*\s*((?:^-\s*.+$\n?)+)',
        details,
        re.MULTILINE
    )
    
    if outline_match:
        outline_text = outline_match.group(1)
        # Extract each bullet point
        outline_items = re.findall(r'^-\s*(.+)$', outline_text, re.MULTILINE)
        result["outline"] = [item.strip() for item in outline_items if item.strip()]
    
    return result

def get_project_root() -> str:
    """
    Resolve project root assuming this file lives under:
    project_root/agent_engine/...
    """
    return os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../../..")
    )

def get_topic_by_index(input_file: str) -> str:
    # Resolve project root
    base_dir = get_project_root()
    print(f"Project root: {base_dir}")

    # If user passed absolute path, use it directly
    if os.path.isabs(input_file):
        file_path = input_file
    else:
        file_path = os.path.join(base_dir, input_file)

    print(f"Looking for file at: {file_path}")

    # Fallback: try relative to current working directory
    if not os.path.exists(file_path):
        cwd_path = os.path.abspath(input_file)
        if os.path.exists(cwd_path):
            file_path = cwd_path
            print(f"Found file via CWD: {file_path}")
        else:
            raise FileNotFoundError(
                f"File not found.\n"
                f"Tried:\n"
                f" - {file_path}\n"
                f" - {cwd_path}"
            )

    # Read file
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    print(f"Successfully read {content}")
    parsed = parse_markdown_topics(content)
    index=1
    if 1 <= index <= len(parsed["topics"]):
        return parsed["topics"][index - 1]
    return None



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
    
    Also converts the title to proper Title Case with smart handling of:
    - Common lowercase words (a, an, the, in, on, at, to, for, with, etc.)
    - Programming terms (C#, .NET, API, SDK, JSON, XML, etc.)
    - Abbreviations and acronyms
    
    Example:
        Input: "convert PDF to jpg in c# with a powerful sdk"
        Output: "Convert PDF to JPG in C# with a Powerful SDK"
    """
    # Remove markdown-breaking characters
    sanitized = re.sub(r'[:`*>|\\/\[\](){}_~]', '', title)
    
    # Replace multiple spaces with a single space
    sanitized = re.sub(r'\s+', ' ', sanitized)
    
    # Trim extra spaces at the ends
    sanitized = sanitized.strip()
    
    # Convert to title case with smart handling
    sanitized = smart_title_case(sanitized)
    
    return sanitized


def smart_title_case(text: str) -> str:
    """
    Converts text to Title Case with intelligent handling of:
    - Articles and prepositions (kept lowercase unless first/last word)
    - Programming language names (C#, .NET, etc.)
    - Common technical abbreviations (API, SDK, JSON, XML, HTML, CSS, etc.)
    - File formats (PDF, JPG, PNG, DOCX, etc.)
    
    Args:
        text: Input string to convert
        
    Returns:
        Title-cased string with proper capitalization
    """
    # Words that should remain lowercase (unless first or last word)
    lowercase_words = {
        'a', 'an', 'the', 'and', 'but', 'or', 'nor', 'for', 'yet', 'so',
        'at', 'by', 'in', 'of', 'on', 'to', 'up', 'as', 'is', 'if',
        'with', 'from', 'into', 'via', 'per', 'vs', 'etc'
    }
    
    # Technical terms and abbreviations that should be uppercase
    uppercase_terms = {
        # Programming languages
        'c#': 'C#',
        'csharp': 'CSharp',
        'vb': 'VB',
        'sql': 'SQL',
        'php': 'PHP',
        'css': 'CSS',
        'html': 'HTML',
        'xml': 'XML',
        'json': 'JSON',
        'yaml': 'YAML',
        
        # Frameworks and platforms
        '.net': '.NET',
        'dotnet': '.NET',
        'nodejs': 'Node.js',
        'node.js': 'Node.js',
        
        # Common abbreviations
        'api': 'API',
        'sdk': 'SDK',
        'rest': 'REST',
        'http': 'HTTP',
        'https': 'HTTPS',
        'url': 'URL',
        'uri': 'URI',
        'ui': 'UI',
        'ux': 'UX',
        'ide': 'IDE',
        'cli': 'CLI',
        'gui': 'GUI',
        'ajax': 'AJAX',
        
        # File formats
        'pdf': 'PDF',
        'jpg': 'JPG',
        'jpeg': 'JPEG',
        'png': 'PNG',
        'gif': 'GIF',
        'svg': 'SVG',
        'bmp': 'BMP',
        'tiff': 'TIFF',
        'docx': 'DOCX',
        'xlsx': 'XLSX',
        'pptx': 'PPTX',
        'txt': 'TXT',
        'csv': 'CSV',
        'md': 'MD',
        'zip': 'ZIP',
        'rar': 'RAR',
        
        # Other technical terms
        'io': 'IO',
        'os': 'OS',
        'db': 'DB',
        'ai': 'AI',
        'ml': 'ML',
        'ocr': 'OCR',
        'oauth': 'OAuth',
        'jwt': 'JWT',
        'seo': 'SEO',
        'crm': 'CRM',
        'erp': 'ERP',
    }
    
    # Split into words
    words = text.split()
    
    if not words:
        return text
    
    result = []
    
    for i, word in enumerate(words):
        is_first = (i == 0)
        is_last = (i == len(words) - 1)
        
        word_lower = word.lower()
        
        # Check if it's a known uppercase term
        if word_lower in uppercase_terms:
            result.append(uppercase_terms[word_lower])
        # Check if it should be lowercase (and not first/last word)
        elif word_lower in lowercase_words and not is_first and not is_last:
            result.append(word_lower)
        # Check if it's already an acronym (all uppercase)
        elif word.isupper() and len(word) > 1:
            result.append(word)  # Keep acronyms as-is
        # Check if it contains numbers and uppercase (e.g., "C++", "MP3")
        elif any(c.isupper() for c in word) and any(c.isdigit() for c in word):
            result.append(word)  # Keep mixed alphanumeric as-is
        # Default: Title case (capitalize first letter)
        else:
            result.append(word.capitalize())
    
    return ' '.join(result)

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

def extract_all_complete_code_snippets(markdown_content: str) -> dict:
    """
    Extract ALL complete code snippets from Complete Code Example sections
    
    Handles multiple tag formats:
    - <!--[CODE_SNIPPET_START_COMPLETE]--> ... <!--[CODE_SNIPPET_END_COMPLETE]-->
    - <!--[COMPLETE_CODE_SNIPPET_START]--> ... <!--[COMPLETE_CODE_SNIPPET_END]-->
    - <!--[CODE_SNIPPET_START]--> ... <!--[CODE_SNIPPET_END]-->
    - Plain code blocks without tags
    
    Handles common edge cases:
    - Tags on same line as code blocks
    - Tags on separate lines
    - Multiple spaces/tabs
    - Windows/Unix line endings
    - Empty lines between tags and code
    - Multiple code blocks in same section
    - Nested code in explanatory text
    """
    import re
    import sys
    
    # Normalize line endings
    markdown_content = markdown_content.replace('\r\n', '\n').replace('\r', '\n')
    
    # Find all "Complete Code Example" sections
    # Handles variations: "Complete Code Example", "- Complete Code Example", etc.
    section_pattern = r'##\s+([^#\n]+?)\s*-?\s*Complete\s+Code\s+Example\s*(.*?)(?=##|\Z)'
    sections = re.finditer(section_pattern, markdown_content, re.DOTALL | re.IGNORECASE)
    
    snippets = {}
    snippet_index = 1
    
    for section in sections:
        task_name = section.group(1).strip()
        section_content = section.group(2)
        
        matched_text = None
        language = None
        code = None
        match = None
        
        print(f"\n🔍 Processing section: {task_name}", flush=True, file=sys.stderr)
        
        # =====================================================================
        # Pattern 1: CODE_SNIPPET_START_COMPLETE tags
        # =====================================================================
        code_pattern_1 = r'<!--\s*\[CODE_SNIPPET_START_COMPLETE\]\s*-->\s*```([\w#+-]*)\s*(.*?)```\s*<!--\s*\[CODE_SNIPPET_END_COMPLETE\]\s*-->'
        match = re.search(code_pattern_1, section_content, re.DOTALL)
        
        if match:
            print("  ✓ Matched: CODE_SNIPPET_START_COMPLETE tags", flush=True, file=sys.stderr)
            matched_text = match.group(0)
            language = match.group(1).strip() or 'text'
            code = match.group(2).strip()
        
        # =====================================================================
        # Pattern 2: COMPLETE_CODE_SNIPPET_START tags (alternate format)
        # =====================================================================
        if not match:
            code_pattern_2 = r'<!--\s*\[COMPLETE_CODE_SNIPPET_START\]\s*-->\s*```([\w#+-]*)\s*(.*?)```\s*<!--\s*\[COMPLETE_CODE_SNIPPET_END\]\s*-->'
            match = re.search(code_pattern_2, section_content, re.DOTALL)
            
            if match:
                print("  ✓ Matched: COMPLETE_CODE_SNIPPET_START tags", flush=True, file=sys.stderr)
                matched_text = match.group(0)
                language = match.group(1).strip() or 'text'
                code = match.group(2).strip()
        
        # =====================================================================
        # Pattern 3: Regular CODE_SNIPPET tags
        # =====================================================================
        if not match:
            code_pattern_3 = r'<!--\s*\[CODE_SNIPPET_START\]\s*-->\s*```([\w#+-]*)\s*(.*?)```\s*<!--\s*\[CODE_SNIPPET_END\]\s*-->'
            match = re.search(code_pattern_3, section_content, re.DOTALL)
            
            if match:
                print("  ✓ Matched: CODE_SNIPPET_START tags", flush=True, file=sys.stderr)
                matched_text = match.group(0)
                language = match.group(1).strip() or 'text'
                code = match.group(2).strip()
        
        # =====================================================================
        # Pattern 4: Plain code block (no tags) - Get LARGEST block
        # =====================================================================
        if not match:
            print("  ⚠ No tags found, searching for plain code blocks...", flush=True, file=sys.stderr)
            
            # Find ALL code blocks in the section
            code_pattern_plain = r'```([\w#+-]*)\s*(.*?)```'
            all_matches = list(re.finditer(code_pattern_plain, section_content, re.DOTALL))
            
            if all_matches:
                # Get the largest code block (most likely the complete example)
                largest_match = max(all_matches, key=lambda m: len(m.group(2)))
                match = largest_match
                matched_text = match.group(0)
                language = match.group(1).strip() or 'text'
                code = match.group(2).strip()
                
                print(f"  ✓ Found {len(all_matches)} code blocks, using largest ({len(code)} chars)", 
                      flush=True, file=sys.stderr)
        
        # =====================================================================
        # Process extracted code
        # =====================================================================
        if match and matched_text and code:
            # Validate code is not empty or whitespace only
            if not code or len(code.strip()) == 0:
                print(f"  ⚠ Code block is empty, skipping", flush=True, file=sys.stderr)
                continue
            
            # Check for minimum code length (avoid extracting placeholder text)
            if len(code) < 20:
                print(f"  ⚠ Code too short ({len(code)} chars), possibly not real code", 
                      flush=True, file=sys.stderr)
                continue
            
            # Create a clean, safe filename
            safe_task_name = re.sub(r'[^\w\s-]', '', task_name)
            safe_task_name = re.sub(r'[-\s]+', '_', safe_task_name)
            safe_task_name = safe_task_name.lower().strip('_')[:50]
            
            # Handle empty task names
            if not safe_task_name:
                safe_task_name = f"code_example_{snippet_index}"
            
            # Get proper file extension
            extension = get_file_extension(language)
            
            key = f"snippet_{snippet_index}_{safe_task_name}"
            filename = f"{safe_task_name}.{extension}"
            
            snippets[key] = {
                "language": language,
                "extension": extension,
                "code": code,
                "task_name": task_name,
                "matched_text": matched_text,
                "filename": filename,
                "code_lines": len(code.split('\n')),
                "has_tags": "<!--[" in matched_text
            }
            
            print(f"  ✅ Extracted snippet {snippet_index}: {filename}", flush=True, file=sys.stderr)
            
            snippet_index += 1
        else:
            print(f"  ❌ No valid code block found in section: {task_name}", flush=True, file=sys.stderr)
    
    # Final summary
    print("\n" + "="*60, file=sys.stderr, flush=True)
    if snippets:
        print(f"✅ Successfully extracted {len(snippets)} code snippet(s)", file=sys.stderr, flush=True)
    else:
        print("⚠️ WARNING: No code snippets extracted from any Complete Code Example sections", 
              file=sys.stderr, flush=True)
    print("="*60 + "\n", file=sys.stderr, flush=True)
    
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
    """
    updated_content = markdown_content
    
    for key, data in snippets.items():
        filename = data['filename']
        matched_text = data['matched_text']
        
        # Get the corresponding gist shortcode
        if filename in shortcodes_map:
            gist_shortcode = shortcodes_map[filename]
            
            # Verify the matched_text exists before replacing
            if matched_text in updated_content:
                # Replace ONLY the matched text with gist shortcode
                updated_content = updated_content.replace(matched_text, gist_shortcode, 1)
                print(f"✓ Replaced {filename} with gist (removed {len(matched_text)} chars)", flush=True, file=sys.stderr)
            else:
                print(f"⚠ Matched text not found in content for {filename}", flush=True, file=sys.stderr)
                print(f"  Looking for: {matched_text[:100]}...", flush=True, file=sys.stderr)
        else:
            print(f"⚠ No gist found for {filename}", flush=True, file=sys.stderr)
    
    return updated_content


def get_file_extension(language: str) -> str:
    """
    Map language identifiers to file extensions
    Handles common variations and edge cases
    """
    language = language.lower().strip()
    
    # Comprehensive language mapping
    language_map = {
        # C# variations
        'csharp': 'cs',
        'cs': 'cs',
        'c#': 'cs',
        'c-sharp': 'cs',
        'dotnet': 'cs',
        '.net': 'cs',
        
        # Java
        'java': 'java',
        
        # Python
        'python': 'py',
        'py': 'py',
        'python3': 'py',
        'py3': 'py',
        
        # JavaScript/TypeScript
        'javascript': 'js',
        'js': 'js',
        'typescript': 'ts',
        'ts': 'ts',
        'node': 'js',
        'nodejs': 'js',
        
        # C/C++
        'cpp': 'cpp',
        'c++': 'cpp',
        'cplusplus': 'cpp',
        'cxx': 'cpp',
        'c': 'c',
        
        # PHP
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
        
        # Scala
        'scala': 'scala',
        
        # Markup/Data
        'html': 'html',
        'css': 'css',
        'xml': 'xml',
        'json': 'json',
        'yaml': 'yaml',
        'yml': 'yml',
        'markdown': 'md',
        'md': 'md',
        
        # Shell
        'shell': 'sh',
        'bash': 'sh',
        'sh': 'sh',
        'zsh': 'sh',
        'powershell': 'ps1',
        'ps1': 'ps1',
        'batch': 'bat',
        'cmd': 'bat',
        
        # Database
        'sql': 'sql',
        'mysql': 'sql',
        'postgresql': 'sql',
        'plsql': 'sql',
        
        # Other
        'vb': 'vb',
        'vbnet': 'vb',
        'perl': 'pl',
        'r': 'r',
        'matlab': 'm',
        'lua': 'lua',
        'text': 'txt',
        'plaintext': 'txt',
        '': 'txt'
    }
    
    return language_map.get(language, 'txt')