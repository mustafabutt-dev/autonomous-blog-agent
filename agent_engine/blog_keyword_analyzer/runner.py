# src/agents/kra/runner.py
from __future__ import annotations

import argparse
import json
import logging
import re
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Optional, List, Mapping, Any, Dict, Tuple
import requests

from .metrics_sender import send_stage_metrics
from .tools.content_index import get_existing_posts
from .schemas import RunRequest, RunResult, Cluster, KeywordRecord
from .agent import KeywordResearchAgent
from .tools.file_import import import_file
from .tools.preprocess import preprocess
from .tools.cluster import cluster_records
from .tools.intent_brand import annotate_intent_brand
from .tools.scoring import score_clusters
from .config import settings, BRAND_METRICS
from .tools.metrics import RunMetrics, timed_step

logger = logging.getLogger(__name__)


def _project_root(start: Optional[Path] = None) -> Path:
    """
    Walk up from 'start' (or CWD) to find a directory containing pyproject.toml or .git.

    This keeps paths robust across local dev, containers, or CI.
    """
    p = (start or Path.cwd()).resolve()
    for _ in range(10):
        if (p / "pyproject.toml").exists() or (p / ".git").exists():
            return p
        if p.parent == p:
            break
        p = p.parent
    return Path.cwd().resolve()

def _resolve_brand_output_dir(brand_folder: str) -> Path:
    root = _project_root()
    out_dir = (root / "content" / brand_folder / "output").resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir

