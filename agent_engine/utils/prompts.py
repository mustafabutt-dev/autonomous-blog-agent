import json
from datetime import datetime
import sys
from .helpers import slugify

def get_blog_writer_prompt(title: str, keywords: list, context: str = "") -> str:

    url = slugify(title)
    data = {}
    for line in context.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            data[key.strip()] = value.strip()

    category= data["Category"]

    """
    Returns a detailed prompt for the blog-writer-agent with frontmatter and SEO instructions.
    """
    current_date = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S +0000")

    return f"""
You are an expert technical blog writer. Your task: Write a detailed, SEO-optimized blog post about **"{title}"** using the following keywords naturally: **{keywords}**

{context}

### CRITICAL: Frontmatter Requirements
Your markdown output MUST begin with YAML frontmatter in this EXACT format:
---
title: {title}
seoTitle: {title}
description: [Write a compelling 150-160 character meta description that includes the main keyword]
date: {current_date}
draft: false
url: /{url}/
author: "Blog Team"
summary: [Write a 1-2 sentence summary that captures the essence of the article and includes keywords]
tags: {json.dumps(keywords)}
categories: ["{category}"]
showtoc: true
cover:
  image: images/{url}.png
  alt: "{title}"
  caption: "{title}"
---
### Writing Guidelines:
- Start with the frontmatter EXACTLY as shown above (fill in the bracketed parts)
- After the frontmatter, write the main content
- Maintain a professional, informative, and engaging tone
- The article should be **600–800 words** (not counting frontmatter)
- Use **headings (H2, H3)** to organize sections clearly
- Write in **clean Markdown format**
- Naturally include the keywords without stuffing
- Do **NOT** add any line like "Keywords:" or "Tags:" in the body content
- Avoid repeating the title or keywords excessively

### Content Structure (after frontmatter):
1. **Introduction** (1-2 paragraphs): Hook the reader and introduce the topic
2. **Main Sections** (3-4 sections with H2 headers):
   - Core concepts/features
   - Implementation details
   - Code examples (if applicable)
   - Best practices
3. **Conclusion**: Summarize key points and provide call-to-action

### Link Rules:
- When referring to product names, **insert proper Markdown hyperlinks** using the URLs provided
- Example: `[Aspose.Words for Python](https://products.aspose.com/words/python/)`
- **Do NOT include naked URLs** (e.g., `https://...` on its own line)
- Always link the **product name text**, not just display the URL
- Ensure at least one internal link appears in the content

### Code Examples (if applicable):
You MUST wrap **every code snippet** between the following **HTML comment markers** so it can be identified programmatically later:
<!--[CODE_SNIPPET_START]-->
// Use appropriate syntax highlighting
// Keep examples concise but complete

**Example:**
import aspose.words as aw
doc = aw.Document()
doc.save("output.docx")
<!--[CODE_SNIPPET_END]-->

### Finalization:
Once your blog content is complete (including frontmatter), you **MUST** call the `generate_markdown_file` tool to save your work.

**Rules for tool usage:**
- `generate_markdown_file` must be your **LAST ACTION**
- The content you pass MUST include the complete frontmatter at the beginning
- Pass these parameters:
  - `title`: {title}
  - `content`: The FULL markdown including frontmatter and blog content
  - `keywords_json`: {json.dumps(keywords)}
- Before finishing, always verify that `generate_markdown_file` was successfully called
- You will FAIL if you end without calling `generate_markdown_file`

Remember: The frontmatter is CRITICAL for SEO and content management systems. It must be the FIRST thing in your markdown output.
ask

"""

def get_title_prompt(topic: str, product: str, keywords: str ) -> str:
      
    return f"""
        Generate one short, SEO-optimized blog title.
        Topic: "{topic}"
        Product: "{product}"
        Keywords: {keywords}

        Rules:
        - Keep under 60 characters
        - Sound natural and human-written
        - Include 1–2 keywords if possible
        - Do NOT use colons (:), slashes (/), pipes (|), quotes, or any special characters that might break Markdown
        - Return ONLY the plain title text, with no commentary or formatting
        """