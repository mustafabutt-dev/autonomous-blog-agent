"""
SEO MCP Server - Generates optimized titles using self-hosted LLM
"""
import sys
import os
import random
from fastmcp import FastMCP
from openai import OpenAI
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_PATH = os.path.abspath(os.path.join(BASE_DIR, "../.."))

if PARENT_PATH not in sys.path:
    sys.path.append(PARENT_PATH)

from agent_engine.config import settings
from agent_engine.utils.prompts import get_title_prompt

# Load your environment (optional if already set)
from dotenv import load_dotenv
load_dotenv()

# Initialize MCP
mcp = FastMCP("seo-server")

client = OpenAI(
    base_url=settings.ASPOSE_LLM_BASE_URL,
    api_key=settings.ASPOSE_LLM_API_KEY
)

@mcp.tool()
async def generate_seo_title(topic: str, keywords: list, product_name: str = None) -> dict:
    """
    Generate an SEO-optimized blog title using your self-hosted LLM.
    Falls back to rule-based if LLM call fails.
    """

    primary_keyword = keywords[0] if keywords else topic
    keyword_list = ", ".join(keywords or [])
    product_name = product_name or ""

    prompt = get_title_prompt(topic, product_name,keyword_list)

    try:
        response = client.responses.create(
            model='gpt-oss', 
            input=prompt,
        )
        title = response.output_text.strip()
        char_count = len(title)

    except Exception as e:
        print(f"LLM error, using fallback: {e}", file=sys.stderr)
        templates = [
            f"Complete Guide to {primary_keyword} in {product_name}",
            f"How to {primary_keyword} Using {product_name or 'Modern Tools'}",
            f"Mastering {primary_keyword}: Step-by-Step Tutorial",
            f"Top {primary_keyword.title()} Tips You Need in {product_name}",
        ]
        title = random.choice(templates)
        char_count = len(title)

    return {
        "title": title,
        "char_count": char_count,
        "status": "success"
    }

if __name__ == "__main__":
    print(" SEO MCP Server running on http://127.0.0.1:3002")
    mcp.run()