def _resolve_output_dir() -> Path:
    """
    Resolve KRA_OUTPUT_DIR from settings, making it absolute relative to project root.
    Ensures the directory exists.
    """
    root = _project_root()
    out_dir = Path(settings.KRA_OUTPUT_DIR)
    if not out_dir.is_absolute():
        out_dir = (root / out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir

def _resolve_input_file(path_str: str | None) -> Optional[Path]:
    """
    Resolve the input file if explicitly provided via --file.

    Behavior:
      - If path_str is falsy (None / ""), return None (caller may use defaults).
      - If path_str is given but file does NOT exist -> raise FileNotFoundError.
      - Relative paths are resolved against project root for consistency.
    """
    if not path_str:
        return None

    root = _project_root()
    p = Path(path_str)

    if not p.is_absolute():
        p = (root / p).resolve()

    if not p.exists():
        raise FileNotFoundError(f"Input --file not found at: {p}")

    return p

def _get_metrics_db_path(default_dir: Path) -> Path:
    """
    Return the path to the metrics DB JSON.

    If KRA_METRICS_DB_PATH is set (via settings), use that.
    Otherwise, default to <default_dir>/kra_metrics_db.json.
    """
    if settings.KRA_METRICS_DB_PATH:
        return Path(settings.KRA_METRICS_DB_PATH).resolve()
    return default_dir / "kra_metrics_db.json"

def _normalize_topic_key(text: str) -> str:
    """
    Normalize a text (title/url/slug) into a comparable key:
      - lowercase
      - only alphanumeric + single hyphens
    """
    s = text.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s

def _brand_slug(brand: str) -> str:
    return _normalize_topic_key(brand or "unknown")

def _canonical_platform(platform: Optional[str]) -> Optional[str]:
    """
    Normalize platform names so they match what blog tools use, e.g. 'csharp'.

    Examples:
      'C#', 'c-sharp', 'dotnet', '.net', 'asp.net' -> 'csharp'
    """
    if not platform:
        return None
    f = platform.lower().strip()
    if f in {"c#", "c-sharp", "dotnet", ".net", "asp.net"}:
        return "csharp"
    return f

def _derive_product_code(product: str) -> str:
    """
    Generic product normalizer that does NOT assume any brand.
    We derive a short code from the last token (dot/space separated).

    Examples:
        'Aspose.Cells'   -> 'cells'
        'Aspose Cells'   -> 'cells'
        'cells'          -> 'cells'
    """
    p = (product or "").strip().lower()
    if not p:
        return ""
    tokens = re.split(r"[.\s/\\_-]+", p)
    tokens = [t for t in tokens if t]
    if not tokens:
        return p
    return tokens[-1]

def _load_existing_topics_for_prompt(
    product: str,
    platform: Optional[str],
    use_content_index: bool = True,
) -> List[dict]:
    """
    Use content index service to load existing blogs for a given product + platform.

    If use_content_index is False, this function returns [] and does NOT call
    the content index at all.
    """
    if not use_content_index:
        logger.info(
            "Content index lookup disabled (use_content_index=False); skipping existing topic search."
        )
        return []

    product_code = _derive_product_code(product)
    fw_canonical = _canonical_platform(platform)

    logger.info(
        "Loading existing topics for product=%r -> product_code=%r, platform=%r -> fw_canonical=%r",
        product,
        product_code,
        platform,
        fw_canonical,
    )

    try:
        entries = get_existing_posts(product=product_code, platform=fw_canonical)
    except Exception as e:
        logger.warning("Failed to search existing blogs: %s", e, exc_info=True)
        return []

    logger.info("Content index returned %d raw entries.", len(entries))

    topics_for_prompt: List[dict] = []

    for e in entries:
        # e may be a Pydantic model (ExistingPost) or a plain dict.
        if hasattr(e, "dict"):  # Pydantic BaseModel-style
            data: Mapping[str, Any] = e.dict()
        elif isinstance(e, Mapping):
            data = e
        else:
            # Fallback: try __dict__, or skip with a warning
            data = getattr(e, "__dict__", {})
            logger.debug("ExistingPost entry is non-mapping type %r; using __dict__", type(e))

        topics_for_prompt.append(
            {
                "title": (data.get("title") or "").strip(),
                "url": data.get("url"),
                "slug": data.get("slug"),
                "platforms": data.get("platforms"),
            }
        )

    logger.info(
        "Loaded %d existing topics from content index (after shaping).",
        len(topics_for_prompt),
    )

    for sample in topics_for_prompt[:5]:
        logger.info(
            "Existing topic: title=%r slug=%r platforms=%r",
            sample.get("title"),
            sample.get("slug"),
            sample.get("platforms"),
        )

    return topics_for_prompt

def _build_existing_keys(existing_topics: List[dict]) -> set[str]:
    """
    Build a set of normalized keys from existing topics (url/title/slug).
    Used for post-filtering as a safety net.
    """
    keys: set[str] = set()
    for e in existing_topics:
        for field in ("url", "title", "slug"):
            val = e.get(field)
            if val:
                keys.add(_normalize_topic_key(str(val)))
                break
    return keys

def _filter_duplicate_topics(
    topics,
    existing_topics: List[dict],
):
    """
    Drop any generated topics whose normalized title matches an existing topic key.
    """
    existing_keys = _build_existing_keys(existing_topics)
    if not existing_keys:
        return topics

    filtered = []
    dropped = 0
    for t in topics:
        title = getattr(t, "title", "") or ""
        key = _normalize_topic_key(title)
        if key in existing_keys:
            dropped += 1
            continue
        filtered.append(t)

    logger.info(
        "Duplicate filter: kept=%d dropped=%d (existing_keys=%d)",
        len(filtered),
        dropped,
        len(existing_keys),
    )

    return filtered

def _summarize_cluster_scores(clusters: List[Cluster]) -> dict:
    """
    Compute simple summary statistics for cluster scores.
    """
    scores = [c.metrics.score for c in clusters if c.metrics is not None]
    if not scores:
        return {"count": 0, "min": None, "max": None, "avg": None}
    return {
        "count": len(scores),
        "min": min(scores),
        "max": max(scores),
        "avg": mean(scores),
    }

def write_topics_markdown(
    result: RunResult,
    output_dir: Path,
    platform: Optional[str] = None,
) -> Path:
    """
    Write a Markdown file with the generated topics for this run.
    Example: <runid>_<product>_<platform>_topics.md
    """
    # Respect the caller-provided output_dir (workflow sets KRA_OUTPUT_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)

    safe_product = _brand_slug(result.product)
    safe_platform = _brand_slug(platform or "all")

    run_suffix = result.run_id[:8] if result.run_id else "run"
    md_path = output_dir / f"{run_suffix}_{safe_product}_{safe_platform}_topics.md"
    print(md_path)

    lines: List[str] = []
    heading = f"# Blog Topics for {result.product} ({result.locale})"
    lines.append(heading)
    lines.append("")
    lines.append(f"- **Brand:** {result.brand}")
    lines.append(f"- **Product:** {result.product}")
    lines.append(f"- **Platform:** {result.platform}")
    lines.append(f"- **Run ID:** {result.run_id}")
    lines.append(f"- **Topics:** {len(result.topics)}")
    lines.append("")
    lines.append("---")
    lines.append("")

    for idx, t in enumerate(result.topics, start=1):
        title = getattr(t, "title", None) or t.get("title")
        cluster_id = getattr(t, "cluster_id", None) or t.get("cluster_id")
        angle = getattr(t, "angle", None) or t.get("angle")
        primary_kw = getattr(t, "primary_keyword", None) or t.get("primary_keyword")
        supporting_kws = getattr(t, "supporting_keywords", None) or t.get("supporting_keywords") or []
        outline = getattr(t, "outline", None) or t.get("outline") or []
        persona = getattr(t, "target_persona", None) or t.get("target_persona")

        lines.append(f"## {idx}. {title}")
        if cluster_id is not None:
            lines.append(f"- **Cluster ID:** `{cluster_id}`")
        if persona:
            lines.append(f"- **Target persona:** {persona}")
        if angle:
            lines.append(f"- **Angle:** {angle}")
        if primary_kw:
            lines.append(f"- **Primary keyword:** `{primary_kw}`")
        if supporting_kws:
            sk = ", ".join(f"`{kw}`" for kw in supporting_kws)
            lines.append(f"- **Supporting keywords:** {sk}")

        if outline:
            lines.append("")
            lines.append("**Suggested outline:**")
            for bullet in outline:
                lines.append(f"- {bullet}")

        lines.append("")
        lines.append("---")
        lines.append("")

    md_path.write_text("\n".join(lines), encoding="utf-8")
    logger.info("Saved topics markdown to %s", md_path)
    return md_path

def append_metrics_db_entry(
    result: RunResult,
    metrics: RunMetrics,
    output_dir: Path,
    metrics_db_path: Path | None = None,
) -> Path:
    """
    Append a single run's metrics to a small JSON 'DB' file.

    File: kra_metrics_db.json
    Structure:
    {
      "runs": [
        {
          "run_id": "...",
          "timestamp": "...",
          "brand": "...",
          "product": "...",
          "platform": "...",
          "locale": "...",
          "input_file": "...",
          "num_clusters": 10,
          "num_topics": 42,
          "llm_prompt_tokens": 1234,
          "llm_completion_tokens": 567,
          "llm_total_tokens": 1801,
          "wall_time_seconds": 12.34
        },
        ...
      ]
    }
    """
    if metrics_db_path is None:
        metrics_db_path = output_dir / "kra_metrics_db.json"

    db_path = metrics_db_path

    # Load existing DB if present
    if db_path.is_file():
        try:
            db = json.loads(db_path.read_text(encoding="utf-8"))
        except Exception:
            logger.warning("Failed to parse existing metrics DB; recreating: %s", db_path)
            db = {"runs": []}
    else:
        db = {"runs": []}

    # Safely pull fields from metrics (they may or may not exist)
    brand = getattr(metrics, "brand", None)
    product = getattr(metrics, "product", None)
    platform = getattr(metrics, "platform", None)  # may be None
    file_path = getattr(metrics, "file_path", None)

    # Volumes
    keywords_processed = getattr(metrics, "keywords_processed", None)
    clusters_created = getattr(metrics, "clusters_created", None)
    clusters_used = getattr(metrics, "clusters_used_for_topics", None)
    topics_generated_raw = getattr(metrics, "topics_generated_raw", None)
    topics_after_dedup = getattr(metrics, "topics_after_dedup", None)
    existing_topics = getattr(metrics, "existing_topics_loaded", None)
    duplicates_dropped = getattr(metrics, "duplicates_dropped", None)

    # LLM / content index
    llm_requests = getattr(metrics, "llm_requests", None)
    llm_failures = getattr(metrics, "llm_failures", None)

    content_index_calls = getattr(metrics, "content_index_requests", None)
    content_index_errs = getattr(metrics, "content_index_failures", None)
    content_index_time = getattr(metrics, "content_index_duration_seconds", None)

    llm_prompt_tokens = getattr(metrics, "llm_prompt_tokens", None)
    llm_completion_tokens = getattr(metrics, "llm_completion_tokens", None)
    llm_duration_total = getattr(metrics, "llm_duration_seconds", None)

    run_duration = getattr(metrics, "run_duration_seconds", None)
    success = getattr(metrics, "success", None)

    llm_total_tokens = None
    if llm_prompt_tokens is not None and llm_completion_tokens is not None:
        llm_total_tokens = llm_prompt_tokens + llm_completion_tokens

    try:
        summary_text = metrics.as_cli_summary()
    except Exception as e:
        logger.warning("Failed to build CLI summary from metrics: %s", e)
        summary_text = None

    entry: Dict[str, Any] = {
        "run_id": result.run_id,
        # Use timezone-aware UTC (fixes DeprecationWarning)
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "brand": brand,
        "product": product,
        "platform": platform,
        "file_path": file_path,

        # Volumes
        "keywords_processed": keywords_processed,
        "clusters_created": clusters_created,
        "clusters_used": clusters_used,
        "topics_generated_raw": topics_generated_raw,
        "topics_after_dedup": topics_after_dedup,
        "existing_topics": existing_topics,
        "duplicates_dropped": duplicates_dropped,

        # LLM / content index
        "llm_requests": llm_requests,
        "llm_failures": llm_failures,
        "llm_duration_total": llm_duration_total,
        "llm_prompt_tokens": llm_prompt_tokens,
        "llm_completion_tokens": llm_completion_tokens,
        "total_tokens": llm_total_tokens,
        "content_index_calls": content_index_calls,
        "content_index_errs": content_index_errs,
        "content_index_time": content_index_time,
        "run_duration": run_duration,
        "success": success,
        "summary": summary_text,
    }

    db.setdefault("runs", []).append(entry)
    db_path.write_text(json.dumps(db, indent=2), encoding="utf-8")
    logger.info("Appended metrics entry to %s", db_path)
    return db_path

def _print_summary(result: RunResult) -> None:
    """
    Human-readable summary for CLI usage.
    Logging already contains detailed metrics.
    """
    print(f"\nRun ID: {result.run_id}")
    print(f"Brand: {result.brand} | Product: {result.product} | Locale: {result.locale}")
    print(f"Top {len(result.clusters)} clusters (score desc):")
    for c in result.clusters[:5]:
        print(
            f"  - {c.cluster_id} [{c.metrics.intent}] "
            f"score={c.metrics.score:.3f} brand_fit={c.metrics.brand_fit:.2f} "
            f"label='{c.label}' (n={len(c.members)})"
        )

    print("\nTopic ideas:")
    for t in result.topics[:10]:
        print(f"  - {t.title}  (cluster={t.cluster_id})")

def _setup_logging() -> None:
    """
    Basic logging configuration for CLI usage.

    Library users can ignore this and configure logging themselves.
    """
    level = logging.DEBUG if settings.DEBUG else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    )
    logger.debug("Logging initialized with level=%s", logging.getLevelName(level))

