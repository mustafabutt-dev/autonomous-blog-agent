"""
SerpAPI Keyword Service
Fetches keyword suggestions from Google search results
"""

from .base_keyword_service import BaseKeywordService
from typing import Dict, List
import os
import httpx

class SerpAPIKeywordService(BaseKeywordService):
    """
    Fetch keywords using SerpAPI
    Free tier: 100 searches/month
    """
    
    def __init__(self):
        self.api_key = os.getenv("SERPAPI_API_KEY")
        self.base_url = "https://serpapi.com/search"
    
    def is_available(self) -> bool:
        """Check if SerpAPI key is configured"""
        available = bool(self.api_key)
        if not available:
            print("  SerpAPI not configured - set SERPAPI_API_KEY")
        return available
    
    async def fetch_keywords(self, topic: str, product_name: str = None) -> Dict:
        """
        Fetch keywords from SerpAPI
        
        Gets:
        - Related searches
        - People also ask questions
        - Auto-complete suggestions
        """
        
        if not self.is_available():
            return self._empty_result()
        
        try:
            search_query = topic
            if product_name:
                search_query = f"{topic} {product_name}"
            
            # Make API call to SerpAPI
            params = {
                "q": search_query,
                "api_key": self.api_key,
                "engine": "google",
                "google_domain": "google.com",
                "gl": "us",
                "hl": "en"
            }
            
            print(f" Calling SerpAPI for: {search_query}")
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(self.base_url, params=params)
                response.raise_for_status()
                data = response.json()
            

            print(f"SerpAPI Response Keys: {data.keys()}")
            print(f" Organic Results: {len(data.get('organic_results', []))}")
            print(f" Related Searches: {data.get('related_searches', [])}")
            print(f" People Also Ask: {len(data.get('related_questions', []))}")

            # Extract keywords from different sections
            primary = self._extract_primary_keywords(data, topic)
            secondary = self._extract_related_searches(data)
            long_tail = self._extract_people_also_ask(data)
            
            print(f" Extracted Primary: {primary}")
            print(f" Extracted Secondary: {secondary}")
            print(f" Extracted Long-tail: {long_tail}")

            return {
                "source": "SerpAPI",
                "primary": primary,
                "secondary": secondary,
                "long_tail": long_tail,
                "metadata": {
                    "total_keywords": len(primary) + len(secondary) + len(long_tail),
                    "search_results": len(data.get("organic_results", [])),
                    "credits_used": 1
                }
            }
            
        except httpx.HTTPStatusError as e:
            print(f" SerpAPI HTTP Error: {e.response.status_code} - {e.response.text}")
            return self._empty_result()
        except Exception as e:
            print(f" SerpAPI Error: {e}")
            return self._empty_result()
    
    def _extract_primary_keywords(self, data: dict, topic: str) -> List[str]:
        """Extract primary keywords from organic results"""
        keywords = [topic]
        
        # Get from organic results titles
        organic = data.get("organic_results", [])
        for result in organic[:5]:
            title = result.get("title", "")
            # Extract meaningful phrases from titles
            if title:
                keywords.append(title)
        
        return keywords[:5]
    
    def _extract_related_searches(self, data: dict) -> List[str]:
        """Extract related searches"""
        related = data.get("related_searches", [])
        keywords = [item.get("query", "") for item in related if item.get("query")]
        return keywords[:8]
    
    def _extract_people_also_ask(self, data: dict) -> List[str]:
        """Extract People Also Ask questions as long-tail keywords"""
        paa = data.get("related_questions", [])
        questions = [item.get("question", "") for item in paa if item.get("question")]
        return questions[:7]
    
    def _empty_result(self) -> Dict:
        """Return empty result when service unavailable"""
        return {
            "source": "SerpAPI",
            "primary": [],
            "secondary": [],
            "long_tail": [],
            "metadata": {"available": False}
        }