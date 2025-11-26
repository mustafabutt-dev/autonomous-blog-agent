import json
from datetime import datetime
import sys, os
from .helpers import slugify
from typing import List, Dict
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils.helpers import format_related_posts
from config import settings

def get_blog_writer_prompt(
    title: str,
    keywords: List[str],
    outline: List[str],
    related_links: List[Dict[str, str]],
    context: str = ""
) -> str:
    """
    Creates a full SEO blog-writing prompt with frontmatter, outline, and
    a final 'Read More' section using the provided related_links.
    """
    url = slugify(title)

    # Parse context fields
    data = {}
    for line in context.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            data[key.strip()] = value.strip()

    category = data.get("Category", "General")
    # Outline formatting
    formatted_outline = "\n".join([f"   {item}" for item in outline])

    # Properly formatted Read More links (SAFE)
    formatted_related = format_related_posts(related_links)

    # Date
    current_date = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S +0000")

    # FULL PROMPT
    return f"""
You are an expert technical blog writer. Your task: Write a detailed, SEO-optimized blog post about "{title}" using the following keywords naturally: {keywords}

{context}

### MANDATORY CONTENT BOUNDARIES:
- **START**: The blog post must begin EXACTLY with the frontmatter (no text before)
- **END**: The blog post must end EXACTLY after the "Read More" section (no text after)
- **NO EXCEPTIONS**: No introductory text, no concluding remarks, no author notes, no meta-commentary outside the defined structure

### MANDATORY STRUCTURAL REQUIREMENTS:
You MUST include these sections REGARDLESS of the outline:
1. **Introduction section** (H2 header: ## Introduction)
2. **Conclusion section** (H2 header: ## Conclusion)  
3. **Read More section** (H2 header: ## Read More)

### READ MORE LINKS TO INCLUDE EXACTLY:
{formatted_related}

### PROVIDED OUTLINE:
{formatted_outline}

### CRITICAL RULES:
1. **START** with frontmatter - no text before `---`
2. **END** after "Read More" section - no text after the last link
3. Write ONLY the frontmatter and the sections specified below
4. **ALWAYS CREATE Introduction and Conclusion sections** even if not in outline
5. DO NOT add any additional sections, notes, or commentary
6. DO NOT add author notes, editor notes, or meta-commentary
7. DO NOT add "Note:", "Remember:", "Important:" or similar annotations
8. **STRICTLY NO CONTENT** before frontmatter or after Read More section

### FRONTMATTER (MUST BE FIRST - NO TEXT BEFORE THIS):
---
title: {title}
seoTitle: {title}
description: [Write a compelling 150-160 character meta description with main keyword]
date: {current_date}
lastmod: {current_date}
draft: false
url: /{data.get("urlPrefix")}/{url}/
author: "Blog Team"
summary: [1-2 sentence summary with keywords]
tags: {json.dumps(keywords)}
categories: ["{category}"]
showtoc: true
cover:
    image: images/{url}.png
    alt: "{title}"
    caption: "{title}"
---

### FINAL BLOG STRUCTURE (MUST FOLLOW THIS ORDER):
1. **Introduction** (ALWAYS CREATE this section first after frontmatter)
2. **Outline Sections** (Follow the provided outline exactly)
3. **Conclusion** (ALWAYS CREATE this section before Read More)
4. **Read More** (ALWAYS include this section last)

### WRITING INSTRUCTIONS:
- **Start immediately** with frontmatter above (fill bracketed parts)
- **Always begin** with ## Introduction section after frontmatter
- Follow the provided outline EXACTLY for the main content
- **Always include** ## Conclusion section before Read More
- Write 600-800 words total (excluding frontmatter)
- Use clean Markdown with H2/H3 headers
- Include keywords naturally throughout
- DO NOT add extra content not in the outline

### CONTENT STRUCTURE:
- **Introduction** = H2 header (## Introduction) with 2-3 paragraphs
- Outline items = H2/H3 headers as specified
- **Conclusion** = H2 header (## Conclusion) with 2-3 paragraphs
- Complete paragraphs required for all sections
- Include relevant examples/code where appropriate

### READ MORE SECTION RULES:
At the end of the article, include this EXACT section:

## Read More
{formatted_related}

(Use EXACT titles and URLs provided. Do NOT change them.)

### LINK FORMAT:
- Product references: `[Product Name](URL)`
- No naked URLs allowed
- At least one product link required in main content

### CODE FORMAT (if needed):
<!--[CODE_SNIPPET_START]-->
```language
# Code here
<!--[CODE_SNIPPET_END]-->
STRICTLY ENFORCED BOUNDARIES:
BEGINNING: First character must be - of frontmatter (no spaces, no text before)

INTRODUCTION: Must be first content section after frontmatter

CONCLUSION: Must be included before Read More section

ENDING: Last character must be after the final link in "Read More" section

ABSOLUTELY NO CONTENT outside these boundaries

STOP WRITING IMMEDIATELY after the Read More section

OUTPUT REQUIREMENTS:
Complete markdown file starting with frontmatter

Always includes Introduction, Conclusion, and Read More sections

Ending after Read More section

No trailing whitespace, comments, or additional text

Pure markdown content only

VIOLATION PREVENTION:

If Introduction or Conclusion missing → OUTPUT IS INVALID

If any text before frontmatter or after Read More → OUTPUT IS INVALID

If outline sections skipped → OUTPUT IS INVALID
"""

