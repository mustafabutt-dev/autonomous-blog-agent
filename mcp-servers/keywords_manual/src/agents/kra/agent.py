from __future__ import annotations
import json, uuid
from pathlib import Path
import sys, os
from typing import List
from openai import OpenAI

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
ASPOSE_LLM_API_KEY = os.getenv('ASPOSE_LLM_API_KEY')
ASPOSE_LLM_BASE_URL = os.getenv('ASPOSE_LLM_BASE_URL')
ASPOSE_LLM_MODEL = os.getenv('ASPOSE_LLM_MODEL')
print(f"testing -- OPENAI_API_KEY: {OPENAI_API_KEY[:10] if OPENAI_API_KEY else 'NOT SET'}", flush=True, file=sys.stderr)

current_file = Path(__file__).resolve()
# Go up to the blog-agent-backend root
repo_root = current_file.parent.parent.parent.parent.parent.parent
agent_engine_path = repo_root / 'agent_engine'

# Add to path
sys.path.insert(0, str(agent_engine_path))
from config import settings
# print(f"testing -- {settings} - {agent_engine_path}", flush=True, file=sys.stderr)
from .schemas import Cluster, TopicIdea

class KeywordResearchAgent:
    """Minimal agent: only responsible for topic generation via LLM."""
    def __init__(self, model: str | None = None):
        self.model = model or settings.DEFAULT_MODEL
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)

    def generate_topics(self, brand: str, product: str, locale: str,
                        clusters: List[Cluster], top_n: int = 10) -> List[TopicIdea]:
        chosen = clusters[:top_n]
        payload = {
            "brand": brand, "product": product, "locale": locale,
            "clusters": [
                {
                    "cluster_id": c.cluster_id,
                    "label": c.label,
                    "intent": c.metrics.intent,
                    "brand_fit": c.metrics.brand_fit,
                    "score": c.metrics.score,
                    "keywords": [m.keyword for m in c.members[:12]],
                } for c in chosen
            ],
        }

        system = (
            "You are a Blog Keyword Analyzer Agent. "
            "Return STRICT JSON with key 'topics' as a list of topic ideas. "
            "Each item must include: cluster_id, title, angle, outline (3-7 bullets), "
            "target_persona, primary_keyword, supporting_keywords (3-8), internal_links."
        )

        resp = self.client.chat.completions.create(
            model=self.model,
            temperature=0.2,
            messages=[
                {"role":"system","content": system},
                {"role":"user","content": json.dumps(payload)},
            ],
            response_format={"type":"json_object"},
        )
        txt = resp.choices[0].message.content
        data = json.loads(txt)

        out: List[TopicIdea] = []
        for t in data.get("topics", []):
            try:
                out.append(TopicIdea(**t))
            except Exception:
                continue
        return out
