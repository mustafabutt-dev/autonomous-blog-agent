from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import json

# Define tools as decorated functions
async def fetch_keywords(topic: str, product_name: str = "") -> str:
    """Fetch high-ranking SEO keywords for a topic"""

    print(f" fetch_keywords TOOL CALLED! upper")

    try:
        params = StdioServerParameters(
            command="python",
            args=["../mcp-servers/keywords/server.py"]
        )
        
        print(f" Connecting to MCP server fetch_keywords...")
        
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool("fetch_keywords", {
                    "topic": topic,
                    "product_name": product_name
                })
                return result.content[0].text
                
    except Exception as e:
        print(f" ERROR in fetch_keywords: {e}")
        import traceback
        traceback.print_exc()
        return '{"error": "failed"}'

async def generate_seo_title(topic: str, keywords_json: str, product_name: str = "") -> str:
    """
    Generate an SEO-optimized blog title
    
    Args:
        topic: The blog topic
        keywords_json: JSON string containing keywords data
        product_name: Optional product name
    """
    print(f" generate_seo_title TOOL CALLED! upper {keywords_json}", flush=True)
    keywords_data = json.loads(keywords_json)
    keywords = keywords_data.get('keywords', {}).get('primary', [topic])
    
    params = StdioServerParameters(
        command="python",
        args=["../mcp-servers/seo/server.py"]
    )
    print(f" Connecting to MCP server generate_seo_title...")
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool("generate_seo_title", {
                "topic": topic,
                "keywords": keywords,
                "product_name": product_name
            })
            parsed = json.loads(result.content[0].text)
            title = parsed.get("title")
            return title

async def generate_markdown_file(title, content, keywords_json) -> dict:
    """
    Save blog content as a markdown file.
    """
    import json
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    print(" generate_markdown_file TOOL CALLED (wrapper)", flush=True)

    # Parse keywords safely
    if isinstance(keywords_json, str):
        try:
            keywords_data = json.loads(keywords_json)
            if isinstance(keywords_data, dict):
                keywords = (
                    keywords_data.get("primary", []) +
                    keywords_data.get("secondary", []) +
                    keywords_data.get("long_tail", [])
                )
            elif isinstance(keywords_data, list):
                keywords = keywords_data
            else:
                keywords = []
        except Exception as e:
            print(f" Parse error: {e}", flush=True)
            keywords = [keywords_json]
    else:
        keywords = keywords_json or []

    print(" Connecting to MCP server generate_markdown_file...", flush=True)

    params = StdioServerParameters(
        command="python",
        args=["../mcp-servers/file-generator/server.py"]
    )

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool("generate_markdown_file", {
                "title": title,
                "content": content,
                "keywords": keywords,
                "output_dir": "../output/blogs"
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
