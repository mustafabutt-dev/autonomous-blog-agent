"""
Keywords MCP Server - Dynamic keyword research
Uses modular services via aggregator
"""

from fastmcp import FastMCP
import sys
import os
from dotenv import load_dotenv

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), '../../agent-engine/.env')
load_dotenv(env_path)
print(f" Loaded .env from: {env_path}")
print(f" SERPAPI_API_KEY present: {bool(os.getenv('SERPAPI_API_KEY'))}")

# path to import services
current_dir = os.path.dirname(os.path.abspath(__file__))
agent_engine_dir = os.path.join(current_dir, '../../agent-engine')
sys.path.insert(0, agent_engine_dir)

print(f" Adding to path: {agent_engine_dir}")
from services.keyword_aggregator import KeywordAggregator

mcp = FastMCP("keywords-server")

# Initialize aggregator with all services

print(f" Initializing aggregator...")
aggregator = KeywordAggregator()
print(f" Aggregator initialized with {len(aggregator.services)} services")

@mcp.tool()
async def fetch_keywords(topic: str, product_name: str = None) -> dict:
    """
    Fetch high-ranking keywords from multiple sources
    
    Combines data from:
    - Google Search Console (your site data)
    - SerpAPI (Google search results)
    - More sources can be added easily
    """
    
    print(f"fetch_keywords called: {topic}")

    # Use aggregator to fetch from all sources
    result = await aggregator.fetch_all_keywords(topic, product_name)

    print(f" Result: {result}")

    return {
        "topic": topic,
        "keywords": result,
        "status": "success"
    }

@mcp.tool()
def analyze_competition(keyword: str) -> dict:
    """Analyze competition for a keyword"""
    # TODO: Implement competition analysis
    return {
        "keyword": keyword,
        "competition": "medium",
        "status": "success"
    }

@mcp.tool()
def get_trending_topics(category: str = "technology") -> dict:
    """Get trending topics"""
    # TODO: Implement trending topics
    return {
        "category": category,
        "trending": ["AI Agents", "Automation"],
        "status": "success"
    }

if __name__ == "__main__":
    print(" Starting Keywords MCP Server (Dynamic)")
    mcp.run()