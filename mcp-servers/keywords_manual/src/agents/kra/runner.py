# mcp-servers/kra/src/agents/kra/runner.py
from __future__ import annotations

import sys
import os
import uuid
import traceback
from pathlib import Path
from typing import Optional
import sys
agent_engine_path = Path(__file__).parent.parent.parent.parent.parent.parent / 'agent_engine'
sys.path.append(str(agent_engine_path))
from config import settings
sys.dont_write_bytecode = True

# --- Make sure local `src/` package root is first on sys.path so
#     imports like `from agents.kra...` resolve to this repo's code,
#     not an installed PyPI package named `agents`.
_this_file = Path(__file__).resolve()
# file layout: .../mcp-servers/kra/src/agents/kra/runner.py
# want repo_root = parents[3]  (i.e. .../mcp-servers/kra)
repo_root = _this_file.parents[3] if len(_this_file.parents) >= 4 else _this_file.parent
# Add repo_root to sys.path (at front)
sys.path.insert(0, str(repo_root))

# Now local imports (should resolve to your package)
from agents.kra.schemas import RunRequest, RunResult
from agents.kra.agent import KeywordResearchAgent
from agents.kra.tools.file_import import import_file
from agents.kra.tools.preprocess import preprocess
from agents.kra.tools.cluster import cluster_records
from agents.kra.tools.intent_brand import annotate_intent_brand
from agents.kra.tools.scoring import score_clusters


from fastmcp import FastMCP

mcp = FastMCP("kra-server")


def _project_root(start: Optional[Path] = None) -> Path:
    p = (start or Path.cwd()).resolve()
    for _ in range(10):
        if (p / "pyproject.toml").exists() or (p / ".git").exists():
            return p
        if p.parent == p:
            break
        p = p.parent
    return Path.cwd().resolve()


def _resolve_output_dir() -> Path:
    root = _project_root()
    out_dir = Path(settings.KRA_OUTPUT_DIR)
    if not out_dir.is_absolute():
        out_dir = (root / out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir


def run_sync(req: RunRequest) -> RunResult:
    """
    Same deterministic orchestration as before (synchronous).
    """
    run_id = str(uuid.uuid4())[:8]

    # 1) ingest
    records = import_file(req)

    # 2) preprocess
    records = preprocess(records)

    # 3) cluster
    clusters = cluster_records(records, k=req.clustering_k)

    # 4) annotate intent + brand-fit
    clusters = annotate_intent_brand(clusters, req.product)

    # 5) score & sort
    clusters = score_clusters(clusters, req.weights)

    # 6) generate topics via LLM
    agent = KeywordResearchAgent()
    topics = agent.generate_topics(
        brand=req.brand,
        product=req.product,
        locale=req.locale,
        clusters=clusters,
        top_n=req.top_clusters,
    )

    return RunResult(
        run_id=run_id,
        brand=req.brand,
        product=req.product,
        locale=req.locale,
        clusters=clusters[: req.top_clusters],
        topics=topics,
    )


def _summarize_result(result: RunResult) -> dict:
    # Build a small summary that is safe to return over MCP
    summary_clusters = []
    for c in result.clusters:
        summary_clusters.append({
            "cluster_id": c.cluster_id,
            "label": c.label,
            "score": getattr(c.metrics, "score", None),
            "intent": getattr(c.metrics, "intent", None),
            "n_members": len(c.members),
        })

    summary_topics = []
    for t in result.topics:
        # if TopicIdea is a pydantic model, use dict; otherwise best-effort attributes
        try:
            summary_topics.append(t.model_dump())
        except Exception:
            summary_topics.append({
                "title": getattr(t, "title", None),
                "primary_keyword": getattr(t, "primary_keyword", None),
                "cluster_id": getattr(t, "cluster_id", None),
            })

    return {
        "run_id": result.run_id,
        "brand": result.brand,
        "product": result.product,
        "locale": result.locale,
        "clusters": summary_clusters,
        "topics": summary_topics,
    }


@mcp.tool()
def run_kra(
    brand: str = "Aspose",
    product: str = "Aspose.Cells",
    locale: str = "en-US",
    top: int = settings.TOP_CLUSTERS,
    file_path: str = "",
    clustering_k: Optional[int] = None,
    max_rows: Optional[int] = None,
    weights: Optional[dict] = None,
) -> dict:
    """
    MCP tool entrypoint.

    Parameters are passed as JSON by the caller, e.g.:
      {"brand":"Aspose","product":"Aspose.PSD","locale":"en-US","top":4}

    Returns a JSON-serializable dict with status, run_id, summary, and output_path.
    """
    try:
        req = RunRequest(
            brand=brand,
            product=product,
            locale=locale,
            file_path=file_path or "",
            clustering_k=clustering_k,
            top_clusters=top,
            max_rows=max_rows or settings.MAX_ROWS
        )

        result = run_sync(req)

        # write full artifact
        out_dir = _resolve_output_dir()
        out_path = out_dir / f"kra_result_{result.run_id}.json"
        with open(out_path, "w", encoding="utf-8") as f:
            # pydantic v2
            try:
                f.write(result.model_dump_json(indent=2))
            except Exception:
                # fallback: dump dict
                import json
                f.write(json.dumps(result.model_dump(), indent=2))

        summary = _summarize_result(result)

        return {
            "status": "success",
            "run_id": result.run_id,
            "summary": summary,
            "output_path": str(out_path),
        }

    except Exception as e:
        tb = traceback.format_exc()
        # Always return error details in a safe JSON form for debugging the caller
        return {
            "status": "error",
            "error": str(e),
            "traceback": tb,
        }


if __name__ == "__main__":
    # When run directly for local debugging, print tip and start MCP server.
    print("Starting KRA MCP server (FastMCP)...", file=sys.stderr, flush=True)
    mcp.run()
