"""
Keywords MCP Server - Dynamic keyword research
Uses modular services via aggregator
"""

import sys
import os, json
from dotenv import load_dotenv
from fastmcp import FastMCP
from typing import Dict, List
from openai import OpenAI
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_PATH = os.path.abspath(os.path.join(BASE_DIR, "../.."))

if PARENT_PATH not in sys.path:
    sys.path.append(PARENT_PATH)
    
from agent_engine.services import SerpAPIKeywordService
from agent_engine.utils.prompts import keyword_filter_prompt
from agent_engine.config import settings
client = OpenAI(
    base_url=settings.ASPOSE_LLM_BASE_URL,
    api_key=settings.ASPOSE_LLM_API_KEY
)
# ---------------------------------------------
# Log only to stderr — keep stdout clean for JSON-RPC
# ---------------------------------------------
print(" MCP Server starting...", file=sys.stderr, flush=True)

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), '../../agent_engine/.env')
load_dotenv(env_path)
print(f" Loaded .env from: {env_path}", file=sys.stderr, flush=True)
print(f" SERPAPI_API_KEY present: {bool(os.getenv('SERPAPI_API_KEY'))}", file=sys.stderr, flush=True)

# Add agent-engine to import path
current_dir = os.path.dirname(os.path.abspath(__file__))
agent_engine_dir = os.path.join(current_dir, '../../agent_engine')
sys.path.insert(0, agent_engine_dir)

mcp = FastMCP("keywords-server")

# ---------------------------------------------
# Define MCP Tool
# ---------------------------------------------
@mcp.tool()
async def fetch_keywords(topic: str, product_name: str = None) -> dict:
   
    print(f"fetch_keywords TOOL CALLED (topic={topic}, product={product_name})", file=sys.stderr, flush=True)
    all_results = []
    serpapi = SerpAPIKeywordService()
    try:
        result = await serpapi.fetch_keywords(topic, product_name)
        all_results.append(result)
    except Exception as e:
        print(f" Error from: {e}")
    
    # Merge results
    merged = _merge_keywords(all_results)
    prompt = keyword_filter_prompt(product_name, merged)
    response = client.responses.create(
        model='gpt-oss', 
        input=prompt,
    )
    final_keywords = json.loads(response.output_text.strip())
    
    print(f" Result fetched: {final_keywords}", file=sys.stderr, flush=True)

    return {
        "topic": topic,
        "keywords": final_keywords,
        "status": "success"
    }

    # return {
    #     "topic": topic,
    #     "keywords": {'primary': ['Convert docx to xml', 'Convert docx to xml using Aspose', 'Free online DOCX to XML conversion App via java', 'Java API to Convert DOCX to XLAM or with free Online ...', 'Saving Documents as OOXML Format in Aspose.Words for Java'], 'secondary': [], 'long_tail': ['Can I convert docx to XML?', 'How to convert DOCX to PDF in Java Aspose words?', 'How to convert PDF to XML in Java?', 'How do you create an XML file from a Word document?'], 'metadata': {'sources': ['SerpAPI'], 'total_services': 1, 'total_keywords': 9}},
    #     "status": "success"
    # }
def _merge_keywords( results: List[Dict]) -> Dict:
    """
    Merge keywords from multiple sources
    Removes duplicates and combines metadata
    """

    primary = []
    secondary = []
    long_tail = []
    sources = []

    for result in results:
        primary.extend(result.get("primary", []))
        secondary.extend(result.get("secondary", []))
        long_tail.extend(result.get("long_tail", []))
        sources.append(result.get("source", "Unknown"))

    # Remove duplicates while preserving order
    primary = list(dict.fromkeys(primary))
    secondary = list(dict.fromkeys(secondary))
    long_tail = list(dict.fromkeys(long_tail))

    return {
        "primary": primary,
        "secondary": secondary,
        "long_tail": long_tail,
        "metadata": {
            "sources": sources,
            "total_services": len(results),
            "total_keywords": len(primary) + len(secondary) + len(long_tail)
        }
    }

# ---------------------------------------------
# Run MCP Server
# ---------------------------------------------
if __name__ == "__main__":
    print(" Starting Keywords MCP Server (Dynamic)...", file=sys.stderr, flush=True)
    mcp.run()