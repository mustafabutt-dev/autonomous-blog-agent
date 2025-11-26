# src/agents/kra/tools/file_import.py
from __future__ import annotations
import os, re, sys
from pathlib import Path
from typing import List, Dict, Optional
import pandas as pd
from ..schemas import RunRequest, KeywordRecord
agent_engine_path = Path(__file__).parent.parent.parent.parent.parent.parent.parent / 'agent_engine'
sys.path.append(str(agent_engine_path))
from config import settings
# --- add near imports at top ---
from pathlib import Path

NUM_RX = re.compile(r"[-+]?\d[\d,\.]*")

def _clean_number(val) -> Optional[float]:
    """
    Convert strings like '$2.10', '1,200', '1.200,50' to float.
    Returns None if not parseable.
    """
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    if isinstance(val, (int, float)):
        return float(val)
    s = str(val).strip()
    if not s or s.lower() in {"na", "n/a", "-", "none"}:
        return None
    # pick the first numeric-looking token
    m = NUM_RX.search(s)
    if not m:
        return None
    token = m.group(0)
    # handle european decimals "1.234,56" -> "1234.56"
    if "," in token and "." in token:
        if token.rfind(",") > token.rfind("."):
            token = token.replace(".", "").replace(",", ".")
        else:
            token = token.replace(",", "")
    else:
        token = token.replace(",", "")
    try:
        return float(token)
    except ValueError:
        return None

# --- add these helpers above import_file() ---
def _read_table_resilient(path: str) -> pd.DataFrame:
    """
    Robustly read keyword table from path that might be:
    - XLSX (zip magic "PK\x03\x04")
    - XLS (OLE CF "D0 CF 11 E0")
    - CSV with various encodings (utf-8, utf-16, etc.)
    - CSV saved with wrong extension (.xlsx renamed to .csv)
    """
    p = Path(path)
    # Read a few bytes to sniff magic / BOM
    with open(p, "rb") as f:
        head = f.read(8)

    # Magic numbers
    is_xlsx = head.startswith(b"PK\x03\x04")
    is_xls  = head.startswith(b"\xD0\xCF\x11\xE0")
    bom_utf16_le = head.startswith(b"\xff\xfe")
    bom_utf16_be = head.startswith(b"\xfe\xff")

    # If magic says Excel, use read_excel regardless of extension
    if is_xlsx or is_xls or p.suffix.lower() in {".xlsx", ".xls"}:
        return pd.read_excel(p)  # engine auto-detected

    # Otherwise treat as text/CSV; try encodings
    # sep=None + engine='python' lets pandas sniff delimiter (, ; \t)
    encodings = ["utf-8", "utf-8-sig", "utf-16", "utf-16le", "utf-16be", "latin1"]
    # Prioritize utf-16 if BOM says so
    if bom_utf16_le:
        encodings = ["utf-16", "utf-16le", "utf-16be", "utf-8", "utf-8-sig", "latin1"]
    if bom_utf16_be:
        encodings = ["utf-16", "utf-16be", "utf-16le", "utf-8", "utf-8-sig", "latin1"]

    last_err = None
    for enc in encodings:
        try:
            # return pd.read_csv(p, encoding=enc, sep=None, engine="python")
            # GKP CSV: first 2 lines are meta, real header starts at line 3
            return pd.read_csv(
                p,
                skiprows=2,  # skip "Keyword Stats..." and date range line
                encoding=enc,
                sep=None,
                engine="python"
            )
        except Exception as e:
            last_err = e
            continue
    # If we reach here, all attempts failed
    raise ValueError(f"Could not read file as CSV with common encodings; last error: {last_err}")

# --- inside import_file(), replace the current load block with this ---
    # --- load (robust) ---
    df = _read_table_resilient(path)
    df.columns = [c.strip().lower() for c in df.columns]

COMP_MAP = {
    "low": 0.2,
    "medium": 0.6,
    "med": 0.6,
    "high": 0.9,
}

def _parse_competition(value) -> tuple[Optional[float], Optional[str]]:
    """
    Accepts: 'low'|'medium'|'high' (case-insensitive), or numeric (0..1 or %).
    Returns (index_float, label_str).
    """
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None, None
    s = str(value).strip().lower()

    # categorical
    if s in COMP_MAP:
        return float(COMP_MAP[s]), s

    # numeric string (e.g., '0.62' or '62%')
    num = _clean_number(value)
    if num is None:
        return None, None

    # If it looks like a percent (e.g., 62) bring to 0..1 range conservatively only when > 1.5
    if num > 1.5:
        return float(num), None           # keep as 62 (you can divide by 100 if you prefer)
    return float(num), None               # already 0..1


