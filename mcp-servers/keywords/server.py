"""
Keywords MCP Server - Dynamic keyword research
Uses modular services via aggregator
"""

import sys
import os
from dotenv import load_dotenv
from fastmcp import FastMCP

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

# Import aggregator service
from services.keyword_aggregator import KeywordAggregator

# Initialize MCP Server
mcp = FastMCP("keywords-server")
print(" Initializing aggregator...", file=sys.stderr, flush=True)
aggregator = KeywordAggregator()
print(f" Aggregator initialized with {len(aggregator.services)} services", file=sys.stderr, flush=True)

# ---------------------------------------------
# Define MCP Tool
# ---------------------------------------------
@mcp.tool()
async def fetch_keywords(topic: str, product_name: str = None) -> dict:
    """
    Fetch high-ranking keywords from multiple sources
    
    Combines data from:
    - Google Search Console (your site data)
    - SerpAPI (Google search results)
    - More sources can be added easily
    """
    print(f"fetch_keywords TOOL CALLED (topic={topic}, product={product_name})", file=sys.stderr, flush=True)
    
    # Fetch keywords
    result = await aggregator.fetch_all_keywords(topic, product_name)

    print(f" Result fetched: {result}", file=sys.stderr, flush=True)

    return {
        "topic": topic,
        "keywords": result,
        "status": "success"
    }

    # return {
    #     "topic": topic,
    #     "keywords": {'primary': ['Convert docx to xml', 'Convert docx to xml using Aspose', 'Free online DOCX to XML conversion App via java', 'Java API to Convert DOCX to XLAM or with free Online ...', 'Saving Documents as OOXML Format in Aspose.Words for Java'], 'secondary': [], 'long_tail': ['Can I convert docx to XML?', 'How to convert DOCX to PDF in Java Aspose words?', 'How to convert PDF to XML in Java?', 'How do you create an XML file from a Word document?'], 'metadata': {'sources': ['SerpAPI'], 'total_services': 1, 'total_keywords': 9}},
    #     "status": "success"
    # }

# ---------------------------------------------
# Run MCP Server
# ---------------------------------------------
if __name__ == "__main__":
    print(" Starting Keywords MCP Server (Dynamic)...", file=sys.stderr, flush=True)
    mcp.run()
