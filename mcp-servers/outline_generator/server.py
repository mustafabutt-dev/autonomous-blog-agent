# server.py
from fastmcp import FastMCP
from openai import OpenAI
import os, sys

# Load env
from dotenv import load_dotenv
load_dotenv()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_PATH = os.path.abspath(os.path.join(BASE_DIR, "../.."))

if PARENT_PATH not in sys.path:
    sys.path.append(PARENT_PATH)

from agent_engine.config import settings
from agent_engine.utils.prompts import build_outline_prompt
# Initialize client (OpenAI-compatible)
client = OpenAI(
    base_url=settings.ASPOSE_LLM_BASE_URL,
    api_key=settings.ASPOSE_LLM_API_KEY
)

# MCP Server
mcp = FastMCP("outline_generator")


# -----------------------------
# MCP TOOL
# -----------------------------
@mcp.tool()
async def generate_outline(
    title,
    keywords
):
    prompt = build_outline_prompt(title, keywords)

    response = client.responses.create(
        model='gpt-oss', 
        input=prompt,
    )

    outline = response.output_text.strip()
    return {
        "title": title,
        "keywords": keywords,
        "outline": outline
    }


# -----------------------------
# Start MCP
# -----------------------------
if __name__ == "__main__":
    mcp.run()