def _resolve_metric_context(brand: str) -> Tuple[str, str]:
    """
    Strict resolver: BOTH website and section must come from BRAND_METRICS.
    No guessing, no defaults.
    """
    b = _brand_slug(brand)
    try:
        website, section = BRAND_METRICS[b]
    except KeyError as e:
        raise ValueError(
            f"Unknown brand '{brand}'. Add it to BRAND_METRICS in config.py "
            f"with (website, section)."
        ) from e

    if not website or not section:
        raise ValueError(
            f"Invalid BRAND_METRICS mapping for '{brand}': website/section cannot be empty."
        )

    return website, section

def run_sync(
    req: RunRequest,
    platform: Optional[str] = None,
    use_content_index: bool = True,
    records: Optional[List[KeywordRecord]] = None,
) -> tuple[RunResult, RunMetrics]:
    run_id = str(uuid.uuid4())[:8]
    start = time.perf_counter()

    status = "success"
    error_message: Optional[str] = None

    metrics = RunMetrics(
        run_id=run_id,
        brand=req.brand,
        product=req.product,
        locale=req.locale,
        platform=platform,
        file_path=req.file_path or None,
    )
    metrics.add_event("KRA_RUN_STARTED", "Blog Keyword Analyzer run started.")

    website, section = _resolve_metric_context(req.brand)

    # Track stage so we can emit failed stage metrics if something blows up
    current_stage = settings.METRICS_KEYWORD_CLUSTERING_JOB
    stage_start = time.perf_counter()

    try:
        # -----------------------
        # STAGE 1: Keyword Clustering
        # -----------------------
        with timed_step(metrics, "import"):
            if records is None:
                records = import_file(req)
        metrics.keywords_processed = len(records)

        with timed_step(metrics, "preprocess"):
            records = preprocess(records)
        metrics.keywords_after_preprocess = len(records)

        with timed_step(metrics, "cluster"):
            clusters = cluster_records(records, k=req.clustering_k)
        metrics.clusters_created = len(clusters)

        clustered_keywords: set[str] = set()
        for c in clusters:
            for m in c.members:
                clustered_keywords.add(m.keyword)

        metrics.keywords_clustered = len(clustered_keywords)
        metrics.keywords_not_clustered = max(
            0, metrics.keywords_after_preprocess - metrics.keywords_clustered
        )

        with timed_step(metrics, "annotate_intent_brand"):
            clusters = annotate_intent_brand(clusters, req.product)

        with timed_step(metrics, "score"):
            clusters = score_clusters(clusters, req.weights)

        metrics.clusters_used_for_topics = min(len(clusters), req.top_clusters)
        metrics.set_cluster_score_stats([c.metrics.score for c in clusters if c.metrics is not None])

        # Send stage 1 metrics (best-effort)
        run_duration_ms = int((time.perf_counter() - start) * 1000)
        stage_duration_ms = int((time.perf_counter() - stage_start) * 1000)
        topic_clustering_step_id: str = run_id + "kc"
        send_stage_metrics(
            settings=settings,
            run_id=topic_clustering_step_id,
            stage=current_stage,
            stage_status="success",
            req=req,
            platform=platform,
            website=website,
            section=section,
            run_duration_ms=run_duration_ms,
            stage_duration_ms=stage_duration_ms,
            item_name="Keywords",
            items_discovered=metrics.keywords_after_preprocess,
            items_succeeded=metrics.keywords_clustered,
            items_failed=metrics.keywords_not_clustered,
            extra_fields={
                "keywords_processed": metrics.keywords_processed,
                "keywords_after_preprocess": metrics.keywords_after_preprocess,
                "clusters_created": metrics.clusters_created,
                "clusters_used_for_topics": metrics.clusters_used_for_topics,
            },
        )

        # -----------------------
        # STAGE 2: Topic Generation
        # -----------------------
        current_stage = settings.METRICS_TOPIC_GENERATION_JOB
        stage_start = time.perf_counter()

        with timed_step(metrics, "content_index"):
            existing_topics = _load_existing_topics_for_prompt(
                product=req.product,
                platform=platform,
                use_content_index=use_content_index,
            )

        if use_content_index:
            metrics.existing_topics_loaded = len(existing_topics)
            metrics.content_index_requests += 1
        else:
            metrics.existing_topics_loaded = 0
            metrics.add_event(
                "CONTENT_INDEX_SKIPPED",
                "Content index lookup disabled for this run (use_content_index=False).",
            )

        agent = KeywordResearchAgent()
        t0_llm = time.perf_counter()

        topics = agent.generate_topics(
            brand=req.brand,
            product=req.product,
            locale=req.locale,
            clusters=clusters,
            top_n=req.top_clusters,
            platform=platform,
            existing_topics=existing_topics,
            metrics=metrics,
        )
        dt_llm = time.perf_counter() - t0_llm
        metrics.mark_llm_call(duration_seconds=dt_llm, failed=topics is None)

        if topics is None:
            topics = []
        metrics.topics_generated_raw = len(topics)

        topics = _filter_duplicate_topics(topics=topics, existing_topics=existing_topics)
        metrics.topics_after_dedup = len(topics)
        metrics.duplicates_dropped = metrics.topics_generated_raw - metrics.topics_after_dedup

        # Send stage 2 metrics (best-effort)
        run_duration_ms = int((time.perf_counter() - start) * 1000)
        stage_duration_ms = int((time.perf_counter() - stage_start) * 1000)
        topic_generation_step_id = run_id + "tg"
        send_stage_metrics(
            settings=settings,
            run_id=topic_generation_step_id,
            stage=current_stage,
            stage_status="success",
            req=req,
            platform=platform,
            website=website,
            section=section,
            run_duration_ms=run_duration_ms,
            stage_duration_ms=stage_duration_ms,
            item_name="Topics",
            items_discovered=metrics.clusters_used_for_topics,
            items_succeeded=metrics.topics_after_dedup,
            items_failed=metrics.duplicates_dropped,
            extra_fields={
                "existing_topics_loaded": metrics.existing_topics_loaded,
                "topics_generated_raw": metrics.topics_generated_raw,
                "topics_after_dedup": metrics.topics_after_dedup,
                "duplicates_dropped": metrics.duplicates_dropped,
                "llm_call_duration_s": float(dt_llm),
            },
        )

        metrics.finish(success=True)
        metrics.add_event(
            "KRA_RUN_COMPLETED",
            "Run completed successfully.",
            clusters_used=metrics.clusters_used_for_topics,
            topics_final=metrics.topics_after_dedup,
        )

    except Exception as exc:
        # IMPORTANT: flip status so “success” isn’t reported accidentally
        status = "failed"
        error_message = str(exc)

        metrics.finish(success=False, error_message=error_message)
        metrics.add_event(
            "KRA_RUN_FAILED",
            "Run failed with exception.",
            exc_type=type(exc).__name__,
        )

        # Emit failed stage payload (best-effort)
        run_duration_ms = int((time.perf_counter() - start) * 1000)
        stage_duration_ms = int((time.perf_counter() - stage_start) * 1000)

        if current_stage == settings.METRICS_KEYWORD_CLUSTERING_JOB:
            discovered = int(getattr(metrics, "keywords_after_preprocess", 0) or 0)
            succeeded = int(getattr(metrics, "keywords_clustered", 0) or 0)
            failed = int(getattr(metrics, "keywords_not_clustered", 0) or 0)
        else:
            discovered = int(getattr(metrics, "clusters_used_for_topics", 0) or 0)
            succeeded = int(getattr(metrics, "topics_after_dedup", 0) or 0)
            failed = max(1, int(getattr(metrics, "duplicates_dropped", 0) or 0))

        send_stage_metrics(
            settings=settings,
            run_id=run_id,
            stage=current_stage,
            stage_status="failed",
            req=req,
            platform=platform,
            website=website,
            section=section,
            run_duration_ms=run_duration_ms,
            stage_duration_ms=stage_duration_ms,
            items_discovered=discovered,
            items_succeeded=succeeded,
            items_failed=failed,
            extra_fields={
                "error_message": error_message,
                "exc_type": type(exc).__name__,
            },
        )
        raise

    result = RunResult(
        run_id=run_id,
        brand=req.brand,
        product=req.product,
        locale=req.locale,
        clusters=clusters[: req.top_clusters],
        topics=topics,
    )
    return result, metrics

