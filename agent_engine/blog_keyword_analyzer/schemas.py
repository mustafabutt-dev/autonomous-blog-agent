from __future__ import annotations

from typing import List, Optional, Literal, Dict

from pydantic import BaseModel, Field, validator


class KeywordRecord(BaseModel):
    """
    One row of keyword data imported from the source file (GKP, etc.).
    The `keyword` is normalized to lowercase for consistent clustering.
    """

    keyword: str
    source: Literal["upload", "serpapi"]
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
        # Normalize for clustering & deduplication
        return v.strip().lower()


class ClusterMetrics(BaseModel):
    """
    Aggregated metrics for a cluster of keywords.
    These are used to score and rank clusters.
    """

    avg_volume: float = 0.0
    avg_kd: float = 0.0
    avg_cpc: float = 0.0
    brand_fit: float = 0.0
    intent: Literal["informational", "commercial", "transactional", "navigational"] = "informational"
    score: float = 0.0
    avg_competition: Optional[float] = None


class Cluster(BaseModel):
    """
    Represents a cluster of related keywords plus its aggregate metrics.
    """

    cluster_id: str
    label: str
    members: List[KeywordRecord]
    metrics: ClusterMetrics


class TopicIdea(BaseModel):
    """
    Final topic proposal produced by the LLM.
    This is what the consumer agent / UI will work with.
    """

    cluster_id: str
    title: str
    angle: str
    outline: List[str]
    target_persona: str
    primary_keyword: str
    supporting_keywords: List[str]
    internal_links: List[str] = []


class RunRequest(BaseModel):
    """
    Input configuration passed into the orchestration runner.

    Note:
      - `file_path` may be an empty string to let the importer search defaults.
      - `weights` allow overriding the default scoring weights if needed.
    """

    brand: str = "Aspose"
    product: str = "Aspose.Cells"
    locale: str = "en-US"
    file_path: str = "/mnt/data/keywords.csv"
    clustering_k: int | None = None
    top_clusters: int = 10
    max_rows: int = 50000
    weights: Dict[str, float] = Field(
        default_factory=lambda: {
            "volume": 0.35,
            "kd": 0.25,
            "cpc": 0.15,
            "brand": 0.15,
            "intent": 0.10,
        }
    )


class RunResult(BaseModel):
    """
    Aggregate result returned by the runner:
      - run_id: opaque identifier (useful for logs and file names)
      - clusters: top clusters (already scored and sorted)
      - topics: generated TopicIdea objects
    """

    run_id: str
    brand: str
    product: str
    locale: str
    clusters: List[Cluster]
    topics: List[TopicIdea]


class ExistingPost(BaseModel):
    """
    Minimal structure used to represent posts discovered in the content index.

    This is what we pass around when deduplicating topics against existing blogs.
    """

    title: str
    slug: str
    url: str
    product: Optional[str] = None
    platform: Optional[str] = None
    rel_path: Optional[str] = None
