from pydantic_settings import BaseSettings
from typing import Dict, List, Tuple
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()  # loads .env from project root by default


class Settings(BaseSettings):
    ASPOSE_LLM_BASE_URL: str | None = None
    ASPOSE_LLM_API_KEY: str | None = None

    # Standard OpenAI key (used when no custom base URL is set)
    OPENAI_API_KEY: str | None = None

    # --- Model defaults ---
    ASPOSE_LLM_MODEL: str = "gpt-oss"

    # --- SerpAPI integration ---
    SERPAPI_API_KEY: str | None = None
    SERPAPI_ENGINE: str = "google"  # we’ll use standard Google search

    # --- KRA scoring / data dirs (unchanged) ---
    W_VOLUME: float = 0.35
    W_KD: float = 0.25
    W_CPC: float = 0.15
    W_BRAND: float = 0.15
    W_INTENT: float = 0.10
    TOP_CLUSTERS: int = 15
    MAX_ROWS: int = 50000    
    KRA_DATA_DIR: str = "./content"
    KRA_OUTPUT_DIR: str = "./content"
    BLOG_CONTENT_ROOT: str = ""
    KRA_METRICS_DB_PATH: str = "./src/data/kra_metrics_db.json"
    DEBUG: bool = False

    # --- NEW: Metrics / Google Apps Script webhook ---
    METRICS_WEBHOOK_URL: str = "https://script.google.com/macros/s/AKfycbyCHwElrM6RcYLi0JNQAkJmzGrBjAhf28mKXVyub_6SdaZ2ITvzCwfM5xCLE7rmuxio/exec"
    METRICS_TOKEN: str = ""
    METRICS_AGENT_NAME: str = "Keyword Analyzer"
    METRICS_AGENT_OWNER: str = "Muzammil Khan"
    METRICS_KEYWORD_CLUSTERING_JOB: str = "Keyword Clustering"
    METRICS_TOPIC_GENERATION_JOB: str = "Topics Generation"

    # --- Internal Blog Teams Metrics / Google Apps Script webhook ---
    INT_METRICS_WEBHOOK_URL: str = "https://script.google.com/macros/s/AKfycbwYyPBs3ox6xhYfznVpu4Gh8T4l7cXrAIj1m_y1g-vWn6tyP_LAkv3eo6W2EZYAeHgLag/exec"
    INT_METRICS_TOKEN: str = "-2026"

settings = Settings()

BRAND_METRICS: dict[str, Tuple[str, str]] = {
    # key: normalized brand (lowercase)
    "aspose": ("aspose.com", "Blog"),
    "groupdocs": ("groupdocs.com", "Blog"),
    "asposecloud": ("aspose.cloud", "Blog"),
    "groupdocscloud": ("groupdocs.cloud", "Blog"),
    "conholdate": ("conholdate.com", "Blog"),
    "familiarize": ("familiarize.com", "Blog"),
    # add more brands here...
}
platform_LABELS: Dict[str, str] = {
    "python": "Python",
    "java": "Java",
    "c#": "C#",
    "c++": "C++",
    "php": "PHP",
    "javascript": "JavaScript",
    "nodejs": "Node.js",
}

# Canonical platform -> list of patterns to search for
platform_PATTERNS: Dict[str, List[str]] = {
    "python": ["python"],
    "java": ["java"],
    "c#": ["c#", "csharp", "c-sharp", "dotnet", ".net", "asp.net", "vb.net"],
    "c++": ["c++", "cpp"],
    "php": ["php"],
    "javascript": ["javascript", "js"],
    "nodejs": ["node.js", "nodejs", "node js"],
    # you can add more later: "go": ["golang", "go "], etc.
}