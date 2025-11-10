"""
Configuration for Blog Agent
"""

import os
from typing import List
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    ASPOSE_LLM_BASE_URL: str = "http://your-llm-server.com/v1"
    ASPOSE_LLM_API_KEY: str = "your-api-key"
    ASPOSE_LLM_MODEL: str = "gpt-oss-120b"
    
    # MCP Servers
    KEYWORDS_MCP_URL: str = "http://localhost:3001"
    SEO_MCP_URL: str = "http://localhost:3002"
    FILE_GEN_MCP_URL: str = "http://localhost:3003"
    
    # Paths
    PRODUCTS_JSON_PATH: str = "../data/products.json"
    OUTPUT_DIR: str = "../output/blogs"
    
    # CORS
    ALLOWED_ORIGINS: str = "http://localhost:3000"
    
    # NEW: Keyword Services
    GSC_CREDENTIALS_PATH: str = ""
    GSC_SITE_URL: str = ""
    SERPAPI_API_KEY: str = ""  # Add this!
    
    # Agent Settings
    MAX_TOKENS: int = 5000
    TEMPERATURE: float = 0.7
    
    class Config:
        env_file = ".env"
        
    def get_allowed_origins(self) -> List[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]

settings = Settings()