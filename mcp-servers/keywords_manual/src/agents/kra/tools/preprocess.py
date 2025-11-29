from __future__ import annotations
from typing import List, Optional
from ..schemas import KeywordRecord

def preprocess(records: List[KeywordRecord]) -> List[KeywordRecord]:
    cleaned: List[KeywordRecord] = []
    for r in records:
        if not r.keyword:
            continue
        kd = r.kd
        if kd is not None:
            if kd <= 1.0:
                kd = kd * 100.0
            kd = max(0.0, min(100.0, kd))
        cleaned.append(KeywordRecord(**{**r.dict(), "kd": kd}))
    return cleaned
