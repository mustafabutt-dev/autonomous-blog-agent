from __future__ import annotations
from typing import List, Optional, Literal, Dict
from pydantic import BaseModel, Field, validator

class KeywordRecord(BaseModel):
    keyword: str
    source: Literal["upload"]
    locale: str = "en-US"
    volume: Optional[int] = None
    cpc: Optional[float] = None
    kd: Optional[float] = None
    clicks: Optional[float] = None
    url: Optional[str] = None
    competition: Optional[float] = None
    competition_label: Optional[str] = None
    @validator("keyword")
    def norm_kw(cls, v: str) -> str:
        return v.strip().lower()

class ClusterMetrics(BaseModel):
    avg_volume: float = 0.0
    avg_kd: float = 0.0
    avg_cpc: float = 0.0
    brand_fit: float = 0.0
    intent: Literal["informational","commercial","transactional","navigational"] = "informational"
    score: float = 0.0
    avg_competition: Optional[float] = None

class Cluster(BaseModel):
    cluster_id: str
    label: str
    members: List[KeywordRecord]
    metrics: ClusterMetrics

class TopicIdea(BaseModel):
    cluster_id: str
    title: str
    angle: str
    outline: List[str]
    target_persona: str
    primary_keyword: str
    supporting_keywords: List[str]
    internal_links: List[str] = []

class RunRequest(BaseModel):
    brand: str = "Aspose"
    product: str = "Aspose.Cells"
    locale: str = "en-US"
    file_path: str = "/mnt/data/keywords.csv"
    clustering_k: int | None = None
    top_clusters: int = 10
    max_rows: int = 50000
    weights: Dict[str, float] = Field(
        default_factory=lambda: {
            "volume": 0.35, "kd": 0.25, "cpc": 0.15, "brand": 0.15, "intent": 0.10
        }
    )

class RunResult(BaseModel):
    run_id: str
    brand: str
    product: str
    locale: str
    clusters: List[Cluster]
    topics: List[TopicIdea]
