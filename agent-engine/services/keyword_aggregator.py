"""
Keyword Aggregator
Combines results from multiple keyword services
"""

from .base_keyword_service import BaseKeywordService
from .gsc_keyword_service import GSCKeywordService
from .serpapi_keyword_service import SerpAPIKeywordService
from typing import Dict, List

class KeywordAggregator:
    """
    Aggregates keywords from multiple sources
    Plug & play - add/remove services easily
    """
    def __init__(self, services: List[BaseKeywordService] = None):
        """
        Initialize with keyword services
        
        Args:
            services: List of keyword services to use
                     If None, uses all available services
        """
        if services is None:
            self.services = []
            
            # Add GSC if configured
            gsc = GSCKeywordService()
            if gsc.is_available():
                self.services.append(gsc)
            
            # Add SerpAPI if configured
            serpapi = SerpAPIKeywordService()
            if serpapi.is_available():
                self.services.append(serpapi)
        else:
            self.services = services
    
    async def fetch_all_keywords(self, topic: str, product_name: str = None) -> Dict:
        """
        Fetch keywords from all available services and merge
        
        Args:
            topic: Topic to research
            product_name: Optional product context
            
        Returns:
            Aggregated keywords from all sources
        """
        print(f" Aggregator called with topic: {topic}")
        print(f"  Available services: {[s.get_service_name() for s in self.services]}")

        all_results = []
        
        # Fetch from all services
        for service in self.services:
            if service.is_available():
                print(f" Fetching keywords from {service.get_service_name()}...")
                try:
                    result = await service.fetch_keywords(topic, product_name)
                    all_results.append(result)
                except Exception as e:
                    print(f" Error from {service.get_service_name()}: {e}")
        
        # Merge results
        merged = self._merge_keywords(all_results)
        
        return merged
    
    def _merge_keywords(self, results: List[Dict]) -> Dict:
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