from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from typing import Dict, Optional
import json


async def fetch_category_related_articles(
    topic: str,
    product_name: str,
    category_url: str,
    required_count: int = 3
) -> Dict:
   
    server_params = StdioServerParameters(
        command="python",
        args=["../../mcp-servers/related-topics/server.py"]
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            result = await session.call_tool(
                "get_category_related_posts",
                arguments={
                    "topic": topic,
                    "product_name": product_name,
                    "category_url": category_url,
                    "required_count": required_count,
                    "tier1_limit": 50
                }
            )
       
            if hasattr(result, 'content'):
                if isinstance(result.content, list) and len(result.content) > 0:
                    content = result.content[0]
                    if hasattr(content, 'text'):
                        return json.loads(content.text)
                    elif hasattr(content, 'data'):
                        return content.data
            return {"error": "Failed to get response", "related_posts": []}

async def generate_read_more_section(
    topic: str,
    product_name: str,
    category_url: str = None
) -> str:
    """
    Generate Read More section for a blog post
    
    Args:
        topic: Blog topic being written
        product_name: Like "Aspose.PDF for Java"
        category_url: Category page URL (if not provided, uses default)
    
    Returns:
        Formatted Read More markdown section
    """
    
    # Default category URLs for common products (you can expand this)
    default_categories = {
        "aspose.pdf": "https://blog.aspose.com/pdf/",
        "aspose.cells": "https://blog.aspose.com/cells/",
        "aspose.words": "https://blog.aspose.com/words/",
        "aspose.slides": "https://blog.aspose.com/slides/",
    }
    
    # If no category URL provided, try to determine from product name
    if not category_url:
        product_lower = product_name.lower()
        for key, url in default_categories.items():
            if key in product_lower:
                category_url = url
                break
    
    if not category_url:
        return "\n## Read More\n\n- Visit our [blog](https://blog.aspose.com) for more articles\n"
    
    try:
        result = await fetch_category_related_articles(
            topic=topic,
            product_name=product_name,
            category_url=category_url,
            required_count=3
        )
        
        if result.get("error"):
            print(f"Error: {result['error']}")
            return ""
        
        articles = result.get("related_posts", [])
        target_language = result.get("target_language", "")
        
        if not articles:
            return ""
        
        # Build Read More section
        read_more = "\n## Read More\n\n"
        
        # Add language-specific heading if detected
        if target_language:
            lang_display = target_language.upper() if target_language == "java" else target_language.title()
            read_more += f"### More {lang_display} Examples\n\n"
        
        for article in articles:
            tier_info = ""
            if article.get("is_fallback"):
                tier_info = " *"  # Mark fallback articles
            read_more += f"- [{article['title']}]({article['url']}){tier_info}\n"
        
        # Add note if fallback articles included
        if any(a.get('is_fallback') for a in articles):
            read_more += "\n*_General articles from this category_\n"
        
        return read_more
        
    except Exception as e:
        print(f"Error generating read more section: {e}")
        return ""

# Integration function for your orchestrator
async def enhance_blog_with_category_articles(
    blog_content: str,
    topic: str,
    product_name: str,
    category_url: Optional[str] = None
) -> str:
    """
    Add Read More section to blog content based on category
    
    Example:
        product_name = "Aspose.PDF for Java"
        category_url = "https://blog.aspose.com/pdf/"
    """
    read_more = await generate_read_more_section(topic, product_name, category_url)
    if read_more:
        return blog_content + read_more
    return blog_content


async def generate_markdown_file(title, content, brand) -> dict:
    """
    Save blog content as a markdown file.
    """

    print(" Connecting to MCP server generate_markdown_file...", flush=True)

    params = StdioServerParameters(
        command="python",
        args=["../../mcp-servers/file-generator/server.py"]
    )

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool("generate_markdown_file", {
                "title": title,
                "content": content,
                "brand": brand,
                "output_dir": "../../content/blogPosts"
            })

            response_text = result.content[0].text
            print("✅ Raw MCP response:", response_text, flush=True)

            try:
                data = json.loads(response_text)
            except json.JSONDecodeError:
                data = {"raw_output": response_text}

            # ✅ Return structured dict instead of FunctionCallResult
            return {
                "output": data,
                "status": "success"
            }
                
async def gist_injector(content: str, res_title: str) -> str:
    
    params = StdioServerParameters(
        command="python",
        args=["../../mcp-servers/gist-injector/server.py"]
    )
    print(f" Connecting to MCP server gist-injector...")
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool("gist_injector", {
                "content": content,
                "title": res_title
            })
            return result