def main() -> None:
    """
    CLI entrypoint.

    If --file is omitted or empty, the importer will look in sensible defaults:
      - {KRA_DATA_DIR}/keywords.xlsx|csv
      - ./src/data/samples/keywords.xlsx|csv
      - /mnt/data/samples/keywords.xlsx|csv

    If --file is provided but does not exist, we EXIT with an error and DO NOT
    silently fall back to any default file.
    """
    _setup_logging()

    parser = argparse.ArgumentParser(
        description="Run Blog Keyword Analyzer agent on a CSV/XLSX file."
    )
    parser.add_argument("--file", dest="file_path", default="", help="Path to CSV/XLSX (optional).")
    parser.add_argument("--brand", default="Aspose")
    parser.add_argument("--product", default="Aspose.Cells")
    parser.add_argument(
        "--platform",
        dest="platform",
        default="",
        help="Optional target platform, e.g. python, java, csharp (used to avoid duplicates).",
    )
    parser.add_argument("--locale", default="en-US")
    parser.add_argument("--k", dest="clustering_k", type=int, default=None, help="Force number of clusters.")
    parser.add_argument("--top", dest="top_clusters", type=int, default=settings.TOP_CLUSTERS)
    parser.add_argument("--max-rows", dest="max_rows", type=int, default=settings.MAX_ROWS)
    # By default we DO use content index; this flag turns it OFF.
    parser.add_argument(
        "--no-content-index",
        dest="use_content_index",
        action="store_false",
        help="Disable search for existing topics via content index service.",
    )
    parser.set_defaults(use_content_index=True)

    # NEW: SerpAPI options
    parser.add_argument(
        "--use-serp-api",
        action="store_true",
        help="Fetch keywords from Google SERP via SerpAPI instead of reading a file.",
    )
    parser.add_argument(
        "--serp-topic",
        dest="serp_topic",
        default="",
        help="Topic/angle to seed the SerpAPI query, e.g. 'convert CSV to Excel'.",
    )

    args = parser.parse_args()

    # Decide ingestion mode: file vs SerpAPI
    if args.use_serp_api:
        # We won't use file import, so no need to resolve a file path
        resolved_input: Optional[Path] = None
    else:
        # Old behavior: require and resolve the file
        if not args.file_path:
            raise SystemExit(
                "Input file is required unless you specify --use-serp-api."
            )

        try:
            resolved_input = _resolve_input_file(args.file_path)
        except FileNotFoundError as e:
            print(f"\n❌ {e}")
            raise SystemExit(1)

    # Build request (defaults come from .env-backed settings)
    req = RunRequest(
        brand=args.brand,
        product=args.product,
        locale=args.locale,
        # If resolved_input is None, we pass empty string -> importer may search defaults
        file_path=str(resolved_input) if resolved_input is not None else "",
        clustering_k=args.clustering_k,
        top_clusters=args.top_clusters,
        max_rows=args.max_rows,
        # weights keep defaults from model unless you want to override here
    )

    # If using SerpAPI, fetch KeywordRecord list here
    records: Optional[List[KeywordRecord]] = None
    if args.use_serp_api:
        from .tools.serp_import import fetch_serp_keywords

        topic = args.serp_topic.strip() or args.product
        if settings.DEBUG:
            print(f"[KRA] Using SerpAPI for topic={topic!r}, product={args.product!r}")

        records = fetch_serp_keywords(
            topic=topic,
            product=args.product,
            locale=args.locale,
            max_keywords=args.max_rows,
        )

        if not records:
            print("⚠️ SerpAPI returned no keywords; exiting.")
            raise SystemExit(1)

    logger.info(
        "CLI invoked with brand=%s product=%s locale=%s platform=%s file_path=%s",
        req.brand,
        req.product,
        req.locale,
        args.platform or None,
        req.file_path,
    )

    # Orchestrate
    result, metrics = run_sync(
        req,
        platform=args.platform or None,
        use_content_index=args.use_content_index,
        records=records,  # <--- THIS prevents import_file(req) in SerpAPI mode
    )

    # Print a brief human summary of clusters/topics (optional)
    _print_summary(result)

    # Save JSON artifact under KRA_OUTPUT_DIR
    out_dir = _resolve_output_dir()
    brand_slug = _brand_slug(result.brand)
    out_path = out_dir / f"kra_result_{brand_slug}_{result.run_id}.json"
    # Uncomment this section if you want to save JSON file
    """
    with open(out_path, "w", encoding="utf-8") as f:
        # pydantic v2
        f.write(result.model_dump_json(indent=2))

    print(f"\nSaved full result to {out_path}")
    """

    # New: derived artifacts
    try:
        platform = args.platform or None
        brand_out_dir = _resolve_brand_output_dir(result.brand)
        print(brand_out_dir)
        # Save the generated topics in MD file
        write_topics_markdown(result, output_dir=brand_out_dir, platform=platform)

        # Insert the metrics in DB file
        # metrics_db_path = _get_metrics_db_path(out_dir)
        # append_metrics_db_entry(
        #     result,
        #     metrics,
        #     output_dir=out_dir,
        #     metrics_db_path=metrics_db_path,
        # )
    except Exception as e:
        logger.warning("Post-processing (topics/metrics) failed: %s", e, exc_info=True)

    # 🔹 NOW print metrics summary right after JSON file line
    print()  # blank line for spacing
    print(metrics.as_cli_summary())
    print()  # trailing newline



if __name__ == "__main__":
    main()