def import_file(req: RunRequest) -> List[KeywordRecord]:
    # --- resolve path (use your existing robust search or pass absolute) ---
    path = req.file_path
    if not path or not os.path.exists(path):
        for p in (
            "./src/data/keywords.xlsx", "./src/data/keywords.csv",
            f"{settings.KRA_DATA_DIR.rstrip('/')}/keywords.xlsx",
            f"{settings.KRA_DATA_DIR.rstrip('/')}/keywords.csv",
            "/mnt/data/keywords.xlsx", "/mnt/data/keywords.csv",
        ):
            if os.path.exists(p):
                path = p
                break
    if not path or not os.path.exists(path):
        raise FileNotFoundError(f"Input file not found: {req.file_path}")

    # --- load ---
    # df = pd.read_excel(path) if path.lower().endswith(".xlsx") else pd.read_csv(path)
    # df.columns = [c.strip().lower() for c in df.columns]

    df = _read_table_resilient(path)
    df.columns = [c.strip().lower() for c in df.columns]

    # --- header mapping: broaden aliases ---
    aliases = {
        "keyword": {"keyword", "query", "search term", "term"},
        "volume": {
            "volume", "search_volume", "avg_monthly_searches", "search volume",
            "search volume (avg)", "avg. monthly searches"
        },
        "cpc": {"cpc", "avg_cpc", "cost_per_click", "cpc (usd)", "avg. cpc"},
        "kd": {
            "kd", "difficulty", "keyword_difficulty", "keyword difficulty",
            "difficulty (%)", "kd (%)"
        },
        "clicks": {"clicks", "est_clicks", "estimated clicks"},
        "url": {"url", "target_url", "landing_page", "top url"},
        "competition": {
            "competition", "comp", "ad_competition", "competition_index",
            "competition (gkp)", "comp. index", "competitive density"
        },
        "competition_text": {
            "competition level", "comp level", "ad competition", "comp_text",
            "competition_text"
        },
    }

    def find_col(cands: set[str]) -> Optional[str]:
        for name in df.columns:
            if name in cands:
                return name
        return None

    col_map: Dict[str, Optional[str]] = {
        k: find_col(v) for k, v in aliases.items()
    }
    # allow either numeric competition OR text competition source
    comp_col = col_map.get("competition")
    comp_txt_col = col_map.get("competition_text")

    if not col_map["keyword"]:
        raise ValueError(
            "No 'keyword' column found. "
            f"Seen headers: {', '.join(df.columns[:20])}"
        )

    df = df.iloc[: req.max_rows].copy()

    out: List[KeywordRecord] = []
    for _, row in df.iterrows():
        kw = str(row[col_map["keyword"]]).strip().lower()
        if not kw:
            continue

        volume = _clean_number(row[col_map["volume"]]) if col_map["volume"] else None
        cpc    = _clean_number(row[col_map["cpc"]]) if col_map["cpc"] else None
        kd     = _clean_number(row[col_map["kd"]]) if col_map["kd"] else None
        clicks = _clean_number(row[col_map["clicks"]]) if col_map["clicks"] else None
        url    = str(row[col_map["url"]]).strip() if col_map["url"] and pd.notna(row[col_map["url"]]) else None
        comp_val = None
        comp_label = None
        if comp_txt_col:
            comp_val, comp_label = _parse_competition(row[comp_txt_col])
        elif comp_col:
            comp_val, comp_label = _parse_competition(row[comp_col])

        out.append(KeywordRecord(
            keyword=kw,
            source="upload",
            locale=req.locale,
            volume=int(volume) if volume is not None else None,
            cpc=float(cpc) if cpc is not None else None,
            kd=float(kd) if kd is not None else None,
            clicks=float(clicks) if clicks is not None else None,
            url=url or None,
            competition=float(comp_val) if comp_val is not None else None,
            competition_label=(comp_label if comp_label else None),
        ))

    # Dedup by keyword
    seen, dedup = set(), []
    for r in out:
        if r.keyword not in seen:
            seen.add(r.keyword)
            dedup.append(r)
    return dedup
