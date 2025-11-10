"""
Configuration for Blog Agent
"""

import os
from typing import List
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # OpenAI/LLM Settings
    ASPOSE_LLM_BASE_URL: str
    ASPOSE_LLM_API_KEY: str
    ASPOSE_LLM_MODEL: str
    
    # MCP Servers
    KEYWORDS_MCP_URL: str
    SEO_MCP_URL: str
    FILE_GEN_MCP_URL: str
    
    # Paths
    PRODUCTS_JSON_PATH: str = os.path.join(os.path.dirname(__file__), '../data/products.json')
    OUTPUT_DIR: str = os.path.join(os.path.dirname(__file__), '../output/blogs')
    
    # CORS
    ALLOWED_ORIGINS: str = "http://localhost:3000"
    
    # Keyword Services
    GSC_CREDENTIALS_PATH: str = ""
    GSC_SITE_URL: str = ""
    SERPAPI_API_KEY: str
    
    # Agent Settings
    MAX_TOKENS: int = 5000
    TEMPERATURE: float = 0.7

    class Config:
        # Use local .env in dev, ignore if not present (CI/CD uses actual env)
        env_file = ".env"
        env_file_encoding = 'utf-8'

    def get_allowed_origins(self) -> List[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]

# Single settings instance
settings = Settings()
