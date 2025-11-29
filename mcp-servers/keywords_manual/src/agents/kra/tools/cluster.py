from __future__ import annotations
from typing import List, Dict, Optional
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import MiniBatchKMeans
from ..schemas import KeywordRecord, Cluster, ClusterMetrics

def _auto_k(n_samples: int) -> int:
    if n_samples < 500: return 10
    if n_samples < 2000: return 15
    return 20

def _to_1d(a) -> np.ndarray:
    """Convert numpy.matrix / sparse row to a flat ndarray safely."""
    # numpy.matrix has .A1 (flat). For anything else, np.asarray + ravel
    return a.A1 if hasattr(a, "A1") else np.asarray(a).ravel()

def cluster_records(records: List[KeywordRecord], k: Optional[int] = None) -> List[Cluster]:
    texts = [r.keyword for r in records]
    vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=2)
    X = vectorizer.fit_transform(texts)

    k_final = k or _auto_k(X.shape[0])
    kmeans = MiniBatchKMeans(n_clusters=k_final, random_state=42, n_init="auto", batch_size=2048)
    labels = kmeans.fit_predict(X)

    buckets: Dict[int, List[int]] = {}
    for i, lab in enumerate(labels):
        buckets.setdefault(lab, []).append(i)

    clusters: List[Cluster] = []
    for lab, idxs in buckets.items():
        members = [records[i] for i in idxs]

        # Use sum (sparse-friendly), then convert to 1D ndarray safely
        sub = X[idxs].sum(axis=0)          # still a matrix
        vec = _to_1d(sub)                  # now a flat ndarray
        if vec.size == 0 or np.all(vec == 0):
            label_term = members[0].keyword  # fallback
        else:
            top_idx = int(vec.argmax())
            label_term = vectorizer.get_feature_names_out()[top_idx]

        clusters.append(Cluster(
            cluster_id=f"c{lab}",
            label=label_term,
            members=members,
            metrics=ClusterMetrics(),
        ))
    return clusters
