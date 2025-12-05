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
3. **Complete Code Example section(s)** (H2 header: ## [Task] - Complete Code Example) - MUST include full working code for EACH task in title
4. **Conclusion section** (H2 header: ## Conclusion)
5. **FAQs section** (H2 header: ## FAQs)
{"6. **Read More section** (H2 header: ## Read More)" if formatted_related else ""}

{"### READ MORE LINKS TO INCLUDE EXACTLY:" if formatted_related else "### READ MORE SECTION:"}
{formatted_related if formatted_related else "SKIP - No related links provided. Do NOT include Read More section."}

### PROVIDED OUTLINE:
{formatted_outline}

### CONTEXT RESOURCES (MUST USE):
The context above contains important resource URLs including:
- Product documentation links
- API reference pages
- Category pages
- Related product pages
- Download/installation pages

**MANDATORY LINKING REQUIREMENTS:**
1. You MUST include at least 2-3 contextual links from the provided resources in your content
2. Link naturally within paragraphs where relevant (not just in FAQs)
3. Use descriptive anchor text, not "click here" or naked URLs
4. Prioritize linking to:
   - Documentation when explaining features
   - API references when discussing technical implementation
   - Category pages when mentioning product categories
   - Download pages when discussing installation/setup
5. Links should enhance the reader's understanding and provide paths for deeper exploration

### CRITICAL RULES:
1. **START** with frontmatter - no text before `---`
2. **END** after {"Read More section" if formatted_related else "FAQs section"} - no text after the last {"link" if formatted_related else "FAQ"}
3. Write ONLY the frontmatter and the sections specified below
4. **ALWAYS CREATE Introduction, Steps, Complete Code Example(s), Conclusion, and FAQs sections** even if not in outline
{"5. **INCLUDE Read More section** with the provided links" if formatted_related else "5. **DO NOT CREATE Read More section** - no related links available"}
6. DO NOT add any additional sections, notes, or commentary
7. DO NOT add author notes, editor notes, or meta-commentary
8. DO NOT add "Note:", "Remember:", "Important:" or similar annotations
9. **STRICTLY NO CONTENT** before frontmatter or after {"Read More" if formatted_related else "FAQs"} section
10. **MUST include contextual links from provided resources throughout the content**
11. **ALL code snippets MUST be wrapped with <!--[CODE_SNIPPET_START]--> and <!--[CODE_SNIPPET_END]--> tags**
12. **If title contains MULTIPLE tasks, create SEPARATE Complete Code Example sections for EACH task**

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
2. **Steps** (ALWAYS CREATE this section with 4-6 actionable steps, can include code snippets)
3. **Outline Sections** (Follow the provided outline exactly, can include code snippets with explanations)
4. **Complete Code Example(s)** (ALWAYS CREATE - one section per task mentioned in title)
   - If single task: ONE Complete Code Example section
   - If multiple tasks: MULTIPLE Complete Code Example sections (one for each task)
5. **Conclusion** (ALWAYS CREATE this section)
6. **FAQs** (ALWAYS CREATE this section with 3-4 questions)
{"7. **Read More** (ALWAYS include this section last)" if formatted_related else ""}

### WRITING INSTRUCTIONS:
- **Start immediately** with frontmatter above (fill bracketed parts)
- **Always begin** with ## Introduction section after frontmatter
- **Always include** ## Steps section after Introduction
- Follow the provided outline EXACTLY for the main content
- **Always include** Complete Code Example section(s) before Conclusion - ONE section per task in title
- **Always include** ## Conclusion section
- **Always include** ## FAQs section with 3-4 relevant questions
{"- **Always include** ## Read More section last" if formatted_related else "- **DO NOT include** Read More section (no related links provided)"}
- Write 600-800 words total (excluding frontmatter, steps, code examples, and FAQs)
- Use clean Markdown with H2/H3 headers
- Include keywords naturally throughout
- DO NOT add extra content not in the outline
- **Use only markdown-safe characters throughout entire content**
- **MUST include 2-3+ contextual links from provided context resources**
- **ALL code snippets MUST use <!--[CODE_SNIPPET_START]--> and <!--[CODE_SNIPPET_END]--> tags**

### CONTENT STRUCTURE:
- **Introduction** = H2 header (## Introduction) with 2-3 paragraphs (include at least 1 contextual link)
- **Steps** = H2 header (## Steps to [Task Name]) with 4-6 numbered steps (include contextual links where relevant, may include code snippets)
- Outline items = H2/H3 headers as specified (include contextual links naturally, may include code snippets with explanations)
- **Complete Code Example(s)** = H2 header(s) (## [Specific Task] - Complete Code Example) with full working code wrapped in tags - ONE section per task
- **Conclusion** = H2 header (## Conclusion) with 2-3 paragraphs (include at least 1 contextual link)
- **FAQs** = H2 header (## FAQs) with 3-4 Q&A pairs (include contextual links in answers)
{"- **Read More** = H2 header (## Read More) with provided links" if formatted_related else ""}
- Complete paragraphs required for all sections
- Include relevant examples/code where appropriate
- **All content must use markdown-safe characters only**
- **Contextual links must be naturally integrated, not forced**

### CODE SNIPPET REQUIREMENTS (CRITICAL):
**EVERY code snippet MUST follow this exact format:**

<!--[CODE_SNIPPET_START]-->
```language
// Your code here
// Can be partial or full code
```
<!--[CODE_SNIPPET_END]-->

**Rules for code snippets:**
- **MANDATORY**: Wrap ALL code blocks with <!--[CODE_SNIPPET_START]--> and <!--[CODE_SNIPPET_END]-->
- In Steps section: Can include partial code snippets with explanations
- In Outline sections: Can include code chunks broken down for explanation
- In Complete Code Example section(s): MUST include the FULL, working, copy-paste ready code
- Always specify the language (python, javascript, java, csharp, etc.)
- Include comments where helpful
- Code inside blocks can use any characters (not restricted to ASCII)

### COMPLETE CODE EXAMPLE SECTION (MANDATORY):
This section MUST appear after outline sections and before Conclusion.

**MULTIPLE TASKS HANDLING:**
- If title contains ONE task (e.g., "Convert PDF to PNG"): Create ONE Complete Code Example section
- If title contains MULTIPLE tasks (e.g., "Convert PDF to PNG and JPG"): Create SEPARATE Complete Code Example sections for EACH task
- Parse the title to identify all tasks (look for "and", "or", conjunctions, multiple formats mentioned)
- Each task gets its own dedicated Complete Code Example section

**Format for SINGLE task:**
## [Task from Title] - Complete Code Example

Example: "## Convert PDF to PNG - Complete Code Example"

**Format for MULTIPLE tasks:**
## [First Task] - Complete Code Example
[Full code for first task]

## [Second Task] - Complete Code Example
[Full code for second task]

## [Third Task] - Complete Code Example (if applicable)
[Full code for third task]

**Examples:**
- Title: "Convert PDF to PNG and JPG" → Create 2 sections:
  - "## Convert PDF to PNG - Complete Code Example"
  - "## Convert PDF to JPG - Complete Code Example"
  
- Title: "Convert DOCX to PDF, HTML, and Markdown" → Create 3 sections:
  - "## Convert DOCX to PDF - Complete Code Example"
  - "## Convert DOCX to HTML - Complete Code Example"
  - "## Convert DOCX to Markdown - Complete Code Example"

- Title: "Convert PDF to PNG" → Create 1 section:
  - "## Convert PDF to PNG - Complete Code Example"

**Structure for each Complete Code Example section:**

[1-2 sentence introduction explaining what this specific code does]

<!--[COMPLETE_CODE_SNIPPET_START]-->
```language
// Full working code for THIS specific task
// Include all necessary imports, initialization, and implementation
// This should be production-ready or near-production quality
// Must be complete - no placeholders like "// ... rest of code"
```
<!--[COMPLETE_CODE_SNIPPET_END]-->

[Optional: 1-2 sentences explaining how to run or use this code]

**Requirements for EACH Complete Code Example:**
- Must be FULL working code for that specific task (no partial snippets)
- Must be copy-paste ready (no "..." or placeholders)
- Must include all imports/dependencies needed for that task
- Must include proper initialization and error handling
- Should be well-commented for clarity
- Must focus on ONE specific task per section
- Must be wrapped in <!--[COMPLETE_CODE_SNIPPET_START]--> and <!--[COMPLETE_CODE_SNIPPET_END]-->
- Each section is independent and can be used standalone
- If title has multiple tasks, each gets its own complete, standalone code example

### CONTEXTUAL LINKING GUIDELINES:
**When to link to documentation:**
- "Learn more about [feature] in the [documentation](URL)"
- "For detailed API specifications, see the [API reference](URL)"
- "Check out the [complete guide](URL) for advanced features"

**When to link to category pages:**
- "Explore more [category] solutions at [Category Page](URL)"
- "This is part of our [Product Category](URL) offerings"

**When to link to download/installation:**
- "Get started by [downloading the SDK](URL)"
- "Visit our [installation guide](URL) for setup instructions"

**Link placement best practices:**
- Integrate links naturally within sentences
- Use descriptive anchor text that tells readers what they'll find
- Place links where readers would logically want more information
- Don't cluster multiple links in one sentence unless necessary
- Ensure links add value and aren't just inserted for SEO

### STEPS SECTION REQUIREMENTS:
- Create 4-6 clear, actionable steps to accomplish the task described in the title
- Steps should be technical and implementation-focused
- Each step should be a complete, actionable instruction
- Steps should follow a logical progression from setup to completion
- Use technical terminology appropriate to the product/platform
- **Steps must use only markdown-safe characters**
- **Include contextual links in steps where relevant (setup, configuration, API calls)**
- **Can include partial code snippets in steps** (wrapped in tags) to illustrate specific actions
- Steps MUST be included in both:
  1. **Frontmatter** (in YAML format as a list - quoted strings)
  2. **Content section** (as markdown H2 section after Introduction)

### STEPS CONTENT FORMAT:
## Steps to [Task Name Based on Title]

1. **[Step 1 summary]**: [Brief explanation - markdown-safe chars only, include link if relevant]
   
   [Optional code snippet if needed]
   <!--[CODE_SNIPPET_START]-->
```language
   // Step-specific code
```
   <!--[CODE_SNIPPET_END]-->

2. **[Step 2 summary]**: [Brief explanation - markdown-safe chars only, include link if relevant]

3. **[Step 3 summary]**: [Brief explanation - markdown-safe chars only, include link if relevant]

4. **[Step 4 summary]**: [Brief explanation - markdown-safe chars only, include link if relevant]

5. **[Step 5 summary - OPTIONAL]**: [Brief explanation - markdown-safe chars only]

6. **[Step 6 summary - OPTIONAL]**: [Brief explanation - markdown-safe chars only]

### FAQs SECTION REQUIREMENTS:
- Create 3-4 frequently asked questions relevant to the topic
- Questions should cover common user concerns, technical details, or best practices
- Answers should be detailed (2-4 sentences each)
- **MUST include contextual links in FAQ answers** using format: `[Resource Name](URL)`
- Questions should be practical and directly related to the blog topic
- **FAQs must use only markdown-safe characters**
- FAQs MUST be included in both:
  1. **Frontmatter** (in YAML format as shown above - quoted strings)
  2. **Content section** (as markdown H2 section {"before Read More" if formatted_related else "as the FINAL section"})

### FAQs CONTENT FORMAT:
## FAQs

**Q: [First question - markdown-safe chars only]**  
A: [Detailed answer with at least one contextual link - markdown-safe chars only]

**Q: [Second question - markdown-safe chars only]**  
A: [Detailed answer with contextual link if relevant - markdown-safe chars only]

**Q: [Third question - markdown-safe chars only]**  
A: [Detailed answer with contextual link if relevant - markdown-safe chars only]

**Q: [Fourth question - OPTIONAL]**  
A: [Detailed answer - OPTIONAL]

{'''### READ MORE SECTION RULES:
At the end of the article, include this EXACT section:

## Read More
''' + formatted_related + '''

(Use EXACT titles and URLs provided. Do NOT change them.)''' if formatted_related else '''### READ MORE SECTION:
**DO NOT INCLUDE** - No related links provided. The blog MUST end after the FAQs section.'''}

### LINK FORMAT:
- Contextual resource links: `[Descriptive Text](URL from context)`
- Product references: `[Product Name](URL)`
- No naked URLs allowed
- **At least 2-3 contextual links from provided resources required throughout content**
- **At least 1 product/documentation link required in FAQ answers**
- Links are markdown-safe by default

### STRICTLY ENFORCED BOUNDARIES:
- **BEGINNING**: First character must be `-` of frontmatter (no spaces, no text before)
- **INTRODUCTION**: Must be first content section after frontmatter (include contextual link)
- **STEPS**: Must be included after Introduction (include contextual links where relevant, may include code)
- **COMPLETE CODE EXAMPLE(S)**: Must be included before Conclusion (full working code with tags, one section per task)
- **CONCLUSION**: Must be included before FAQs section (include contextual link)
- **FAQs**: Must be included {"before Read More section" if formatted_related else "as the FINAL section"} (include contextual links in answers)
{"- **READ MORE**: Must be included as the FINAL section" if formatted_related else ""}
- **ENDING**: Last character must be after the final {"link in Read More section" if formatted_related else "FAQ answer"}
- **ABSOLUTELY NO CONTENT** outside these boundaries
- **STOP WRITING IMMEDIATELY** after the {"Read More" if formatted_related else "FAQs"} section

### OUTPUT REQUIREMENTS:
- Complete markdown file starting with frontmatter
- Always includes Introduction, Steps, Complete Code Example(s), Conclusion, and FAQs sections
{"- Always includes Read More section with provided links" if formatted_related else "- Does NOT include Read More section (no related links)"}
- Steps in both frontmatter (YAML list - quoted) and content (Markdown numbered list)
- FAQs in both frontmatter (YAML - quoted) and content (Markdown)
- **ALL code snippets wrapped with <!--[CODE_SNIPPET_START]--> and <!--[CODE_SNIPPET_END]-->**
- **Complete Code Example section(s) with full, copy-paste ready code - ONE section per task in title**
- **ALL content uses only markdown-safe ASCII characters**
- **NO Unicode characters that break YAML/Hugo rendering**
- **MINIMUM 2-3 contextual links from provided resources integrated naturally**
- Ending after {"Read More" if formatted_related else "FAQs"} section
- No trailing whitespace, comments, or additional text
- Pure markdown content only

### VIOLATION PREVENTION:
- If Introduction, Steps, Complete Code Example(s), Conclusion, or FAQs missing → OUTPUT IS INVALID
- If title mentions multiple tasks (e.g., "X to Y and Z") and only ONE Complete Code Example exists → OUTPUT IS INVALID
- If title mentions N tasks and fewer than N Complete Code Example sections exist → OUTPUT IS INVALID
{"- If Read More section missing → OUTPUT IS INVALID" if formatted_related else "- If Read More section present → OUTPUT IS INVALID"}
- If Steps not in frontmatter → OUTPUT IS INVALID
- If FAQs not in frontmatter → OUTPUT IS INVALID
- If any code snippet lacks <!--[CODE_SNIPPET_START]--> and <!--[CODE_SNIPPET_END]--> → OUTPUT IS INVALID
- If any Complete Code Example is partial or has placeholders → OUTPUT IS INVALID
- If any text before frontmatter or after {"Read More" if formatted_related else "FAQs"} → OUTPUT IS INVALID
- If outline sections skipped → OUTPUT IS INVALID
- **If Unicode/special characters in frontmatter → OUTPUT IS INVALID**
- **If unquoted YAML values contain colons → OUTPUT IS INVALID**
- **If line breaks in YAML string values → OUTPUT IS INVALID**
- **If fewer than 2 contextual links from provided resources → OUTPUT IS INVALID**
- **If no links in FAQ answers → OUTPUT IS INVALID**

### PRE-SUBMISSION CHECKLIST:
Before returning the blog post, verify:
- [ ] No em/en dashes (— –) anywhere - use hyphens (-)
- [ ] No curly quotes (" " ' ') - use straight quotes (" ')
- [ ] No special Unicode characters
- [ ] All YAML values with colons are quoted
- [ ] No line breaks in frontmatter string values
- [ ] All steps are quoted in frontmatter
- [ ] All FAQ questions and answers are properly formatted in YAML
- [ ] **ALL code snippets wrapped with <!--[CODE_SNIPPET_START]--> and <!--[CODE_SNIPPET_END]-->**
- [ ] **Analyzed title for number of tasks (count "and", "or", multiple formats)**
- [ ] **Created separate Complete Code Example section for EACH task identified**
- [ ] **Each Complete Code Example section has FULL working code (no placeholders)**
- [ ] **Each Complete Code Example section is independently usable**
- [ ] **All Complete Code Example sections appear BEFORE Conclusion**
- [ ] **At least 2-3 contextual links from provided resources included naturally**
- [ ] **At least 1 link in Introduction section**
- [ ] **At least 1 link in Conclusion section**
- [ ] **At least 1 link in FAQ answers**
- [ ] All links use descriptive anchor text (not "click here")
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

def keyword_filter_prompt(PRODUCT_NAME, KEYWORDS, platform) -> str:
    print(f"platform is----- {platform}", flush=True, file=sys.stderr)
    return f"""
    You are an expert in keyword filtering and refinement.
    I have a product called {PRODUCT_NAME} and a list of candidate keywords: {KEYWORDS} and platform: {platform}.
    
    1. Only return keywords that are relevant to the exact product.
    2. Exclude any keyword that refers to other products or cloud offerings if the product is on-premises.
    3. **PLATFORM-SPECIFIC FILTERING:**
       - If platform is NOT 'cloud' (i.e., on-premises/desktop):
         * EXCLUDE all keywords mentioning: REST API, REST APIs, Web API, Cloud API, cURL, HTTP requests, API endpoints, web services, cloud storage, cloud conversion
         * EXCLUDE keywords with terms: "online", "web-based", "cloud", "SaaS", "API call", "REST", "endpoint"
         * KEEP only keywords related to: desktop applications, local libraries, SDK, on-premise tools, offline conversion
       - If platform IS 'cloud':
         * INCLUDE keywords related to REST APIs, cloud services, web APIs, online tools
    4. If any keyword is incomplete, truncated, or has trailing ellipses (e.g., "..."), complete it sensibly while keeping it relevant.
    5. Remove or replace any characters that break Hugo/Markdown rendering:
       - Replace Unicode dashes (\\u2013, \\u2014, em dash, en dash) with standard hyphens (-)
       - Replace smart quotes (\\u201c, \\u201d, \\u2018, \\u2019) with straight quotes (' or ")
       - Replace ellipsis character (\\u2026) with three periods (...)
       - Remove any other Unicode characters that could break YAML frontmatter
       - Ensure all characters are safe for Hugo YAML frontmatter rendering
    6. **MINIMUM KEYWORD REQUIREMENT:**
       - If after filtering, the total number of keywords (primary + secondary + long_tail) is less than 2:
         * Generate 2-5 additional relevant keywords based on the product name and topic
         * Add them to the appropriate category (primary for broad terms, long_tail for specific queries)
         * Ensure generated keywords match the platform type (cloud vs on-premises)
         * Generated keywords must be realistic search queries users would actually type
    7. Return the filtered and refined keywords in the **exact structure as you received** (e.g., primary, secondary, long_tail).
    
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
    - Example of CORRECT format: {{"primary": ["keyword1", "keyword2"], "secondary": [], "long_tail": ["how to keyword3"]}}
    - Example of INCORRECT format: {{'primary': ['keyword1', 'keyword2']}}
    
    **EXAMPLES OF PLATFORM-SPECIFIC FILTERING:**
    
    Example 1 - On-premises platform:
    Input: platform="java", keywords=["Convert PDF using REST API", "PDF to Word Java", "Cloud PDF conversion"]
    Output: {{"primary": ["PDF to Word Java"], "secondary": [], "long_tail": []}}
    (Excluded: REST API and Cloud keywords)
    
    Example 2 - Cloud platform:
    Input: platform="cloud", keywords=["Convert PDF REST API", "PDF to Word online", "Java PDF library"]
    Output: {{"primary": ["Convert PDF REST API", "PDF to Word online"], "secondary": [], "long_tail": []}}
    (Kept: REST API and online keywords, excluded Java library as it's not cloud-related)
    
    Example 3 - Minimum keywords requirement:
    Input: After filtering, only 1 keyword remains
    Output: {{"primary": ["original keyword", "generated relevant keyword 1"], "secondary": [], "long_tail": ["generated long-tail keyword"]}}
    (Added keywords to meet minimum of 2)
    
    Return ONLY the JSON object with no additional text, explanation, or markdown formatting.
    Ensure all output keywords are Hugo/YAML-safe and will render correctly in frontmatter.
"""