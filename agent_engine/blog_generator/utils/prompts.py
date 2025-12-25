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
    author: str = "",
    platform: str = ""
    
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
1. **Introduction content** (NO heading - start directly with content paragraphs after frontmatter)
2. **Prerequisites/Installation section** (H2 header: ## Prerequisites or ## Installation) - ALWAYS CREATE to show SDK setup
3. **Steps section** (H2 header: ## Steps to [Task])
4. **Complete Code Example section(s)** (H2 header: ## [Task] - Complete Code Example) - MUST include full working code for EACH task in title - **ONLY CREATE if you have actual code to include**
5. **Conclusion section** (H2 header: ## Conclusion)
6. **FAQs section** (H2 header: ## FAQs)
{"7. **Read More section** (H2 header: ## Read More)" if formatted_related else ""}

{"### READ MORE LINKS TO INCLUDE EXACTLY:" if formatted_related else "### READ MORE SECTION:"}
{formatted_related if formatted_related else "SKIP - No related links provided. Do NOT include Read More section."}

### PROVIDED OUTLINE:
{formatted_outline}

### CONTEXT RESOURCES (MUST USE):
The context above contains important resource URLs including:
- Product documentation links
- Product page URLs (MANDATORY to use throughout the blog)
- **API reference pages with class/method documentation** (MANDATORY to link when mentioning classes/methods)
- Category pages
- Related product pages
- Download/installation pages

**MANDATORY LINKING REQUIREMENTS:**
1. You MUST include at least 2-3 contextual links from the provided resources in your content
2. **MUST include product page URL** (from context) throughout the blog post where the product is mentioned
3. **MUST link classes, methods, properties, and APIs** to their API reference documentation when mentioned
4. **CRITICAL LINK VALIDATION**: Only use links that are explicitly provided in the context above
5. **NEVER construct or guess API reference URLs** - use only the exact URLs from context
6. **If a class/method API reference URL is not provided in context, do NOT link it** - just mention it as plain text
7. Link naturally within paragraphs where relevant (not just in FAQs)
8. Use descriptive anchor text, not "click here" or naked URLs
9. **NEVER put links inside code literals or backticks** - links must be outside of inline code formatting
10. **CORRECT**: Use the [ImageFormat](URL) property (link is outside backticks)
11. **WRONG**: Use the `[ImageFormat](URL)` property (link inside backticks will not render)
12. **WRONG**: Use the `[ImageFormat](URL).PNG` property (link inside code literal)
13. Prioritize linking to:
   - **Product page when mentioning the product name** (URL must be in context)
   - **API references when mentioning classes, methods, properties** (ONLY if URL is in context)
   - Documentation when explaining features (URL must be in context)
   - Category pages when mentioning product categories (URL must be in context)
   - Download pages when discussing installation/setup (URL must be in context)
14. Links should enhance the reader's understanding and provide paths for deeper exploration
15. **All links MUST work** - if you're unsure about a URL, don't include it

### TERMINOLOGY REQUIREMENTS (CRITICAL):
**SDK vs Library vs API terminology:**
- **Platform-based terminology**: The terminology depends on the platform type specified in the `{platform}` variable
- **If platform is "cloud"**: Use "library" or "API" when referring to the software development kit
  - Examples: "Install the library", "The API provides", "Using the cloud library", "Call the API"
- **If platform is NOT "cloud"**: Use "SDK" when referring to the software development kit
  - Examples: "Install the SDK", "The SDK provides", "Using the SDK"
- **Decision logic**: 
  - Check the `{platform}` variable value
  - If `{platform}` = "cloud" → use "library" or "API"
  - If `{platform}` ≠ "cloud" (e.g., ".NET", "Java", "Python", etc.) → use "SDK"
- This applies to ALL sections: introduction, prerequisites, steps, outline content, code examples, conclusion, FAQs

**PROHIBITED TERMINOLOGY:**
- **NEVER use the word "Framework"** in any context
- Replace "Framework" with alternatives: "SDK", "library", "API", "platform", "toolkit", "solution", "technology"
- Examples:
  - ❌ WRONG: ".NET Framework", "framework provides", "using this framework"
  - ✅ CORRECT: ".NET", "SDK provides" (if not cloud), "library provides" (if cloud), "using this SDK", "using this platform"
- This applies to ALL content: introduction, prerequisites, steps, outline, code examples, conclusion, FAQs

### CRITICAL RULES:
1. **START** with frontmatter - no text before `---`
2. **END** after {"Read More section" if formatted_related else "FAQs section"} - no text after the last {"link" if formatted_related else "FAQ"}
3. Write ONLY the frontmatter and the sections specified below
4. **Introduction content has NO H2 heading** - start directly with paragraphs after frontmatter
5. **ALWAYS CREATE Introduction content, Steps, Conclusion, and FAQs sections** even if not in outline
6. **ONLY CREATE Complete Code Example section(s) if you have actual code snippets to include**
7. **If title mentions multiple tasks, create separate Complete Code Example sections ONLY for tasks where you have code**
8. **NEVER create a "Complete Code Example" heading without actual code content**
{"9. **INCLUDE Read More section** with the provided links" if formatted_related else "9. **DO NOT CREATE Read More section** - no related links available"}
10. DO NOT add any additional sections, notes, or commentary
11. DO NOT add author notes, editor notes, or meta-commentary
12. DO NOT add "Note:", "Remember:", "Important:" or similar annotations
13. **STRICTLY NO CONTENT** before frontmatter or after {"Read More" if formatted_related else "FAQs"} section
14. **MUST include contextual links from provided resources throughout the content**
15. **MUST use product page URL from context whenever product is mentioned**
16. **ALL code snippets MUST be wrapped with <!--[CODE_SNIPPET_START]--> and <!--[CODE_SNIPPET_END]--> tags**
17. **Use "SDK" terminology if platform is NOT "cloud"; use "library" or "API" if platform IS "cloud"**

### TITLE AND SEO REQUIREMENTS (CRITICAL):
**STRICT CHARACTER LIMITS:**
- **Title**: MUST be between 40-60 characters (count every character including spaces)
- **SEO Title**: MUST be between 40-60 characters (count every character including spaces)
- **Meta Description**: MUST be between 140-160 characters (count every character including spaces)
- **Summary**: MUST be between 140-160 characters (count every character including spaces)
- **URL Slug**: Create from title, lowercase, hyphens for spaces, NO product names, MUST use "in" before language/platform

**PRODUCT NAME EXCLUSION (MANDATORY):**
- **DO NOT include product name in title** (e.g., remove "Aspose.Slides", "GroupDocs.Conversion", "Conholdate.Total")
- **DO NOT include brand name in title** (e.g., remove "Aspose", "GroupDocs", "Conholdate")
- **DO NOT include product name in seoTitle**
- **DO NOT include brand name in seoTitle**
- **DO NOT include product name in URL slug**
- **DO NOT include brand name in URL slug**
- Focus titles on the TASK/ACTION, not the product or brand
- **Acceptable generic references**: "powerful SDK", "robust library", "efficient API", "modern toolkit"
- **URL slug must be clear and readable**: Use "in" for language/platform designation
  - ✅ CORRECT: "convert-pdf-to-jpg-in-java"
  - ✅ CORRECT: "excel-to-pdf-conversion-in-csharp"
  - ✅ CORRECT: "html-to-markdown-in-python"
  - ❌ WRONG: "convert-pdf-to-jpg-java" (missing "in")
  - ❌ WRONG: "excel-pdf-csharp" (unclear, missing "to" and "in")
  - ❌ WRONG: "convert-pdf-to-jpg-using-aspose-in-java" (contains brand name)
  - ❌ WRONG: "convert-pdf-to-jpg-with-conholdate-in-java" (contains brand name)
- **CORRECT**: "Convert PDF to JPG in Java" (29 chars) ✅
- **CORRECT**: "Convert PPTX to JPG in Java" (28 chars) ✅
- **CORRECT**: "Convert PDF to JPG using a Powerful SDK" (40 chars) ✅
- **INCORRECT**: "Convert PDF to JPG using Aspose.PDF in Java" (44 chars and includes brand + product) ❌
- **INCORRECT**: "Convert PPTX to JPG in Java using Conholdate SDK" (49 chars and includes brand) ❌
- **INCORRECT**: "Convert PDF with Aspose in Java" (32 chars but includes brand) ❌
- **CORRECT**: "Excel to PDF Conversion Guide" (30 chars) ✅
- **INCORRECT**: "Excel to PDF with GroupDocs.Conversion" (39 chars and includes brand + product) ❌

**BRAND AND PRODUCT IDENTIFICATION:**
- **Brands**: Aspose, GroupDocs, Conholdate
- **Products**: Aspose.PDF, Aspose.Slides, Aspose.Words, GroupDocs.Conversion, GroupDocs.Viewer, Conholdate.Total, etc.
- **Rule**: Remove BOTH brand names AND product names from title, seoTitle, and URL slug
- **Alternative phrasing**: Focus on functionality, not branding
  - Instead of "using Aspose" → "using a powerful SDK" or just describe the task
  - Instead of "with Conholdate" → "with modern tools" or omit entirely
  - Instead of "GroupDocs solution" → "efficient solution" or focus on capability

**TITLE CRAFTING GUIDELINES:**
- Keep titles concise and action-oriented
- Include primary programming language/platform (Java, .NET, Python, etc.)
- **NEVER include brand names** (Aspose, GroupDocs, Conholdate)
- **NEVER include product names** (Aspose.PDF, GroupDocs.Conversion, Conholdate.Total, etc.)
- Use format: "[Action] [Format1] to [Format2] in [Language]"
- Alternative format: "[Format] [Action] in [Language] Guide"
- Optional: Can add generic descriptor like "using a Powerful SDK" if needed for length, but avoid branding
- **URL slugs must use "in" before language/platform for clarity**
- Examples:
  - Title: "Convert PDF to PNG in C#" (26 chars) → URL: "convert-pdf-to-png-in-csharp" ✅
  - Title: "JPG to PDF in Java Guide" (25 chars) → URL: "jpg-to-pdf-in-java-guide" ✅
  - Title: "HTML to Markdown in Python" (27 chars) → URL: "html-to-markdown-in-python" ✅
  - Title: "DOCX to PDF in .NET" (20 chars) → URL: "docx-to-pdf-in-dotnet" ✅
  - Title: "Convert PPTX to JPG in Java" (28 chars) → URL: "convert-pptx-to-jpg-in-java" ✅
  - Title: "Convert PDF to JPG using a Powerful SDK" (40 chars) → URL: "convert-pdf-to-jpg-using-powerful-sdk" ✅
  - ❌ WRONG TITLE: "Convert PPTX to JPG in Java using Conholdate SDK" (contains brand)
  - ❌ WRONG TITLE: "PDF to Image with Aspose in C#" (contains brand)
  - ❌ WRONG URL: "convert-pdf-png-csharp" (missing "to" and "in")
  - ❌ WRONG URL: "jpg-pdf-java" (unclear, missing words)
  - ❌ WRONG URL: "convert-pdf-aspose-java" (contains brand name)

**CHARACTER COUNT VALIDATION:**
Before finalizing title/seoTitle/description/summary:
1. Count EXACT characters (including spaces)
2. Title: Must be 40-60 chars
3. SEO Title: Must be 40-60 chars
4. Description: Must be 140-160 chars
5. Summary: Must be 140-160 chars
6. URL: Must use "in" before language/platform (e.g., "in-csharp", "in-java", "in-python")
7. **Check for brand/product names**: Remove "Aspose", "GroupDocs", "Conholdate" and any product names
8. If outside range or contains branding, REWRITE until within limits and brand-free

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
title: "[Use exact title from {title} variable - adjust only if needed for 40-60 char limit - Keep product/brand names if present]"
seoTitle: "[Use exact title from {title} variable - adjust only if needed for 40-60 char limit - Keep product/brand names if present]"
description: "[140-160 char meta description - NO colons, NO special chars, NO line breaks]"
date: {current_date}
lastmod: {current_date}
draft: false
url: /{data.get("urlPrefix")}/[url-slug-NO-product-brand-names-use-in-before-language]/
author: "{author}"
summary: "[140-160 char summary - NO colons, NO special chars, NO line breaks, wrap in quotes if needed]"
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
1. **Introduction content** (NO HEADING - start directly with 2-3 paragraphs after frontmatter)
2. **Prerequisites/Installation** (ALWAYS CREATE - H2 header showing SDK setup instructions)
3. **Steps** (ALWAYS CREATE this section with 4-6 actionable steps, can include code snippets)
4. **Outline Sections** (Follow the provided outline exactly, can include code snippets with explanations)
5. **Complete Code Example(s)** (ONLY CREATE if you have actual code - one section per task with code)
   - **CRITICAL**: Only create this section if you have complete, working code to include
   - **NEVER** create the heading without code content
   - If single task with code: ONE Complete Code Example section
   - If multiple tasks: ONLY create Complete Code Example sections for tasks where you have code
6. **Conclusion** (ALWAYS CREATE this section)
7. **FAQs** (ALWAYS CREATE this section with 3-4 questions)
{"8. **Read More** (ALWAYS include this section last)" if formatted_related else ""}

### WRITING INSTRUCTIONS:
- **Start immediately** with frontmatter above (fill bracketed parts)
- **CRITICAL: Use the exact title from {title} variable** - keep it as-is, including any product/brand names
- **Only adjust title if it's outside 40-60 character limit** - otherwise use {title} exactly
- **Title MUST be 40-60 characters** - adjust length only if necessary
- **SEO Title MUST be 40-60 characters** - should match title
- **Description MUST be 140-160 characters**
- **URL MUST NOT contain product/brand name** - strip these out even if they're in {title}
- **After frontmatter**: Begin directly with introduction content (NO heading)
- **Introduction content**: 2-3 paragraphs explaining the topic (include at least 1 contextual link and product page URL with full product name)
- **Always include** ## Prerequisites or ## Installation section after introduction content
- **Always include** ## Steps section after Prerequisites/Installation
- Follow the provided outline EXACTLY for the main content
- **Only include** Complete Code Example section(s) if you have actual code - ONE section per task that has code
- **Never create** "Complete Code Example" heading without code content beneath it
- **Always include** ## Conclusion section
- **Always include** ## FAQs section with 3-4 relevant questions
{"- **Always include** ## Read More section last" if formatted_related else "- **DO NOT include** Read More section (no related links provided)"}
- Write 600-800 words total (excluding frontmatter, steps, code examples, and FAQs)
- Use clean Markdown with H2/H3 headers
- Include keywords naturally throughout
- **Use "SDK" terminology if platform ≠ "cloud"; use "library" or "API" if platform = "cloud"**
- **Use product page URL from context** whenever mentioning the product
- DO NOT add extra content not in the outline
- **Use only markdown-safe characters throughout entire content**
- **MUST include 2-3+ contextual links from provided context resources**
- **ALL code snippets MUST use <!--[CODE_SNIPPET_START]--> and <!--[CODE_SNIPPET_END]--> tags**

### CONTENT STRUCTURE:
- **Introduction content** = NO heading, just 2-3 paragraphs directly after frontmatter (include at least 1 contextual link and product page URL with full product name like "Aspose.Slides for .NET", use "SDK" if platform ≠ "cloud" or "library"/"API" if platform = "cloud", never use "Framework")
- **Prerequisites/Installation** = H2 header (## Prerequisites or ## Installation) showing how to install/set up the SDK/library (include download links, NuGet/Maven/pip commands, environment setup)
- **Steps** = H2 header (## Steps to [Task Name]) with 4-6 numbered steps (mention classes/methods/properties, link ONLY if URLs in context, NEVER put links in backticks, include contextual links where relevant, may include code snippets, use "SDK" if platform ≠ "cloud" or "library"/"API" if platform = "cloud", never use "Framework")
- Outline items = H2/H3 headers as specified (include contextual links naturally, link classes/methods ONLY if URLs in context, no links in backticks, may include code snippets with explanations, use "SDK" if platform ≠ "cloud" or "library"/"API" if platform = "cloud", include product page URL with full product name, never use "Framework")
- **Complete Code Example(s)** = H2 header(s) (## [Specific Task] - Complete Code Example) with full working code wrapped in tags - ONLY CREATE if you have actual code for that task
- **Conclusion** = H2 header (## Conclusion) with 2-3 paragraphs (include at least 1 contextual link and product page URL with full product name, use "SDK" if platform ≠ "cloud" or "library"/"API" if platform = "cloud", never use "Framework")
- **FAQs** = H2 header (## FAQs) with 3-4 Q&A pairs (include contextual links and product page URL with full product name in answers, link API references ONLY if URLs in context, no links in backticks, use "SDK" if platform ≠ "cloud" or "library"/"API" if platform = "cloud", never use "Framework")
{"- **Read More** = H2 header (## Read More) with provided links" if formatted_related else ""}
- Complete paragraphs required for all sections
- Include relevant examples/code where appropriate
- **All content must use markdown-safe characters only**
- **Contextual links must be naturally integrated, not forced**
- **Product page URL must use full product name with platform as anchor text**
- **Link classes/methods/properties ONLY if their URLs are provided in context**
- **NEVER put links inside backticks or code literals**
- **Never use "Framework" anywhere in content**

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

### COMPLETE CODE EXAMPLE SECTION (CONDITIONAL):
**CRITICAL REQUIREMENT**: Only create this section if you have actual, complete, working code to include.

**When to CREATE Complete Code Example section(s):**
- You have full, working code that demonstrates the task
- The code is complete and copy-paste ready (no placeholders)
- The task in the title can be demonstrated with code

**When to SKIP Complete Code Example section(s):**
- You don't have complete code available
- The code would be incomplete or use placeholders like "// ... rest of code"
- The task is conceptual and doesn't have a concrete code implementation

**MULTIPLE TASKS HANDLING:**
- If title contains ONE task with code: Create ONE Complete Code Example section
- If title contains MULTIPLE tasks: ONLY create Complete Code Example sections for tasks where you have actual code
- Parse the title to identify all tasks (look for "and", "or", conjunctions, multiple formats mentioned)
- Each task that has code gets its own dedicated Complete Code Example section
- Tasks without code implementations should be skipped (no empty sections)

**Format for SINGLE task (with code):**
## [Task from Title] - Complete Code Example

Example: "## Convert PDF to PNG - Complete Code Example"

**Format for MULTIPLE tasks (only sections with code):**
## [First Task] - Complete Code Example
[Full code for first task]

## [Second Task] - Complete Code Example
[Full code for second task - only if you have code]

## [Third Task] - Complete Code Example
[Full code for third task - only if you have code]

**Examples:**
- Title: "Convert PDF to PNG and JPG" → Create 2 sections ONLY if you have code for both:
  - "## Convert PDF to PNG - Complete Code Example" (if code available)
  - "## Convert PDF to JPG - Complete Code Example" (if code available)
  
- Title: "Convert DOCX to PDF, HTML, and Markdown" → Create sections ONLY for tasks with code:
  - "## Convert DOCX to PDF - Complete Code Example" (if code available)
  - "## Convert DOCX to HTML - Complete Code Example" (if code available)
  - Skip Markdown section if no code available

- Title: "Convert PDF to PNG" → Create 1 section ONLY if you have code:
  - "## Convert PDF to PNG - Complete Code Example" (if code available)

**Structure for each Complete Code Example section (when included):**

[1-2 sentence introduction explaining what this specific code does, use "SDK" if platform ≠ "cloud" or "library"/"API" if platform = "cloud"]

<!--[COMPLETE_CODE_SNIPPET_START]-->
```language
// Full working code for THIS specific task
// Include all necessary imports, initialization, and implementation
// This should be production-ready or near-production quality
// Must be complete - no placeholders like "// ... rest of code"
```
<!--[COMPLETE_CODE_SNIPPET_END]-->

[Optional: 1-2 sentences explaining how to run or use this code]

**Requirements for EACH Complete Code Example (when created):**
- Must be FULL working code for that specific task (no partial snippets)
- Must be copy-paste ready (no "..." or placeholders)
- Must include all imports/dependencies needed for that task
- Must include proper initialization and error handling
- Should be well-commented for clarity
- Must focus on ONE specific task per section
- Must be wrapped in <!--[COMPLETE_CODE_SNIPPET_START]--> and <!--[COMPLETE_CODE_SNIPPET_END]-->
- Each section is independent and can be used standalone
- **Only create section if you have actual code** - never create empty sections

### CONTEXTUAL LINKING GUIDELINES:
**When to link to API references (CONDITIONAL - ONLY IF URL IN CONTEXT):**
- **CRITICAL**: Only link classes/methods/properties if their API reference URL is explicitly provided in the context
- **If URL is NOT in context**: Mention the class/method/property as plain text without a link
- **NEVER construct or guess API reference URLs**
- **NEVER put links inside backticks or code literals** - this breaks Hugo rendering
- When linking (if URL available):
  - ✅ CORRECT: "Initialize the [Presentation](API_reference_URL) class" (link outside backticks)
  - ✅ CORRECT: "Use the [Save](API_reference_URL) method to export" (link outside backticks)
  - ❌ WRONG: "Initialize the `[Presentation](URL)` class" (link inside backticks - won't render)
  - ❌ WRONG: "Use `[Save](URL).PNG`" (link inside code literal - won't render)
  - ❌ WRONG: "Use the [ImageFormat](URL).PNG property" (appending .PNG to URL breaks link)
- When URL is NOT available:
  - ✅ CORRECT: "Initialize the Presentation class" (plain text, no link)
  - ✅ CORRECT: "Use the Save method to export" (plain text, no link)
  - ✅ CORRECT: "Set the ImageFormat property" (plain text, no link)
- **Apply to Steps section, code explanations, and throughout content**
- **Only use URLs that are verified to be in the context**

**When to link to documentation:**
- "Learn more about [feature] in the [documentation](URL)"
- "For detailed API specifications, see the [API reference](URL)"
- "Check out the [complete guide](URL) for advanced features"

**When to link to product page (MANDATORY):**
- "Using [Full Product Name with Platform](product_page_URL), you can..."
- "The [Full Product Name with Platform](product_page_URL) SDK provides..." (if platform ≠ "cloud")
- "The [Full Product Name with Platform](product_page_URL) library provides..." (if platform = "cloud")
- "Get started with [Full Product Name with Platform](product_page_URL) to..."
- **CRITICAL**: Use FULL product name including platform (e.g., "Aspose.Slides for .NET", "GroupDocs.Conversion for Java")
- **NEVER use generic text like "product page" or just product name without platform**
- **Use product page URL from context whenever product is mentioned**
- **Example**: [Aspose.Slides for .NET](https://products.aspose.com/slides/net/) ✅
- **WRONG**: [product page](https://products.aspose.com/slides/net/) ❌
- **WRONG**: [Aspose.Slides](https://products.aspose.com/slides/net/) ❌

**When to link to category pages:**
- "Explore more [category] solutions at [Category Page](URL)"
- "This is part of our [Product Category](URL) offerings"

**When to link to download/installation:**
- "Get started by [downloading the SDK](URL)" (if platform ≠ "cloud")
- "Get started by [downloading the library](URL)" (if platform = "cloud")
- "Visit our [installation guide](URL) for setup instructions"

**Link placement best practices:**
- Integrate links naturally within sentences
- **Only link classes/methods/properties if their API reference URL is in context**
- **NEVER put links inside backticks or code literals** - Hugo won't render them
- Use descriptive anchor text that tells readers what they'll find
- Place links where readers would logically want more information
- Don't cluster multiple links in one sentence unless necessary
- Ensure links add value and aren't just inserted for SEO
- **Always link product name to product page URL from context**
- **Only link API elements (classes/methods) if URLs are in context**
- **If URL is not in context, mention without linking**
- **Verify all URLs are from context before using**

### PREREQUISITES/INSTALLATION SECTION (MANDATORY):
This section MUST appear after introduction content and before Steps section.

**Section title options:**
- ## Prerequisites (if covering requirements + installation)
- ## Installation (if focusing only on setup)

**Content to include:**
1. **System requirements** (if applicable):
   - Operating system compatibility
   - Platform version (e.g., .NET version, Java version, Python version)
   - Any other dependencies

2. **Installation instructions** (MANDATORY):
   - Package manager command (NuGet, Maven, pip, npm, etc.)
   - Alternative: Direct download link from context resources
   - Example:
     ```
     Install-Package Aspose.Slides.NET
     ```
   - Or for Java:
     ```xml
     <dependency>
         <groupId>com.aspose</groupId>
         <artifactId>aspose-slides</artifactId>
         <version>XX.X</version>
     </dependency>
     ```

3. **License/Setup** (if applicable):
   - Mention licensing requirements
   - Link to getting started guide or documentation

**Format:**
## Prerequisites
[OR]
## Installation

[1-2 sentences explaining what's needed]

**Installation via [Package Manager]:**

<!--[CODE_SNIPPET_START]-->
```language
// Installation command
```
<!--[CODE_SNIPPET_END]-->

[Optional: Alternative installation methods or additional setup steps]

[Optional: Link to download page or documentation]

**Requirements:**
- Must include actual installation command/code
- Must use code snippet tags
- Should link to download page if available in context
- Keep concise (2-4 paragraphs maximum)
- Use "SDK" if platform ≠ "cloud", or "library"/"API" if platform = "cloud", never "Framework"
- Include product page URL with full product name if mentioning product
- Create 4-6 clear, actionable steps to accomplish the task described in the title
- Steps should be technical and implementation-focused
- Each step should be a complete, actionable instruction
- Steps should follow a logical progression from setup to completion
- Use technical terminology appropriate to the product/platform
- **Use "SDK" terminology unless product is cloud-based**
- **NEVER use "Framework" - replace with "SDK", "platform", or other alternatives**
- **Steps must use only markdown-safe characters**
- **Include contextual links in steps where relevant (setup, configuration, API calls)**
- **Include product page URL with full product name when mentioning product in steps**
- **Can include partial code snippets in steps** (wrapped in tags) to illustrate specific actions
- Steps MUST be included in both:
  1. **Frontmatter** (in YAML format as a list - quoted strings)
  2. **Content section** (as markdown H2 section after Prerequisites/Installation)

### STEPS CONTENT FORMAT:
## Steps to [Task Name Based on Title]

1. **[Step 1 summary with class/method]**: [Brief explanation mentioning the class/method - markdown-safe chars only, link API reference ONLY if URL is in context, NEVER put links in backticks]
   
   Example: **Initialize Presentation class**: Load your PowerPoint file using the Presentation constructor. (Note: Only add [Presentation](URL) link if URL is in context, otherwise plain text)
   
   [Optional code snippet if needed]
   <!--[CODE_SNIPPET_START]-->
```language
   // Step-specific code
```
   <!--[CODE_SNIPPET_END]-->

2. **[Step 2 summary with method]**: [Brief explanation - markdown-safe chars only, link ONLY if URL in context, no links in backticks]

3. **[Step 3 summary with method]**: [Brief explanation - markdown-safe chars only, link ONLY if URL in context, no links in backticks]

4. **[Step 4 summary with method]**: [Brief explanation - markdown-safe chars only, link ONLY if URL in context, no links in backticks]

5. **[Step 5 summary - OPTIONAL]**: [Brief explanation - markdown-safe chars only]

6. **[Step 6 summary - OPTIONAL]**: [Brief explanation - markdown-safe chars only]

### FAQs SECTION REQUIREMENTS:
- Create 3-4 frequently asked questions relevant to the topic
- Questions should cover common user concerns, technical details, or best practices
- Answers should be detailed (2-4 sentences each)
- **MUST include contextual links in FAQ answers** using format: `[Resource Name](URL)`
- **MUST use product page URL with full product name when mentioning product in answers**
- **Example**: [Aspose.Slides for .NET](https://products.aspose.com/slides/net/) ✅
- **Use "SDK" if platform ≠ "cloud"; use "library" or "API" if platform = "cloud"**
- **NEVER use "Framework" in answers**
- Questions should be practical and directly related to the blog topic
- **FAQs must use only markdown-safe characters**
- FAQs MUST be included in both:
  1. **Frontmatter** (in YAML format as shown above - quoted strings)
  2. **Content section** (as markdown H2 section {"before Read More" if formatted_related else "as the FINAL section"})

### FAQs CONTENT FORMAT:
## FAQs

**Q: [First question - markdown-safe chars only]**  
A: [Detailed answer with at least one contextual link and product page URL - markdown-safe chars only, use "SDK" if platform ≠ "cloud" or "library"/"API" if platform = "cloud"]

**Q: [Second question - markdown-safe chars only]**  
A: [Detailed answer with contextual link if relevant - markdown-safe chars only, use "SDK" if platform ≠ "cloud" or "library"/"API" if platform = "cloud"]

**Q: [Third question - markdown-safe chars only]**  
A: [Detailed answer with contextual link if relevant - markdown-safe chars only, use "SDK" if platform ≠ "cloud" or "library"/"API" if platform = "cloud"]

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
- API reference links: `[ClassName](API_ref_URL)`, `[MethodName](API_ref_URL)` - **ONLY if URL is in context**
- **If API reference URL not in context**: Mention class/method as plain text without link
- **NEVER put links inside backticks**: `[ClassName](URL)` won't render in Hugo
- **CORRECT**: Use the [ClassName](URL) method (link outside backticks)
- **WRONG**: Use the `[ClassName](URL)` method (link inside backticks)
- **WRONG**: Use the `[ClassName](URL).Property` (link in code literal)
- Product references: `[Full Product Name with Platform](product_page_URL from context)` - **MANDATORY when mentioning product**
- **CRITICAL**: Always use FULL product name including platform
- **Example**: `[Aspose.Slides for .NET](https://products.aspose.com/slides/net/)` ✅
- **Example**: `[Presentation](https://reference.aspose.com/slides/net/aspose.slides/presentation/)` ✅ (only if URL in context)
- **WRONG**: `[product page](URL)` ❌
- **WRONG**: `[Aspose.Slides](URL)` ❌
- **WRONG**: `[ImageFormat](URL).PNG` ❌ (appending to URL breaks link)
- No naked URLs allowed
- **At least 2-3 contextual links from provided resources required throughout content**
- **Product page URL must use full product name as anchor text whenever product is mentioned**
- **Only link classes/methods/properties if their API reference URLs are in context**
- **At least 1 product/documentation link required in FAQ answers**
- Links are markdown-safe by default
- **Verify all URLs exist in context before using**

### STRICTLY ENFORCED BOUNDARIES:
- **BEGINNING**: First character must be `-` of frontmatter (no spaces, no text before)
- **INTRODUCTION CONTENT**: Must be first content after frontmatter (NO heading, just paragraphs, include contextual link and product page URL with full product name)
- **PREREQUISITES/INSTALLATION**: Must be included after introduction content (H2 header with setup instructions)
- **STEPS**: Must be included after Prerequisites/Installation (include contextual links where relevant, may include code, use "SDK" if platform ≠ "cloud" or "library"/"API" if platform = "cloud", never use "Framework")
- **COMPLETE CODE EXAMPLE(S)**: Only include if you have actual code - never create empty sections
- **CONCLUSION**: Must be included before FAQs section (include contextual link and product page URL with full product name, use "SDK" if platform ≠ "cloud" or "library"/"API" if platform = "cloud", never use "Framework")
- **FAQs**: Must be included {"before Read More section" if formatted_related else "as the FINAL section"} (include contextual links and product page URL with full product name in answers, use "SDK" if platform ≠ "cloud" or "library"/"API" if platform = "cloud", never use "Framework")
{"- **READ MORE**: Must be included as the FINAL section" if formatted_related else ""}
- **ENDING**: Last character must be after the final {"link in Read More section" if formatted_related else "FAQ answer"}
- **ABSOLUTELY NO CONTENT** outside these boundaries
- **STOP WRITING IMMEDIATELY** after the {"Read More" if formatted_related else "FAQs"} section

### OUTPUT REQUIREMENTS:
- Complete markdown file starting with frontmatter
- **Title: 40-60 characters, use exact title from {title} variable (keep product/brand names if present)**
- **SEO Title: 40-60 characters, should match title**
- **Description: 140-160 characters**
- **Summary: 140-160 characters**
- **URL: NO product/brand name in slug** (no "aspose", "groupdocs", "conholdate"), **MUST use "in" before language/platform**
- **Introduction content with NO heading** - start directly with paragraphs
- Always includes Prerequisites/Installation, Steps, Conclusion, and FAQs sections
- **Only includes Complete Code Example(s) if actual code is available** - never create empty sections
{"- Always includes Read More section with provided links" if formatted_related else "- Does NOT include Read More section (no related links)"}
- Steps in both frontmatter (YAML list - quoted) and content (Markdown numbered list)
- FAQs in both frontmatter (YAML - quoted) and content (Markdown)
- **ALL code snippets wrapped with <!--[CODE_SNIPPET_START]--> and <!--[CODE_SNIPPET_END]-->**
- **Complete Code Example section(s) ONLY if you have full, working code** - one section per task with code
- **Use "SDK" if platform ≠ "cloud"; use "library" or "API" if platform = "cloud"**
- **NEVER use "Framework" terminology anywhere**
- **Use product page URL with FULL product name (including platform) whenever product is mentioned**
- **Example**: [Aspose.Slides for .NET](URL) not [product page](URL) or [Aspose.Slides](URL)
- **ALL content uses only markdown-safe ASCII characters**
- **NO Unicode characters that break YAML/Hugo rendering**
- **MINIMUM 2-3 contextual links from provided resources integrated naturally**
- **Only link classes/methods/properties if their API reference URLs are in context**
- **NEVER construct or guess URLs - use only URLs from context**
- **NEVER put links inside backticks or code literals - Hugo won't render them**
- **Product page URL linked with FULL product name (e.g., "Aspose.Slides for .NET") whenever product appears**
- **Prerequisites/Installation section with SDK setup instructions**
- Ending after {"Read More" if formatted_related else "FAQs"} section
- No trailing whitespace, comments, or additional text
- Pure markdown content only

### VIOLATION PREVENTION:
- If title is NOT 40-60 characters → OUTPUT IS INVALID
- If seoTitle is NOT 40-60 characters → OUTPUT IS INVALID
- If description is NOT 140-160 characters → OUTPUT IS INVALID
- If summary is NOT 140-160 characters → OUTPUT IS INVALID
- If URL contains product name → OUTPUT IS INVALID
- If URL contains brand name (aspose, groupdocs, conholdate) → OUTPUT IS INVALID
- If URL doesn't use "in" before language/platform → OUTPUT IS INVALID
- If introduction has H2 heading → OUTPUT IS INVALID
- If Prerequisites/Installation section missing → OUTPUT IS INVALID
- If Steps, Conclusion, or FAQs missing → OUTPUT IS INVALID
- If "Complete Code Example" heading exists WITHOUT actual code content → OUTPUT IS INVALID
- If title mentions multiple tasks and Complete Code Example sections exist for tasks without code → OUTPUT IS INVALID
{"- If Read More section missing → OUTPUT IS INVALID" if formatted_related else "- If Read More section present → OUTPUT IS INVALID"}
- If Steps not in frontmatter → OUTPUT IS INVALID
- If FAQs not in frontmatter → OUTPUT IS INVALID
- If any code snippet lacks <!--[CODE_SNIPPET_START]--> and <!--[CODE_SNIPPET_END]--> → OUTPUT IS INVALID
- If any Complete Code Example is partial or has placeholders → OUTPUT IS INVALID
- If any text before frontmatter or after {"Read More" if formatted_related else "FAQs"} → OUTPUT IS INVALID
- If outline sections skipped → OUTPUT IS INVALID
- If "library" or "API" used when platform ≠ "cloud" → OUTPUT IS INVALID
- If "SDK" used when platform = "cloud" → OUTPUT IS INVALID
- If "Framework" appears anywhere in content → OUTPUT IS INVALID
- If product mentioned without product page URL link → OUTPUT IS INVALID
- If product page URL uses generic anchor text like "product page" → OUTPUT IS INVALID
- If product page URL doesn't include full product name with platform → OUTPUT IS INVALID
- **If word count (Introduction + Prerequisites/Installation + Outline sections + Conclusion) is NOT {settings.NUMBER_OF_BLOG_WORDS} words → OUTPUT IS INVALID**
- **If Unicode/special characters in frontmatter → OUTPUT IS INVALID**
- **If unquoted YAML values contain colons → OUTPUT IS INVALID**
- **If line breaks in YAML string values → OUTPUT IS INVALID**
- **If fewer than 2 contextual links from provided resources → OUTPUT IS INVALID**
- **If links are placed inside backticks or code literals → OUTPUT IS INVALID**
- **If API reference links used for classes/methods whose URLs are NOT in context → OUTPUT IS INVALID**
- **If any URL used is not found in the context → OUTPUT IS INVALID**
- **If no links in FAQ answers → OUTPUT IS INVALID**
- **If product page URL not used with full product name when mentioning product → OUTPUT IS INVALID**

### PRE-SUBMISSION CHECKLIST:
Before returning the blog post, verify:
- [ ] **Title is 40-60 characters (count manually)**
- [ ] **SEO Title is 40-60 characters (count manually)**
- [ ] **Description is 140-160 characters (count manually)**
- [ ] **Summary is 140-160 characters (count manually)**
- [ ] **Summary is 140-160 characters (count manually)**
- [ ] **URL uses "in" before language/platform** (e.g., "in-csharp", "in-java", "in-python")
- [ ] **NO product name in title**
- [ ] **NO product name in seoTitle**
- [ ] **NO product name in URL slug**
- [ ] **URL uses "in" before language/platform** (e.g., "in-csharp", "in-java", "in-python")
- [ ] **Introduction content has NO H2 heading** - starts directly with paragraphs
- [ ] **Prerequisites/Installation section included** with SDK setup instructions
- [ ] **Correct terminology used based on platform variable**: "SDK" if platform ≠ "cloud", "library"/"API" if platform = "cloud"
- [ ] **"Framework" is NEVER used anywhere** in content
- [ ] **Product page URL with FULL product name** (e.g., "Aspose.Slides for .NET") used whenever product is mentioned
- [ ] **NEVER use "product page" or incomplete product name as anchor text**
- [ ] **Only link classes/methods/properties if their API reference URLs are in context**
- [ ] **NO links inside backticks or code literals** (e.g., no `[ClassName](URL)`)
- [ ] **All URLs used are verified to exist in context**
- [ ] **No constructed or guessed URLs** - only use exact URLs from context
- [ ] **Steps section mentions classes/methods (links only if URLs in context)**
- [ ] **Complete Code Example sections ONLY exist where actual code is included**
- [ ] **NO "Complete Code Example" headings without code content**
- [ ] No em/en dashes (— –) anywhere - use hyphens (-)
- [ ] No curly quotes (" " ' ') - use straight quotes (" ')
- [ ] No special Unicode characters
- [ ] All YAML values with colons are quoted
- [ ] No line breaks in frontmatter string values
- [ ] All steps are quoted in frontmatter
- [ ] All FAQ questions and answers are properly formatted in YAML
- [ ] **ALL code snippets wrapped with <!--[CODE_SNIPPET_START]--> and <!--[CODE_SNIPPET_END]-->**
- [ ] **If multiple tasks in title: verified which have code, only created sections for those**
- [ ] **Each Complete Code Example section has FULL working code (no placeholders)**
- [ ] **Each Complete Code Example section is independently usable**
- [ ] **At least 2-3 contextual links from provided resources included naturally**
- [ ] **At least 1 link in introduction content**
- [ ] **Prerequisites/Installation section has installation code/commands**
- [ ] **At least 1 link in Conclusion section**
- [ ] **At least 1 link in FAQ answers**
- [ ] **Product page URL with full product name in introduction, conclusion, and FAQs**
- [ ] All links use descriptive anchor text (not "click here")
- [ ] **Word count verified: Introduction + Prerequisites/Installation + Outline sections + Conclusion = {settings.NUMBER_OF_BLOG_WORDS} words**
- [ ] **Word count EXCLUDES: Frontmatter, Steps section, Code examples, FAQs, Read More**
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
        Return ONLY a well-formatted markdown outline with exactly 6 H2 sections.

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