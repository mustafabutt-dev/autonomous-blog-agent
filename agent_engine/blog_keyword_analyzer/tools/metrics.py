# src/agent_engine/kra/tools/metrics.py
from __future__ import annotations

import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class RunMetrics:
    """
    In-memory metrics collector for a single Blog Keyword Analyzer run.
    """

    # --- Agent identity ---
    agent_name: str = "Blog Keyword Analyzer"
    agent_owner: str = "MZK"
    job_type: str = "Keyword Analysis and Topic Generation"

    # --- Run identity / context ---
    run_id: str = ""
    brand: str = ""
    product: str = ""
    locale: str = ""
    platform: Optional[str] = None
    file_path: Optional[str] = None

    # --- Volume / count metrics ---
    # renamed from keywords_imported -> keywords_processed
    keywords_processed: int = 0
    keywords_after_preprocess: int = 0
    keywords_clustered: int = 0
    keywords_not_clustered: int = 0
    clusters_created: int = 0
    clusters_used_for_topics: int = 0
    topics_generated_raw: int = 0
    topics_after_dedup: int = 0
    existing_topics_loaded: int = 0
    duplicates_dropped: int = 0

    # --- LLM / content-index metrics ---
    llm_requests: int = 0
    llm_failures: int = 0
    llm_duration_seconds: float = 0.0

    content_index_requests: int = 0
    content_index_failures: int = 0
    content_index_duration_seconds: float = 0.0

    # Optional future: token usage
    llm_prompt_tokens: int = 0
    llm_completion_tokens: int = 0

    # --- Aggregated cluster score stats ---
    cluster_score_min: Optional[float] = None
    cluster_score_max: Optional[float] = None
    cluster_score_avg: Optional[float] = None

    # --- Timing ---
    run_started_at: float = field(default_factory=time.perf_counter)
    run_duration_seconds: Optional[float] = None
    step_durations: Dict[str, float] = field(default_factory=dict)

    # --- Events / status ---
    events: List[Dict[str, Any]] = field(default_factory=list)
    success: bool = True
    error_message: Optional[str] = None

    # -------------------------------------------------------------------------
    # Basic API
    # -------------------------------------------------------------------------

    def record_step_duration(self, step_name: str, duration_seconds: float) -> None:
        current = self.step_durations.get(step_name, 0.0)
        self.step_durations[step_name] = current + duration_seconds

    def mark_llm_call(self, duration_seconds: float, failed: bool = False) -> None:
        self.llm_requests += 1
        self.llm_duration_seconds += duration_seconds
        if failed:
            self.llm_failures += 1

    def mark_content_index_call(self, duration_seconds: float, failed: bool = False) -> None:
        self.content_index_requests += 1
        self.content_index_duration_seconds += duration_seconds
        if failed:
            self.content_index_failures += 1

    def add_event(self, event_type: str, message: str, **kwargs: Any) -> None:
        self.events.append(
            {
                "ts": time.time(),
                "type": event_type,
                "message": message,
                **kwargs,
            }
        )

    def set_cluster_score_stats(self, scores: List[float]) -> None:
        if not scores:
            return
        self.cluster_score_min = min(scores)
        self.cluster_score_max = max(scores)
        self.cluster_score_avg = sum(scores) / len(scores)

    def finish(self, success: bool = True, error_message: Optional[str] = None) -> None:
        self.run_duration_seconds = time.perf_counter() - self.run_started_at
        self.success = success
        self.error_message = error_message

    def as_dict(self) -> Dict[str, Any]:
        """
        Serialize metrics into a plain dict suitable for logging / JSON export.
        """
        return {
            "agent_name": self.agent_name,
            "agent_owner": self.agent_owner,
            "job_type": self.job_type,
            "run_id": self.run_id,
            "brand": self.brand,
            "product": self.product,
            "locale": self.locale,
            "platform": self.platform,
            "file_path": self.file_path,
            "keywords_processed": self.keywords_processed,
            "keywords_after_preprocess": self.keywords_after_preprocess,
            "keywords_clustered": self.keywords_clustered,
            "keywords_not_clustered": self.keywords_not_clustered,
            "clusters_created": self.clusters_created,
            "clusters_used_for_topics": self.clusters_used_for_topics,
            "topics_generated_raw": self.topics_generated_raw,
            "topics_after_dedup": self.topics_after_dedup,
            "existing_topics_loaded": self.existing_topics_loaded,
            "duplicates_dropped": self.duplicates_dropped,
            "llm_requests": self.llm_requests,
            "llm_failures": self.llm_failures,
            "llm_duration_seconds": self.llm_duration_seconds,
            "llm_prompt_tokens": self.llm_prompt_tokens,
            "llm_completion_tokens": self.llm_completion_tokens,
            "content_index_requests": self.content_index_requests,
            "content_index_failures": self.content_index_failures,
            "content_index_duration_seconds": self.content_index_duration_seconds,
            "cluster_score_min": self.cluster_score_min,
            "cluster_score_max": self.cluster_score_max,
            "cluster_score_avg": self.cluster_score_avg,
            "run_duration_seconds": self.run_duration_seconds,
            "step_durations": self.step_durations,
            "success": self.success,
            "error_message": self.error_message,
        }

    def as_cli_summary(self) -> str:
        """
        Human-readable multiline summary for CLI output.
        """
        lines: List[str] = []

        # 🔹 Header as requested
        lines.append(f"agent_name          : {self.agent_name}")
        lines.append(f"agent_owner         : {self.agent_owner}")
        lines.append(f"job_type            : {self.job_type}")
        lines.append("")  # blank line

        lines.append("Metrics summary:")
        lines.append(f"  - run_id              : {self.run_id}")
        lines.append(f"  - brand/product       : {self.brand} / {self.product}")
        if self.platform:
            lines.append(f"  - platform           : {self.platform}")
        if self.file_path:
            lines.append(f"  - file_path           : {self.file_path}")

        # Volumes
        lines.append(f"  - keywords_processed  : {self.keywords_processed}")
        lines.append(f"  - keywords_after_preprocess  : {self.keywords_after_preprocess}")
        lines.append(f"  - keywords_clustered  : {self.keywords_clustered}")
        lines.append(f"  - keywords_not_clustered  : {self.keywords_not_clustered}")
        lines.append(f"  - clusters_created    : {self.clusters_created}")
        lines.append(f"  - clusters_used       : {self.clusters_used_for_topics}")
        lines.append(f"  - topics_generated_raw: {self.topics_generated_raw}")
        lines.append(f"  - topics_after_dedup  : {self.topics_after_dedup}")
        lines.append(f"  - existing_topics     : {self.existing_topics_loaded}")
        lines.append(f"  - duplicates_dropped  : {self.duplicates_dropped}")

        # LLM / content index
        lines.append(f"  - llm_requests        : {self.llm_requests}")
        lines.append(f"  - llm_failures        : {self.llm_failures}")
        lines.append(f"  - llm_duration_total  : {self.llm_duration_seconds:.3f} s")
        lines.append(f"  - llm_prompt_tokens   : {self.llm_prompt_tokens}")
        lines.append(f"  - llm_completion_tokens  : {self.llm_completion_tokens}")
        total_tokens = self.llm_prompt_tokens + self.llm_completion_tokens
        lines.append(f"  - llm_total_tokens    : {total_tokens}")
        lines.append(f"  - content_index_calls : {self.content_index_requests}")
        lines.append(f"  - content_index_errs  : {self.content_index_failures}")
        lines.append(f"  - content_index_time  : {self.content_index_duration_seconds:.3f} s")

        # Cluster scores
        if self.cluster_score_min is not None:
            lines.append(
                "  - cluster_scores      : "
                f"min={self.cluster_score_min:.4f} "
                f"max={self.cluster_score_max:.4f} "
                f"avg={self.cluster_score_avg:.4f}"
            )

        # Timings
        if self.run_duration_seconds is not None:
            lines.append(f"  - run_duration        : {self.run_duration_seconds:.3f} s")
        if self.step_durations:
            lines.append("  - step_durations:")
            for name, dur in self.step_durations.items():
                lines.append(f"      * {name:<16}: {dur:.3f} s")

        # Status
        lines.append(f"  - success             : {self.success}")
        if self.error_message:
            lines.append(f"  - error_message       : {self.error_message}")

        return "\n".join(lines)


@contextmanager
def timed_step(metrics: RunMetrics, step_name: str):
    """
    Context manager to measure duration of a pipeline step.

    Usage:
        with timed_step(metrics, "import"):
            records = import_file(req)
    """
    t0 = time.perf_counter()
    try:
        yield
    finally:
        dt = time.perf_counter() - t0
        metrics.record_step_duration(step_name, dt)
