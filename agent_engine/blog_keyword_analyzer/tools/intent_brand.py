from __future__ import annotations
import re
from typing import List
from ..schemas import Cluster

def annotate_intent_brand(clusters: List[Cluster], product: str) -> List[Cluster]:
    info_pat = re.compile(r"\b(how to|guide|tutorial|what is|examples?)\b")
    comm_pat = re.compile(r"\b(best|top|tools?|software|alternatives?|compare|vs\.? )\b")
    trans_pat = re.compile(r"\b(buy|price|pricing|download|license|trial)\b")
    nav_pat  = re.compile(r"\b(aspose|docs|reference|api|login|account)\b")
    p_ns = product.strip().lower()

    for cl in clusters:
        corpus = " ".join([m.keyword for m in cl.members])
        intent = "informational"
        if trans_pat.search(corpus):
            intent = "transactional"
        elif comm_pat.search(corpus):
            intent = "commercial"
        elif nav_pat.search(corpus):
            intent = "navigational"
        elif info_pat.search(corpus):
            intent = "informational"

        hits = sum(1 for m in cl.members if p_ns in m.keyword)
        brand_fit = hits / max(1, len(cl.members))

        cl.metrics.intent = intent  # type: ignore
        cl.metrics.brand_fit = round(float(brand_fit), 3)
    return clusters
