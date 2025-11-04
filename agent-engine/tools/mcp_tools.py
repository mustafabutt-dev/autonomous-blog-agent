from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from agents import function_tool
import json

# Define tools as decorated functions
@function_tool
async def fetch_keywords(topic: str, product_name: str = "") -> str:
    """Fetch high-ranking SEO keywords for a topic"""

    print(f" fetch_keywords TOOL CALLED!")

    try:
        params = StdioServerParameters(
            command="python",
            args=["../mcp-servers/keywords/server.py"]
        )
        
        print(f" Connecting to MCP server...")
        
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool("fetch_keywords", {
                    "topic": topic,
                    "product_name": product_name
                })
                print(f" Got result: {result.content[0].text}")
                return result.content[0].text
                
    except Exception as e:
        print(f" ERROR in fetch_keywords: {e}")
        import traceback
        traceback.print_exc()
        return '{"error": "failed"}'

@function_tool
async def generate_seo_title(topic: str, keywords_json: str, product_name: str = "") -> str:
    """
    Generate an SEO-optimized blog title
    
    Args:
        topic: The blog topic
        keywords_json: JSON string containing keywords data
        product_name: Optional product name
    """
    keywords_data = json.loads(keywords_json)
    keywords = keywords_data.get('keywords', {}).get('primary', [topic])
    
    params = StdioServerParameters(
        command="python",
        args=["../mcp-servers/seo/server.py"]
    )
    
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool("generate_seo_title", {
                "topic": topic,
                "keywords": keywords,
                "product_name": product_name
            })
            return result.content[0].text

@function_tool
async def generate_markdown_file(title: str, content: str, keywords_json: str) -> str:
    """
    Save blog content as a markdown file
    
    Args:
        title: Blog title
        content: Full blog content in markdown format
        keywords_json: JSON string of keywords list
    """

    # Parse keywords if it's a string
    if isinstance(keywords_json, str):
        try:
            keywords_data = json.loads(keywords_json)
            print(f" Parsed keywords_data: {keywords_data}")

            if isinstance(keywords_data, dict):
                # Combine all keyword types into a single list
                all_keywords = (
                    keywords_data.get("primary", []) +
                    keywords_data.get("secondary", []) +
                    keywords_data.get("long_tail", [])
                )
                keywords = all_keywords
                print(f" Combined keywords: {keywords}")

            elif isinstance(keywords_data, list):
                keywords = keywords_data
            else:
                keywords = []
        except Exception as e:
            print(f" Parse error: {e}")
            keywords = [keywords_json]
    else:
        # If already a dict (not string), handle directly
        if isinstance(keywords_json, dict):
            keywords = (
                keywords_json.get("primary", []) +
                keywords_json.get("secondary", []) +
                keywords_json.get("long_tail", [])
            )
        elif isinstance(keywords_json, list):
            keywords = keywords_json
        else:
            keywords = []

    print(f" Final keywords list: {keywords}")
    
    params = StdioServerParameters(
        command="python",
        args=["../mcp-servers/file-generator/server.py"]
    )

    print(f" generate_markdown_file CALLED!")
    print(f"Title: {title}")
    print(f"Content length: {len(content)}")
    print(f"Keywords: {keywords_json}")

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool("generate_markdown_file", {
                "title": title,
                "content": content,
                "keywords": keywords,
                "output_dir": "../output/blogs"
            })
            return result.content[0].text