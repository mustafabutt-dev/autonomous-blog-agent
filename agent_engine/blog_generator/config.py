"""
Configuration for Blog Agent
"""
import os, sys
from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings
from pydantic import ConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]
ENV_PATH = BASE_DIR / ".env"

class Settings(BaseSettings):
    model_config = ConfigDict(
        env_file=ENV_PATH,
        env_file_encoding="utf-8"
    )

    ASPOSE_LLM_BASE_URL: str = "http://your-llm-server.com/v1"
    ASPOSE_LLM_API_KEY: str = "your-api-key"
    ASPOSE_LLM_MODEL: str = "gpt-oss"
    GIST_NAME: str = "mustafabutt"
    REPO_PAT: str = ""
    # Paths
    PRODUCTS_JSON_PATH: str = "../data/products.json"
    OUTPUT_DIR: str = "../output/blogs"

    GOOGLE_SCRIPT_URL_FOR_TEAM = os.getenv("GOOGLE_SCRIPT_URL_FOR_TEAM", "")
    TOKEN_FOR_TEAM = os.getenv("TOKEN_FOR_TEAM", "")
    
    GOOGLE_SCRIPT_URL_FOR_PROD = os.getenv("GOOGLE_SCRIPT_URL_FOR_PROD", "")
    TOKEN_FOR_PROD = os.getenv("TOKEN_FOR_PROD", "")

    print(f"Config loaded - TEAM URL set: {bool(GOOGLE_SCRIPT_URL_FOR_TEAM)}")
    print(f"Config loaded - PROD URL set: {bool(GOOGLE_SCRIPT_URL_FOR_PROD)}")
    
    # Agent Settings
    NUMBER_OF_BLOG_WORDS: int = 6  # FIX: must be int, cannot be "5-7"
    ENVIRONMENT: str = ""
    KRA_DATA_DIR: str = "./src/data/samples"
    KRA_OUTPUT_DIR: str = "./src/data/outputs"
    TOP_CLUSTERS: int = 10
    MAX_ROWS: int = 50000
    DEBUG: bool = False
    # Optional value which your helper method uses
    ALLOWED_ORIGINS: str = "*"

    def get_allowed_origins(self) -> List[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]


settings = Settings()
