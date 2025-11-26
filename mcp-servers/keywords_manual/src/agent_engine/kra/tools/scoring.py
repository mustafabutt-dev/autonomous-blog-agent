from __future__ import annotations
from typing import List, Dict, Optional
from ..schemas import Cluster
import numpy as np

def _nz(vals):
    return [float(v) for v in vals if v is not None]

def _nrm(v: float, lo: float, hi: float) -> float:
    if hi <= lo:
        return 0.0
    return (v - lo) / (hi - lo)

def score_clusters(clusters: List[Cluster], weights: Dict[str, float]) -> List[Cluster]:
    vols, kds, cpcs = [], [], []
    for cl in clusters:
        vols += _nz([m.volume for m in cl.members])
        kds  += _nz([m.kd for m in cl.members])
        cpcs += _nz([m.cpc for m in cl.members])

    v_lo, v_hi = (min(vols), max(vols)) if vols else (0.0, 1.0)
    kd_lo, kd_hi = (min(kds), max(kds)) if kds else (0.0, 100.0)
    cpc_lo, cpc_hi = (min(cpcs), max(cpcs)) if cpcs else (0.0, 5.0)

    intent_w = {"informational":0.25, "commercial":0.6, "transactional":1.0, "navigational":0.2}

    for cl in clusters:
        vols_c = _nz([m.volume for m in cl.members])
        kds_c  = _nz([m.kd for m in cl.members])
        cpcs_c = _nz([m.cpc for m in cl.members])
        comps = [m.competition for m in cl.members if m.competition is not None]

        avg_v = float(sum(vols_c)/len(vols_c)) if vols_c else 0.0
        avg_kd = float(sum(kds_c)/len(kds_c)) if kds_c else 0.0
        avg_cpc = float(sum(cpcs_c)/len(cpcs_c)) if cpcs_c else 0.0
        avg_comp = float(np.mean(comps)) if comps else None

        v_s = _nrm(avg_v, v_lo, v_hi)
        kd_s = _nrm(avg_kd, kd_lo, kd_hi)
        cpc_s = _nrm(avg_cpc, cpc_lo, cpc_hi)
        brand_s = cl.metrics.brand_fit
        intent_s = intent_w.get(cl.metrics.intent, 0.25)


        score = (
            weights["volume"] * v_s
            - weights["kd"] * kd_s
            + weights["cpc"] * cpc_s
            + weights["brand"] * brand_s
            + weights["intent"] * intent_s
        )
        cl.metrics.avg_volume = round(avg_v, 3)
        cl.metrics.avg_kd = round(avg_kd, 3)
        cl.metrics.avg_cpc = round(avg_cpc, 3)
        cl.metrics.score = round(float(score), 6)
        cl.metrics.avg_competition = avg_comp

    clusters.sort(key=lambda c: c.metrics.score, reverse=True)
    return clusters
