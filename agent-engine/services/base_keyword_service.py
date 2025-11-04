"""
Base abstract class for all keyword research services
"""

from abc import ABC, abstractmethod
from typing import Dict, List

class BaseKeywordService(ABC):
    """
    Abstract base class for keyword research services
    All keyword services must implement this interface
    """
    
    @abstractmethod
    async def fetch_keywords(self, topic: str, product_name: str = None) -> Dict:
        """
        Fetch keywords for a given topic
        
        Args:
            topic: The topic to research
            product_name: Optional product name for context
            
        Returns:
            Dictionary with structure:
            {
                "source": "service_name",
                "primary": ["keyword1", "keyword2", ...],
                "secondary": ["keyword3", "keyword4", ...],
                "long_tail": ["keyword5", ...],
                "metadata": {...}
            }
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if this service is configured and available
        
        Returns:
            True if service can be used, False otherwise
        """
        pass
    
    def get_service_name(self) -> str:
        """
        Get the name of this service
        
        Returns:
            Service name as string
        """
        return self.__class__.__name__