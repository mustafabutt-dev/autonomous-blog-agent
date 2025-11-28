"""
Configuration for Blog Agent
"""

import os
from typing import List
from pydantic_settings import BaseSettings
from pydantic import ConfigDict


class Settings(BaseSettings):
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )

    ASPOSE_LLM_BASE_URL: str = "http://your-llm-server.com/v1"
    ASPOSE_LLM_API_KEY: str = "your-api-key"
    ASPOSE_LLM_MODEL: str = "gpt-oss"
    
    # Paths
    PRODUCTS_JSON_PATH: str = "../data/products.json"
    OUTPUT_DIR: str = "../output/blogs"
    
    SERPAPI_API_KEY: str = ""  # Add this!
    
    # Agent Settings
    NUMBER_OF_BLOG_SECTIONS: int = 5  # FIX: must be int, cannot be "5-7"

    KRA_DATA_DIR: str = "./src/data/samples"
    KRA_OUTPUT_DIR: str = "./src/data/outputs"

    # Optional value which your helper method uses
    ALLOWED_ORIGINS: str = "*"

    def get_allowed_origins(self) -> List[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]


settings = Settings()
