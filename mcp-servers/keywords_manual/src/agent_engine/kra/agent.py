from __future__ import annotations
from pathlib import Path
import json
import re, sys
from typing import List

from openai import OpenAI
agent_engine_path = Path(__file__).parent.parent.parent.parent.parent.parent / 'agent_engine'
sys.path.append(str(agent_engine_path))
from config import settings
from .schemas import Cluster, TopicIdea


class KeywordResearchAgent:
    """Agent responsible for turning scored clusters into topic ideas via LLM."""

    def __init__(self, model: str | None = None) -> None:
        # Prefer explicit model, then custom model, then default
        self.model = model or settings.ASPOSE_LLM_MODEL or settings.DEFAULT_MODEL

        # Decide which backend to use
        if (
            settings.ASPOSE_LLM_MODEL
            and settings.ASPOSE_LLM_BASE_URL
            and settings.ASPOSE_LLM_API_KEY
        ):
            # Your self-hosted LLM (OpenAI-compatible)
            self.client = OpenAI(
                base_url=settings.ASPOSE_LLM_BASE_URL,
                api_key=settings.ASPOSE_LLM_API_KEY,
            )
            # Many custom servers don't fully support response_format yet
            self._use_response_format = False
        else:
            # Standard OpenAI
            self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
            self._use_response_format = True

    @staticmethod
    def _extract_json_block(text: str) -> str | None:
        """
        Try to rescue a JSON object from a response that may contain
        extra text or markdown fences.
        """
        # Remove common markdown fences
        text = text.strip()
        if text.startswith("```"):
            # Strip leading ```... and trailing ```
            text = re.sub(r"^```[a-zA-Z0-9]*\s*", "", text)
            text = text.rstrip("`").strip()

        # Greedy match the first {...} block
        match = re.search(r"\{[\s\S]*\}", text)
        if match:
            return match.group(0)
        return None

    def generate_topics(
        self,
        brand: str,
        product: str,
        locale: str,
        clusters: List[Cluster],
        top_n: int = 10,
    ) -> List[TopicIdea]:
        # Take top N clusters
        chosen = clusters[:top_n]

        # Compact payload for the LLM
        payload = {
            "brand": brand,
            "product": product,
            "locale": locale,
            "clusters": [
                {
                    "cluster_id": c.cluster_id,
                    "label": c.label,
                    "intent": c.metrics.intent,
                    "brand_fit": c.metrics.brand_fit,
                    "score": c.metrics.score,
                    "keywords": [m.keyword for m in c.members[:12]],
                }
                for c in chosen
            ],
        }

        # System prompt (your existing long description is fine)
        system = (
            "You are an SEO & Content Strategy assistant specializing in analyzing "
            "Google Keyword Planner (GKP) data and turning it into blog post topic ideas.\n"
            "\n"
            "You will receive JSON with keys: 'brand', 'product', 'locale', and 'clusters'. "
            "'clusters' is a list; each cluster has 'cluster_id', 'label', 'intent', "
            "'brand_fit', 'score', and 'keywords' (list of phrases).\n"
            "\n"
            "Your job is to propose high-impact blog post topics based on these clusters.\n"
            "You MUST reply with STRICT JSON with a single top-level key 'topics'.\n"
            "'topics' must be a list of objects, each with ALL of:\n"
            "  - 'cluster_id'\n"
            "  - 'title'\n"
            "  - 'angle'\n"
            "  - 'outline' (list of 3–7 strings)\n"
            "  - 'target_persona'\n"
            "  - 'primary_keyword'\n"
            "  - 'supporting_keywords' (list of 3–8 strings)\n"
            "  - 'internal_links' (list of 0–5 strings)\n"
            "\n"
            "Your entire response MUST be valid JSON parsable as:\n"
            "{ \"topics\": [ { ... }, { ... } ] }\n"
            "Do NOT include any explanations or text outside the JSON."
        )

        if settings.DEBUG:
            print("\n[KeywordResearchAgent] Payload sent to LLM:")
            print(json.dumps(payload, indent=2))

        # Build request kwargs
        request_kwargs = {
            "model": self.model,
            "temperature": 0.2,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": json.dumps(payload)},
            ],
        }
        if self._use_response_format:
            request_kwargs["response_format"] = {"type": "json_object"}

        # Call LLM
        resp = self.client.chat.completions.create(**request_kwargs)
        txt = resp.choices[0].message.content or ""

        if settings.DEBUG:
            print("\n[KeywordResearchAgent] Raw LLM output (truncated to 1200 chars):")
            print(txt[:1200])

        # Try to parse JSON strictly
        data_obj = None
        try:
            data_obj = json.loads(txt)
        except json.JSONDecodeError:
            # Try to rescue JSON from messy text
            json_block = self._extract_json_block(txt)
            if json_block is not None:
                if settings.DEBUG:
                    print("\n[KeywordResearchAgent] Extracted JSON block:")
                    print(json_block[:1200])
                try:
                    data_obj = json.loads(json_block)
                except json.JSONDecodeError:
                    if settings.DEBUG:
                        print(
                            "[KeywordResearchAgent] Failed to parse extracted JSON block."
                        )
                    data_obj = None
            else:
                if settings.DEBUG:
                    print(
                        "[KeywordResearchAgent] No JSON object found in LLM output; returning no topics."
                    )
                data_obj = None

        if not isinstance(data_obj, dict):
            return []

        topics_raw = data_obj.get("topics", [])
        if not isinstance(topics_raw, list):
            if settings.DEBUG:
                print(
                    "[KeywordResearchAgent] 'topics' key missing or not a list in JSON; returning no topics."
                )
            return []

        out: List[TopicIdea] = []
        for t in topics_raw:
            if not isinstance(t, dict):
                continue
            try:
                out.append(TopicIdea(**t))
            except Exception as e:
                if settings.DEBUG:
                    print(f"[KeywordResearchAgent] Failed to parse TopicIdea: {e}")
                continue

        if settings.DEBUG:
            print(f"[KeywordResearchAgent] Parsed {len(out)} topics")

        return out
