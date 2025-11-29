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
    context: str = "",
    author: str = ""
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
- **END**: The blog post must end EXACTLY after the {"FAQs section" if not formatted_related else "Read More section"} (no text after)
- **NO EXCEPTIONS**: No introductory text, no concluding remarks, no author notes, no meta-commentary outside the defined structure

### MANDATORY STRUCTURAL REQUIREMENTS:
You MUST include these sections REGARDLESS of the outline:
1. **Introduction section** (H2 header: ## Introduction)
2. **Steps section** (H2 header: ## Steps to [Task])
3. **Conclusion section** (H2 header: ## Conclusion)
4. **FAQs section** (H2 header: ## FAQs)
{"5. **Read More section** (H2 header: ## Read More)" if formatted_related else ""}

{"### READ MORE LINKS TO INCLUDE EXACTLY:" if formatted_related else "### READ MORE SECTION:"}
{formatted_related if formatted_related else "SKIP - No related links provided. Do NOT include Read More section."}

### PROVIDED OUTLINE:
{formatted_outline}

### CRITICAL RULES:
1. **START** with frontmatter - no text before `---`
2. **END** after {"Read More section" if formatted_related else "FAQs section"} - no text after the last {"link" if formatted_related else "FAQ"}
3. Write ONLY the frontmatter and the sections specified below
4. **ALWAYS CREATE Introduction, Steps, Conclusion, and FAQs sections** even if not in outline
{"5. **INCLUDE Read More section** with the provided links" if formatted_related else "5. **DO NOT CREATE Read More section** - no related links available"}
6. DO NOT add any additional sections, notes, or commentary
7. DO NOT add author notes, editor notes, or meta-commentary
8. DO NOT add "Note:", "Remember:", "Important:" or similar annotations
9. **STRICTLY NO CONTENT** before frontmatter or after {"Read More" if formatted_related else "FAQs"} section

### MARKDOWN-SAFE CONTENT REQUIREMENTS (CRITICAL):
All content in frontmatter and body MUST be safe for Hugo/Markdown/YAML:
- **NO Unicode dashes**: Replace em dash (—), en dash (–) with standard hyphen (-)
- **NO Smart quotes**: Replace curly quotes (" " ' ') with straight quotes (" ')
- **NO Special characters**: Replace © → (c), ® → (R), ™ → (TM), • → -, … → ...
- **NO Unescaped colons**: In YAML values (title, description, summary), avoid colons or wrap entire value in quotes
- **NO Line breaks**: In YAML values, keep everything on one line
- **NO Special symbols**: Replace %, &, *, @, #, etc. in YAML with words when possible
- **MANDATORY**: Use only ASCII characters (a-z, A-Z, 0-9) and basic punctuation (. , - " ')
- **In frontmatter strings**: If a value contains special characters, wrap it in double quotes
- **Escape quotes**: If using quotes inside quoted strings, escape them properly

### CHARACTER SANITIZATION RULES:
**Replace these automatically in ALL content:**
- — (em dash) → - (hyphen)
- – (en dash) → - (hyphen)
- " " (curly double quotes) → " (straight quotes)
- ' ' (curly single quotes) → ' (straight quotes)
- … (ellipsis) → ... (three periods)
- © → (c)
- ® → (R)
- ™ → (TM)
- • → -
- ° → degrees
- × → x
- ÷ → /
- Any other Unicode → Remove or replace with ASCII equivalent

### FRONTMATTER YAML SAFETY RULES:
1. **Strings with colons MUST be quoted**: title: "Convert PDF: A Complete Guide"
2. **No line breaks in values**: Keep description, summary, steps on single lines
3. **Escape internal quotes**: Use \\" for quotes inside quoted strings
4. **No trailing colons**: Don't end values with colons
5. **Safe characters only**: Stick to alphanumeric, spaces, hyphens, periods, commas
6. **Test mentally**: Would this break YAML parsing? If yes, fix it.

### FRONTMATTER (MUST BE FIRST - NO TEXT BEFORE THIS):
---
title: "{title}"
seoTitle: "{title}"
description: "[Write compelling 150-160 char meta description - NO colons, NO special chars, NO line breaks]"
date: {current_date}
lastmod: {current_date}
draft: false
url: /{data.get("urlPrefix")}/{url}/
author: "{author}"
summary: "[1-2 sentence summary - NO colons, NO special chars, NO line breaks, wrap in quotes if needed]"
tags: {json.dumps(keywords)}
categories: ["{category}"]
showtoc: true
cover:
    image: images/{url}.png
    alt: "{title}"
    caption: "{title}"
steps:
  - "Step 1: [Clear actionable instruction - NO special chars, NO colons unless quoted]"
  - "Step 2: [Clear actionable instruction - NO special chars, NO colons unless quoted]"
  - "Step 3: [Clear actionable instruction - NO special chars, NO colons unless quoted]"
  - "Step 4: [Clear actionable instruction - NO special chars, NO colons unless quoted]"
  - "Step 5: [Clear actionable instruction - OPTIONAL]"
faqs:
  - q: "[Question - NO special chars, safe punctuation only]"
    a: "[Answer - NO special chars, use product links, safe punctuation only]"
  - q: "[Question - NO special chars, safe punctuation only]"
    a: "[Answer - NO special chars, use product links, safe punctuation only]"
  - q: "[Question - NO special chars, safe punctuation only]"
    a: "[Answer - NO special chars, use product links, safe punctuation only]"
  - q: "[Question - OPTIONAL]"
    a: "[Answer - OPTIONAL]"
---

### FINAL BLOG STRUCTURE (MUST FOLLOW THIS ORDER):
1. **Introduction** (ALWAYS CREATE this section first after frontmatter)
2. **Steps** (ALWAYS CREATE this section with 4-6 actionable steps)
3. **Outline Sections** (Follow the provided outline exactly)
4. **Conclusion** (ALWAYS CREATE this section)
5. **FAQs** (ALWAYS CREATE this section with 3-4 questions)
{"6. **Read More** (ALWAYS include this section last)" if formatted_related else ""}

### WRITING INSTRUCTIONS:
- **Start immediately** with frontmatter above (fill bracketed parts)
- **Always begin** with ## Introduction section after frontmatter
- **Always include** ## Steps section after Introduction
- Follow the provided outline EXACTLY for the main content
- **Always include** ## Conclusion section
- **Always include** ## FAQs section with 3-4 relevant questions
{"- **Always include** ## Read More section last" if formatted_related else "- **DO NOT include** Read More section (no related links provided)"}
- Write 600-800 words total (excluding frontmatter, steps, and FAQs)
- Use clean Markdown with H2/H3 headers
- Include keywords naturally throughout
- DO NOT add extra content not in the outline
- **Use only markdown-safe characters throughout entire content**

### CONTENT STRUCTURE:
- **Introduction** = H2 header (## Introduction) with 2-3 paragraphs
- **Steps** = H2 header (## Steps to [Task Name]) with 4-6 numbered steps
- Outline items = H2/H3 headers as specified
- **Conclusion** = H2 header (## Conclusion) with 2-3 paragraphs
- **FAQs** = H2 header (## FAQs) with 3-4 Q&A pairs
{"- **Read More** = H2 header (## Read More) with provided links" if formatted_related else ""}
- Complete paragraphs required for all sections
- Include relevant examples/code where appropriate
- **All content must use markdown-safe characters only**

### STEPS SECTION REQUIREMENTS:
- Create 4-6 clear, actionable steps to accomplish the task described in the title
- Steps should be technical and implementation-focused
- Each step should be a complete, actionable instruction
- Steps should follow a logical progression from setup to completion
- Use technical terminology appropriate to the product/platform
- **Steps must use only markdown-safe characters**
- Steps MUST be included in both:
  1. **Frontmatter** (in YAML format as a list - quoted strings)
  2. **Content section** (as markdown H2 section after Introduction)

### STEPS CONTENT FORMAT:
## Steps to [Task Name Based on Title]

1. **[Step 1 summary]**: [Brief explanation - markdown-safe chars only]
2. **[Step 2 summary]**: [Brief explanation - markdown-safe chars only]
3. **[Step 3 summary]**: [Brief explanation - markdown-safe chars only]
4. **[Step 4 summary]**: [Brief explanation - markdown-safe chars only]
5. **[Step 5 summary - OPTIONAL]**: [Brief explanation - markdown-safe chars only]
6. **[Step 6 summary - OPTIONAL]**: [Brief explanation - markdown-safe chars only]

### FAQs SECTION REQUIREMENTS:
- Create 3-4 frequently asked questions relevant to the topic
- Questions should cover common user concerns, technical details, or best practices
- Answers should be detailed (2-4 sentences each)
- Include product links in answers where appropriate using format: `[Product Name](URL)`
- Questions should be practical and directly related to the blog topic
- **FAQs must use only markdown-safe characters**
- FAQs MUST be included in both:
  1. **Frontmatter** (in YAML format as shown above - quoted strings)
  2. **Content section** (as markdown H2 section {"before Read More" if formatted_related else "as the FINAL section"})

### FAQs CONTENT FORMAT:
## FAQs

**Q: [First question - markdown-safe chars only]**  
A: [Detailed answer - markdown-safe chars only, with links if applicable]

**Q: [Second question - markdown-safe chars only]**  
A: [Detailed answer - markdown-safe chars only, with links if applicable]

**Q: [Third question - markdown-safe chars only]**  
A: [Detailed answer - markdown-safe chars only, with links if applicable]

**Q: [Fourth question - OPTIONAL]**  
A: [Detailed answer - OPTIONAL]

{'''### READ MORE SECTION RULES:
At the end of the article, include this EXACT section:

## Read More
''' + formatted_related + '''

(Use EXACT titles and URLs provided. Do NOT change them.)''' if formatted_related else '''### READ MORE SECTION:
**DO NOT INCLUDE** - No related links provided. The blog MUST end after the FAQs section.'''}

### LINK FORMAT:
- Product references: `[Product Name](URL)`
- No naked URLs allowed
- At least one product link required in main content
- Links are markdown-safe by default

### CODE FORMAT (if needed):
<!--[CODE_SNIPPET_START]-->
```language
# Code here - can use any characters inside code blocks
```
<!--[CODE_SNIPPET_END]-->

### STRICTLY ENFORCED BOUNDARIES:
- **BEGINNING**: First character must be `-` of frontmatter (no spaces, no text before)
- **INTRODUCTION**: Must be first content section after frontmatter
- **STEPS**: Must be included after Introduction
- **CONCLUSION**: Must be included before FAQs section
- **FAQs**: Must be included {"before Read More section" if formatted_related else "as the FINAL section"}
{"- **READ MORE**: Must be included as the FINAL section" if formatted_related else ""}
- **ENDING**: Last character must be after the final {"link in Read More section" if formatted_related else "FAQ answer"}
- **ABSOLUTELY NO CONTENT** outside these boundaries
- **STOP WRITING IMMEDIATELY** after the {"Read More" if formatted_related else "FAQs"} section

### OUTPUT REQUIREMENTS:
- Complete markdown file starting with frontmatter
- Always includes Introduction, Steps, Conclusion, and FAQs sections
{"- Always includes Read More section with provided links" if formatted_related else "- Does NOT include Read More section (no related links)"}
- Steps in both frontmatter (YAML list - quoted) and content (Markdown numbered list)
- FAQs in both frontmatter (YAML - quoted) and content (Markdown)
- **ALL content uses only markdown-safe ASCII characters**
- **NO Unicode characters that break YAML/Hugo rendering**
- Ending after {"Read More" if formatted_related else "FAQs"} section
- No trailing whitespace, comments, or additional text
- Pure markdown content only

### VIOLATION PREVENTION:
- If Introduction, Steps, Conclusion, or FAQs missing → OUTPUT IS INVALID
{"- If Read More section missing → OUTPUT IS INVALID" if formatted_related else "- If Read More section present → OUTPUT IS INVALID"}
- If Steps not in frontmatter → OUTPUT IS INVALID
- If FAQs not in frontmatter → OUTPUT IS INVALID
- If any text before frontmatter or after {"Read More" if formatted_related else "FAQs"} → OUTPUT IS INVALID
- If outline sections skipped → OUTPUT IS INVALID
- **If Unicode/special characters in frontmatter → OUTPUT IS INVALID**
- **If unquoted YAML values contain colons → OUTPUT IS INVALID**
- **If line breaks in YAML string values → OUTPUT IS INVALID**

### PRE-SUBMISSION CHECKLIST:
Before returning the blog post, verify:
- [ ] No em/en dashes (— –) anywhere - use hyphens (-)
- [ ] No curly quotes (" " ' ') - use straight quotes (" ')
- [ ] No special Unicode characters
- [ ] All YAML values with colons are quoted
- [ ] No line breaks in frontmatter string values
- [ ] All steps are quoted in frontmatter
- [ ] All FAQ questions and answers are properly formatted in YAML
- [ ] Content ends exactly after {"Read More" if formatted_related else "FAQs"} section
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
    4. Remove or replace any characters that break Hugo/Markdown rendering:
       - Replace Unicode dashes (\\u2013, \\u2014, em dash, en dash) with standard hyphens (-)
       - Replace smart quotes (\\u201c, \\u201d, \\u2018, \\u2019) with straight quotes (' or ")
       - Replace ellipsis character (\\u2026) with three periods (...)
       - Remove any other Unicode characters that could break YAML frontmatter
       - Ensure all characters are safe for Hugo YAML frontmatter rendering
    5. Return the filtered and refined keywords in the **exact structure as you received** (e.g., primary, secondary, long_tail).
    
    **Character Replacement Rules:**
    - \\u2013 (en dash) → - (hyphen)
    - \\u2014 (em dash) → - (hyphen)
    - \\u201c, \\u201d (curly double quotes) → " (straight double quote)
    - \\u2018, \\u2019 (curly single quotes) → ' (straight single quote)
    - \\u2026 (ellipsis) → ... (three periods)
    - Any other problematic Unicode → Remove or replace with ASCII equivalent
    
    **CRITICAL OUTPUT FORMAT REQUIREMENT:**
    - You MUST return ONLY valid JSON format
    - Use DOUBLE QUOTES for all strings (not single quotes)
    - Do NOT return Python dict format with single quotes
    - Your response must be parseable by json.loads() without any modifications
    - Example of CORRECT format: {{"primary": ["keyword1", "keyword2"]}}
    - Example of INCORRECT format: {{'primary': ['keyword1', 'keyword2']}}
    
    Return ONLY the JSON object with no additional text, explanation, or markdown formatting.
    Ensure all output keywords are Hugo/YAML-safe and will render correctly in frontmatter.
"""