def get_title_prompt(topic: str, product: str, keywords: str ) -> str:
      
    return f"""
Generate one short, SEO-optimized blog title.
Topic: "{topic}"
Product: "{product}"
Keywords: {keywords}

CRITICAL RULES:
- Keep under 60 characters
- Sound natural and human-written
- Include 1-2 keywords if possible
- DO NOT change, modify, or alter the product name in any way
- Use the EXACT product name as provided: "{product}"
- Do NOT remove dots, hyphens, or any punctuation from the product name
- Do NOT use colons (:), slashes (/), pipes (|), quotes, or any special characters that might break Markdown
- Return ONLY the plain title text, with no commentary or formatting

PRODUCT NAME PROTECTION:
- Product name must appear exactly as: "{product}"
- No substitutions: ".NET" stays ".NET", not "dotnet" or "NET"
- No removals: "Aspose.CAD" stays "Aspose.CAD", not "Aspose CAD"
- No additions: Don't add extra words to the product name

Return ONLY the plain title text.
"""
def build_outline_prompt(title: str, keywords: list[str]) -> str:
    keyword_list = ", ".join(keywords)

    return f"""
        You are an expert technical SEO content writer.

        TASK:
        Create a **comprehensive, SEO-optimized blog post outline** for the topic:

        Title: **{title}**

        Popular Keywords: {keyword_list}

        STRICT REQUIREMENTS:
        - Generate EXACTLY 4-6 main headings (H2 level)
        - Each main heading MUST be a complete, actionable section title
        - Include 2-3 subheadings (H3 level) under each main heading
        - Headings MUST include the popular keywords naturally
        - Outline must be detailed, hierarchical, and structured
        - Follow proper markdown heading structure
        - Be concise but comprehensive
        - NO introductory text, NO explanations, NO meta-commentary
        - NO content outside the outline structure

        OUTPUT FORMAT:
        Return ONLY a well-formatted markdown outline with exactly {settings.NUMBER_OF_BLOG_SECTIONS} H2 sections.

        ENFORCEMENT:
        - STRICTLY 5-7 main H2 headings - no more, no less
        - Each H2 must be a substantial section that can contain multiple paragraphs
        - NO additional text before or after the outline
        - Start immediately with H1 title
        - End after the last H3 subheading

        EXAMPLE STRUCTURE:
        # Main Title

        ## First Main Heading
        ### First Subheading
        ### Second Subheading

        ## Second Main Heading
        ### First Subheading
        ### Second Subheading

        [Continue with 3-5 more main headings...]

        Now create the outline for: **{title}**
        """

def keyword_filter_prompt(PRODUCT_NAME, KEYWORDS) -> str:
 
    return f"""
    You are an expert in keyword filtering and refinement.
    I have a product called {PRODUCT_NAME} and a list of candidate keywords: {KEYWORDS}.
    1. Only return keywords that are relevant to the exact product.
    2. Exclude any keyword that refers to other products or cloud offerings if the product is on-premises.
    3. If any keyword is incomplete, truncated, or has trailing ellipses (e.g., "..."), complete it sensibly while keeping it relevant.
    4. Return the filtered and refined keywords in the **exact structure as you received** (e.g., primary, secondary, long_tail).

    """