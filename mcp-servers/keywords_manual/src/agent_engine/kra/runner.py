# kra_server.py
from fastmcp import FastMCP
from pathlib import Path
import json
import uuid
import os
import sys
agent_engine_path = Path(__file__).parent.parent.parent.parent.parent.parent / 'agent_engine'
sys.path.append(str(agent_engine_path))
from config import settings

from .schemas import RunRequest, RunResult
from .agent import KeywordResearchAgent
from .tools.file_import import import_file
from .tools.preprocess import preprocess
from .tools.cluster import cluster_records
from .tools.intent_brand import annotate_intent_brand
from .tools.scoring import score_clusters
# from .config import settings


# ------------------------------------------------
# Helpers (same logic — but removed CLI parts)
# ------------------------------------------------

def _project_root(start=None) -> Path:
    p = (start or Path.cwd()).resolve()
    for _ in range(10):
        if (p / "pyproject.toml").exists() or (p / ".git").exists():
            return p
        if p.parent == p:
            break
        p = p.parent
    return Path.cwd().resolve()


def _resolve_input_file(path_str):
    if not path_str:
        return None
    root = _project_root()
    p = Path(path_str)
    if not p.is_absolute():
        p = (root / p).resolve()
    if not p.exists():
        raise FileNotFoundError(f"Input file not found: {p}")
    return p


def _resolve_output_dir() -> Path:
    root = _project_root()
    out_dir = Path(settings.KRA_OUTPUT_DIR)
    if not out_dir.is_absolute():
        out_dir = (root / out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir


# ------------------------------------------------
# Core sync logic
# ------------------------------------------------
def run_sync(req: RunRequest) -> RunResult:
    run_id = str(uuid.uuid4())[:8]

    # 1) ingest
    records = import_file(req)

    # 2) preprocess
    records = preprocess(records)

    # 3) cluster
    clusters = cluster_records(records, k=req.clustering_k)

    # 4) annotate
    clusters = annotate_intent_brand(clusters, req.product)

    # 5) score
    clusters = score_clusters(clusters, req.weights)

    # 6) generate topics
    agent = KeywordResearchAgent()
    topics = agent.generate_topics(
        brand=req.brand,
        product=req.product,
        locale=req.locale,
        clusters=clusters,
        top_n=req.top_clusters,
    ) or []

    return RunResult(
        run_id=run_id,
        brand=req.brand,
        product=req.product,
        locale=req.locale,
        clusters=clusters[:req.top_clusters],
        topics=topics,
    )


# ------------------------------------------------
# MCP Server
# ------------------------------------------------
mcp = FastMCP("kra_keyword_agent")

print("🔧 KRA MCP server initialized. Tools:")
@mcp.tool()
async def run_kra(
    brand: str,
    product: str,
    locale: str = "en-US",
    file_path: str = "",
    clustering_k: int | None = None,
    top_clusters: int = settings.TOP_CLUSTERS,
    max_rows: int = settings.MAX_ROWS,
):
    """
    MCP tool that runs the Keyword Research Agent (KRA)
    and returns scored clusters + generated topics.
    """
    print(f"bidd - {brand}")
    # Resolve file if given
    try:
        resolved_input = _resolve_input_file(file_path) if file_path else ""
    except FileNotFoundError as e:
        return {"error": str(e)}

    # Build request
    req = RunRequest(
        brand=brand,
        product=product,
        locale=locale,
        file_path=str(resolved_input) if resolved_input else "",
        clustering_k=clustering_k,
        top_clusters=top_clusters,
        max_rows=max_rows,
    )

    # Run
    result = run_sync(req)

    # Save artifacts
    out_dir = _resolve_output_dir()
    out_path = out_dir / f"kra_result_{result.run_id}.json"
    out_path.write_text(result.model_dump_json(indent=2), encoding="utf-8")

    return {
        "run_id": result.run_id,
        "brand": result.brand,
        "product": result.product,
        "locale": result.locale,
        "clusters": [c.model_dump() for c in result.clusters],
        "topics": [t.model_dump() for t in result.topics],
        "artifact": str(out_path),
    }


if __name__ == "__main__":
    mcp.run()
