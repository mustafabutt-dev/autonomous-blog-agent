"""
Configuration for Blog Agent
"""

import os
from typing import List
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    ASPOSE_LLM_BASE_URL: str = "http://your-llm-server.com/v1"
    ASPOSE_LLM_API_KEY: str = "your-api-key"
    ASPOSE_LLM_MODEL: str = "gpt-oss"
    
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
    NUMBER_OF_BLOG_SECTIONS: int = 5-7
    MAX_TOKENS: int = 5000
    TEMPERATURE: float = 0.7
    
    CUSTOM_LLM_BASE_URL: str | None = None
    CUSTOM_LLM_API_KEY: str | None = None

    # --- KRA scoring / data dirs (unchanged) ---
    W_VOLUME: float = 0.35
    W_KD: float = 0.25
    W_CPC: float = 0.15
    W_BRAND: float = 0.15
    W_INTENT: float = 0.10
    TOP_CLUSTERS: int = 10
    MAX_ROWS: int = 50000
    KRA_DATA_DIR: str = "./src/data/samples"
    KRA_OUTPUT_DIR: str = "./src/data/outputs"
    DEBUG: bool = False

    class Config:
        # Use local .env in dev, ignore if not present (CI/CD uses actual env)
        env_file = ".env"
        env_file_encoding = 'utf-8'

    def get_allowed_origins(self) -> List[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]

settings = Settings()