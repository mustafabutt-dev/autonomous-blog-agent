# src/apps/api/main.py
from __future__ import annotations

import json
import uuid
import traceback
from pathlib import Path
from typing import Optional
from typing import Dict, List

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import ValidationError

from agent_engine.kra.config import settings
from agent_engine.kra.schemas import RunRequest
from agent_engine.kra.runner import run_sync
from fastapi.responses import FileResponse

app = FastAPI(title="Blog Keyword Analyzer UI/API", version="0.1.3")

BASE_DIR = Path(__file__).resolve().parents[1]  # points to apps/
FAVICON_PATH = BASE_DIR / "images" / "favicon.ico"

@app.get("/favicon.ico")
async def favicon() -> FileResponse:
    return FileResponse(FAVICON_PATH)

# CORS for local dev (tighten in prod)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- helper data for brands/products ----------
def load_brands() -> Dict[str, List[str]]:
    # Resolve brands.json relative to *this file* (main.py)
    path = Path(__file__).resolve().parent.parent / "brands.json"
    # If your brands.json is beside main.py, use:
    # path = Path(__file__).resolve().parent / "brands.json"

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        print("Loaded brands from:", path)

        if isinstance(raw, dict):
            cleaned: Dict[str, List[str]] = {}
            for k, v in raw.items():
                if isinstance(v, list):
                    cleaned[str(k)] = [str(x) for x in v]
            if cleaned:
                return cleaned

    except Exception as exc:
        # Optional: log, don't crash import
        print(f"⚠️ Failed to load {path}: {exc}")

    # Fallback: return empty dict or your hard-coded mapping
    return {}

BRANDS_DEFAULT: Dict[str, List[str]] = load_brands()


# ---------- helpers ----------

def _project_root(start: Optional[Path] = None) -> Path:
    p = (start or Path.cwd()).resolve()
    for _ in range(10):
        if (p / "pyproject.toml").exists() or (p / ".git").exists():
            return p
        if p.parent == p:
            break
        p = p.parent
    return Path.cwd().resolve()


def _ensure_dir(p: Path) -> Path:
    p.mkdir(parents=True, exist_ok=True)
    return p


def _outputs_dir() -> Path:
    root = _project_root()
    out_root = Path(settings.KRA_OUTPUT_DIR)
    if not out_root.is_absolute():
        out_root = (root / out_root).resolve()
    _ensure_dir(out_root)
    return out_root


def _brands_path() -> Optional[Path]:
    """
    Try to locate brands.json in a few sensible places.
    """
    root = _project_root()
    candidates = [
        root / "src" / "data" / "brands.json",
        root / "brands.json",
        Path(__file__).resolve().parent / "brands.json",
    ]
    for p in candidates:
        if p.exists():
            return p
    return None


def _load_brands() -> dict[str, list[str]]:
    """
    Load brands from brands.json, falling back to BRANDS_DEFAULT.
    """
    p = _brands_path()
    if p:
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                norm: dict[str, list[str]] = {}
                for k, v in data.items():
                    if isinstance(v, list):
                        norm[str(k)] = [str(x) for x in v]
                if norm:
                    return norm
        except Exception:
            # Fall back to default if anything goes wrong
            pass
    return BRANDS_DEFAULT


# ---------- UI ----------

@app.get("/", response_class=HTMLResponse)
def index() -> str:
    """Single-page UI (light/dark) + Previous runs loader + JSON normalizer."""
    return """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>Blog Keyword Analyzer</title>
  <link rel="icon" type="image/x-icon" href="/favicon.ico" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <style>
    :root {
      --bg: #f7f9fc; --text: #0a1628; --muted: #5e6b85; --card: #ffffff;
      --border: #e6eaf1; --shadow: 0 10px 25px rgba(16, 24, 40, 0.08);
      --info: #2563eb; --info-soft: #eaf1ff;
      --comm: #b45309; --comm-soft: #fff6e6;
      --trans: #059669; --trans-soft: #e8fff4;
      --nav: #7c3aed; --nav-soft: #f3e8ff;
      --accent: #0ea5e9; --accent-soft: #e6f6ff;
    }
    @media (prefers-color-scheme: dark) {
      :root { --bg:#0c1220; --text:#eaf0ff; --muted:#a8b3cf; --card:#0f172a; --border:#1e2a44; --shadow:0 10px 25px rgba(0,0,0,0.35); }
    }
    * { box-sizing: border-box; }
    body { margin: 0; padding: 32px; background: var(--bg); color: var(--text); font-family: Inter, ui-sans-serif, system-ui, -apple-system, Segoe UI, Arial, sans-serif; }
    .container { max-width: 1200px; margin: 0 auto; }

    .form-card, .list-card {
      background: var(--card); border: 1px solid var(--border); border-radius: 18px; padding: 24px; box-shadow: var(--shadow);
    }
    .hdr { display:flex; align-items:center; justify-content:space-between; margin-bottom: 14px; }
    .hdr h1, .hdr h2 { margin: 0; letter-spacing:.2px; }
    .desc, .small { color: var(--muted); }

    .grid { display:grid; gap:16px; grid-template-columns: repeat(12, 1fr); }
    .col-6 { grid-column: span 6; } .col-12 { grid-column: span 12; }
    label { display:block; font-weight:600; margin-bottom:6px; }
    input[type="text"], input[type="number"], select {
      width:100%; border-radius:12px; border:1px solid var(--border); padding:10px 12px;
      background:#fff; color:var(--text); outline:none;
    }
    input[type="file"] { margin-top:6px; }

    .actions { display:flex; gap:12px; align-items:center; margin-top:10px; }
    button.primary {
      border:1px solid #cde6ff; background:linear-gradient(180deg,#e8f5ff 0%,#dff1ff 100%);
      color:#0b3a6a; font-weight:700; padding:10px 14px; border-radius:12px; cursor:pointer;
      box-shadow:0 6px 20px rgba(14,165,233,0.25); display:inline-flex; align-items:center; gap:10px;
    }
    button.primary[disabled]{ opacity:.6; cursor:not-allowed; }
    .spinner { width:16px; height:16px; border:2px solid #94caff; border-top-color:transparent; border-radius:50%; display:none; animation:spin .9s linear infinite; }
    .show .spinner { display:inline-block; }
    @keyframes spin { to { transform: rotate(360deg); } }
    .status { font-size:13px; color:var(--muted); }

    .results { margin-top:24px; display:grid; gap:16px; grid-template-columns: repeat(12, 1fr); }
    .topic { grid-column: span 12; background:var(--card); border:1px solid var(--border); border-radius:16px; padding:18px; box-shadow:var(--shadow); }
    .topic .t-head { display:flex; align-items:center; justify-content:space-between; gap:12px; }
    .topic h3 { margin:0; font-size:18px; line-height:1.35; }
    .pill { font-size:12px; font-weight:700; padding:4px 10px; border-radius:999px; display:inline-flex; align-items:center; gap:8px; border:1px solid transparent; }
    .pill.info { color:#2563eb; background:#eaf1ff; border-color: rgba(37,99,235,.2); }
    .pill.comm { color:#b45309; background:#fff6e6; border-color: rgba(180,83,9,.2); }
    .pill.trans { color:#059669; background:#e8fff4; border-color: rgba(5,150,105,.2); }
    .pill.nav { color:#7c3aed; background:#f3e8ff; border-color: rgba(124,58,237,.2); }
    .small { font-size:12px; }
    .meta-row { display:flex; align-items:center; gap:12px; margin:10px 0 6px; color:var(--muted); font-size:13px; }
    .score { padding:3px 8px; border-radius:8px; background:#e6f6ff; color:#0b4d6a; font-weight:700; border:1px solid #cde6ff; }
    .bar { height:8px; background:#eef3f9; border:1px solid var(--border); border-radius:999px; overflow:hidden; }
    .bar > div { height:100%; background:linear-gradient(90deg,#22c55e,#16a34a); width:0%; }
    .topic-grid { display:grid; gap:16px; margin-top:12px; grid-template-columns:2fr 1fr; }
    .kw-list { display:flex; flex-wrap:wrap; gap:8px; margin-top:8px; }
    .kw { background:#f1f5f9; border:1px solid #e2e8f0; color:#0f172a; padding:4px 10px; border-radius:999px; font-size:12px; font-weight:600; }
    .kw .vol { color:#64748b; font-weight:600; margin-left:6px; }
    .outline li { margin:4px 0; }

    .list-card { margin-top:24px; }
    table { width:100%; border-collapse: collapse; }
    th, td { padding:10px 8px; border-bottom:1px solid var(--border); text-align:left; font-size:14px; }
    th { color:#475569; }
    .btn-sm { border:1px solid var(--border); background:#f8fbff; color:#0b3a6a; padding:6px 10px; border-radius:8px; cursor:pointer; }
    .btn-sm:hover { background:#eef7ff; }
    .json-raw { margin-top:18px; background:#f9fbff; border:1px solid var(--border); border-radius:12px; padding:12px; max-height:380px; overflow:auto; color:#1f2937; }
  </style>
</head>
<body>
  <div class="container">
    <div class="form-card">
      <div class="hdr">
        <h1>Blog Keyword Analyzer</h1>
        <div class="small">Cluster keywords → Generate topics → Export JSON</div>
      </div>
      <p class="desc">Upload a CSV/XLSX or run with the default data folder. The agent analyzes and clusters your keywords, then proposes high-quality topics.</p>

      <form id="runForm" method="post" action="/api/run" enctype="multipart/form-data" onsubmit="return onRun(event);" novalidate>
        <div class="grid">
          <div class="col-6">
            <label>Brand</label>
            <select id="brandSelect" name="brand" required>
              <!-- Options populated from /api/brands -->
            </select>
          </div>
          <div class="col-6">
            <label>Product</label>
            <select id="productSelect" name="product" required>
              <!-- Options populated based on selected brand -->
            </select>
          </div>
          <div class="col-6"><label>Locale</label><input name="locale" type="text" value="en-US" /></div>
          <div class="col-6"><label>Top clusters</label><input name="top_clusters" type="number" value="12" /><div class="small">How many clusters to summarize & generate topics for</div></div>
          <div class="col-12"><label>Keyword file (.csv / .xlsx)</label><input name="file" type="file" accept=".csv,.xlsx" /></div>
        </div>
        <div class="actions">
          <button type="submit" id="runBtn" class="primary"><span class="spinner" aria-hidden="true"></span><span>Run Agent</span></button>
          <span id="status" class="status"></span>
        </div>
      </form>
    </div>

    <!-- Previous runs -->
    <div class="list-card">
      <div class="hdr">
        <div style="display:flex;align-items:center;gap:8px;">
          <h2>Previous runs</h2>
          <button
            type="button"
            id="togglePrevBtn"
            class="btn-sm"
            onclick="togglePreviousRuns()"
          >
            Show
          </button>
        </div>
        <div class="small">Loaded from <code>KRA_OUTPUT_DIR</code></div>
      </div>
    
      <!-- Wrap the table in a section we can hide/show -->
      <div id="previousRunsSection" style="display:none;">
        <div id="listWrap">
          <table>
            <thead>
              <tr>
                <th>File</th>
                <th>Modified</th>
                <th>Size</th>
                <th></th>
              </tr>
            </thead>
            <tbody id="runsBody">
              <tr>
                <td colspan="4" class="small">Loading…</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <div class="results" id="results"></div>
    <div class="json-raw" id="output">No run yet.</div>
  </div>

  <script>
    const form = document.getElementById('runForm');
    const btn  = document.getElementById('runBtn');
    const out  = document.getElementById('output');
    const statusEl = document.getElementById('status');
    const resultsEl = document.getElementById('results');
    const runsBody = document.getElementById('runsBody');

    const brandSelect = document.getElementById('brandSelect');
    const productSelect = document.getElementById('productSelect');

    let BRAND_DATA = {};

    function setBusy(busy) {
      if (busy) { btn.classList.add('show'); btn.setAttribute('disabled','disabled'); statusEl.textContent = 'Running…'; }
      else { btn.classList.remove('show'); btn.removeAttribute('disabled'); statusEl.textContent = ''; }
    }

    async function parseJsonSafe(res) {
      const text = await res.text();
      try { return [res.ok, JSON.parse(text)]; }
      catch { return [res.ok, { error:'Non-JSON response from server', status:res.status, statusText:res.statusText, body:text.slice(0,1000) }]; }
    }

    function fmt(n) {
      if (n === null || n === undefined) return "—";
      if (typeof n !== "number") n = Number(n);
      if (Number.isNaN(n)) return "—";
      if (n >= 1000) return Math.round(n).toLocaleString();
      return String(Math.round(n));
    }

    function fmtCompLabel(label, index) {
      if (label) {
        const nice = label.charAt(0).toUpperCase() + label.slice(1);
        return index != null && !Number.isNaN(Number(index))
          ? `${nice} (${Number(index) <= 1.5 ? Number(index).toFixed(2) : Math.round(Number(index))}%)`
          : nice;
      }
      if (index == null || Number.isNaN(Number(index))) return "—";
      const n = Number(index);
      return n <= 1.5 ? n.toFixed(2) : `${Math.round(n)}%`;
    }

    function pillClass(intent) {
      const x = (intent || "").toLowerCase();
      if (x.startsWith("trans")) return "pill trans";
      if (x.startsWith("comm"))  return "pill comm";
      if (x.startsWith("nav"))   return "pill nav";
      return "pill info";
    }

    function barPct(brandFit) {
      const p = Math.max(0, Math.min(1, Number(brandFit || 0)));
      const pct = Math.round(p * 100);
      return `<div class="bar"><div style="width:${pct}%"></div></div>`;
    }

    // -------- JSON normalizer (handles older/newer artifact shapes) --------
    function normalizePayload(d) {
      if (!d || typeof d !== "object") return { topics: [], clusters: [] };
      const candidates = [d, d.result, d.data, d.payload, d.output].filter(Boolean);
      for (const c of candidates) {
        if (Array.isArray(c?.topics) && Array.isArray(c?.clusters)) return { topics: c.topics, clusters: c.clusters };
      }
      let topics = [], clusters = [];
      for (const c of candidates) {
        if (!topics.length && Array.isArray(c?.topics)) topics = c.topics;
        if (!clusters.length && Array.isArray(c?.clusters)) clusters = c.clusters;
      }
      return { topics, clusters };
    }

    function renderResults(data) {
      resultsEl.innerHTML = "";
      if (!data || !Array.isArray(data.topics) || !Array.isArray(data.clusters)) {
        resultsEl.innerHTML = "<div class='small'>No topics found.</div>";
        return;
      }
      const clusters = {};
      for (const c of data.clusters) clusters[c.cluster_id] = c;

      const frag = document.createDocumentFragment();
      for (const t of data.topics) {
        const c = clusters[t.cluster_id] || null;
        const intent = c?.metrics?.intent ?? "informational";
        const rawScore = c?.metrics?.score ?? 0;
        const score = (typeof rawScore === "number") ? rawScore : Number(rawScore || 0);
        const brandFit = c?.metrics?.brand_fit ?? 0;
        const label = c?.label ?? "—";

        let members = [];
        if (c?.members?.length) {
          members = [...c.members]
            .map(m => ({ kw: m.keyword, vol: (m.volume ?? null), comp: (m.competition ?? null), compLabel: (m.competition_label ?? null) }))
            .sort((a,b) => (b.vol ?? -1) - (a.vol ?? -1))
            .slice(0, 6);
        }
        const kwChips = members.length
          ? members.map(m => `
              <span class="kw">
                ${m.kw}
                <span class="vol"> · ${fmt(m.vol)}</span>
                <span class="vol"> · C ${fmtCompLabel(m.compLabel, m.comp)}</span>
              </span>
            `).join(" ")
          : "<span class='small'>No volumes available</span>";

        const outline = Array.isArray(t.outline) ? t.outline.map(i => `<li>${i}</li>`).join("") : "";

        const el = document.createElement("div");
        el.className = "topic";
        el.innerHTML = `
          <div class="t-head">
            <h3>${t.title}</h3>
            <span class="${pillClass(intent)}">${intent}</span>
          </div>
          <div class="meta-row">
            <span>Cluster: <b>${label}</b></span>
            <span class="score">Score: ${score.toFixed ? score.toFixed(3) : score}</span>
            <span>Brand fit</span>
          </div>
          ${barPct(brandFit)}
          <div class="topic-grid">
            <div>
              <div><b>Angle:</b> ${t.angle || "—"}</div>
              <div style="margin-top:6px;"><b>Persona:</b> ${t.target_persona || "—"}</div>
              <div style="margin-top:6px;"><b>Primary keyword:</b> ${t.primary_keyword || "—"}</div>
              <div style="margin-top:6px;"><b>Supporting keywords:</b></div>
              <div class="kw-list" style="margin-top:6px;">
                ${(t.supporting_keywords || []).map(k => `<span class="kw">${k}</span>`).join(" ")}
              </div>
              ${Array.isArray(t.outline) && t.outline.length ? `<div style="margin-top:10px;"><b>Outline</b><ul class="outline">${outline}</ul></div>` : ""}
            </div>
            <div>
              <div><b>Top keywords in cluster</b> (by volume; <span class="small">C = Competition</span>)</div>
              <div class="kw-list" style="margin-top:6px;">${kwChips}</div>
            </div>
          </div>
        `;
        frag.appendChild(el);
      }
      resultsEl.appendChild(frag);
      <!--
      out.innerHTML = `<div><b>Raw JSON (debug):</b></div><pre>${JSON.stringify(data, null, 2)}</pre>`;
      -->
    }

    async function onRun(e) {
      if (e) e.preventDefault();
      const fd = new FormData(form);
      setBusy(true);
      resultsEl.innerHTML = "";
      out.textContent = "Working…";
      try {
        const res = await fetch('/api/run', { method: 'POST', body: fd });
        const [ok, data] = await parseJsonSafe(res);
        out.textContent = JSON.stringify(data, null, 2);
        if (ok) {
          const norm = normalizePayload(data);
          renderResults(norm);
          statusEl.textContent = "Done.";
        } else {
          statusEl.textContent = `Error (${res.status})`;
        }
      } catch (err) {
        out.textContent = String(err);
        statusEl.textContent = "Network error";
      } finally {
        setBusy(false);
      }
      return false;
    }

    // -------- Brand & product dropdowns --------
    function populateBrands() {
      if (!brandSelect) return;

      brandSelect.innerHTML = "";
      productSelect.innerHTML = "";

      const brands = Object.keys(BRAND_DATA).sort();
      if (!brands.length) {
        const opt = document.createElement('option');
        opt.value = "";
        opt.textContent = "No brands available";
        brandSelect.appendChild(opt);
        brandSelect.disabled = true;
        productSelect.disabled = true;
        return;
      }

      const placeholder = document.createElement('option');
      placeholder.value = "";
      placeholder.textContent = "Select brand";
      placeholder.disabled = true;
      placeholder.selected = true;
      brandSelect.appendChild(placeholder);

      for (const b of brands) {
        const opt = document.createElement('option');
        opt.value = b;
        opt.textContent = b;
        brandSelect.appendChild(opt);
      }

      brandSelect.disabled = false;
      productSelect.disabled = false;

      // Auto-select default brand if available
      const defaultBrand = "aspose.com";
      if (brands.includes(defaultBrand)) {
        brandSelect.value = defaultBrand;
        onBrandChange();
      }
    }

    function onBrandChange() {
      if (!brandSelect || !productSelect) return;
      const brand = brandSelect.value;
      const products = Array.isArray(BRAND_DATA[brand]) ? BRAND_DATA[brand] : [];

      productSelect.innerHTML = "";

      if (!products.length) {
        const opt = document.createElement('option');
        opt.value = "";
        opt.textContent = "No products available";
        productSelect.appendChild(opt);
        return;
      }

      for (const p of products) {
        const opt = document.createElement('option');
        opt.value = p;
        opt.textContent = p;
        productSelect.appendChild(opt);
      }

      // Optional: set a sensible default product for Aspose
      if (brand === "aspose.com" && products.includes("Aspose.Cells")) {
        productSelect.value = "Aspose.Cells";
      }
    }

    async function loadBrands() {
      try {
        const res = await fetch('/api/brands');
        const [ok, data] = await parseJsonSafe(res);
        if (!ok || !data || typeof data !== "object") {
          console.warn("Failed to load brands:", data);
          return;
        }
        BRAND_DATA = data;
        populateBrands();
      } catch (e) {
        console.error("Error loading brands:", e);
      }
    }

    if (brandSelect) {
      brandSelect.addEventListener('change', onBrandChange);
    }

    // -------- Previous runs UI --------
    async function refreshRuns() {
      runsBody.innerHTML = `<tr><td colspan="4" class="small">Loading…</td></tr>`;
      try {
        const res = await fetch('/api/list');
        const [ok, data] = await parseJsonSafe(res);
        if (!ok) { runsBody.innerHTML = `<tr><td colspan="4">Error loading list</td></tr>`; return; }
        if (!Array.isArray(data) || data.length === 0) {
          runsBody.innerHTML = `<tr><td colspan="4" class="small">No artifacts found</td></tr>`;
          return;
        }
        runsBody.innerHTML = data.map(row => `
          <tr>
            <td>${row.name}</td>
            <td>${row.modified}</td>
            <td>${row.size_human}</td>
            <td><button class="btn-sm" onclick="loadRun('${encodeURIComponent(row.name)}')">Load</button></td>
          </tr>
        `).join("");
      } catch (e) {
        runsBody.innerHTML = `<tr><td colspan="4">Failed to load list</td></tr>`;
      }
    }

    function togglePreviousRuns() {
		const section = document.getElementById("previousRunsSection");
		const btn = document.getElementById("togglePrevBtn");

		// If display is '' (default) or not set, treat it as visible
		const isHidden = section.style.display === "none";

		if (isHidden) {
		  section.style.display = "";
		  btn.textContent = "Hide";
		} else {
		  section.style.display = "none";
		  btn.textContent = "Show";
		}
	}
    async function loadRun(name) {
      resultsEl.innerHTML = "";
      out.textContent = "Loading artifact…";
      try {
        const res = await fetch(`/api/load?name=${name}`);
        const [ok, data] = await parseJsonSafe(res);
        out.textContent = JSON.stringify(data, null, 2);
        if (ok) {
          const norm = normalizePayload(data);
          renderResults(norm);
          statusEl.textContent = "Loaded.";
        } else {
          statusEl.textContent = `Error (${res.status})`;
        }
      } catch (e) {
        out.textContent = String(e);
        statusEl.textContent = "Network error";
      }
      return false;
    }

    // init
    loadBrands();
    refreshRuns();
  </script>
</body>
</html>
"""


# ---------- APIs ----------

@app.get("/api/brands")
def list_brands() -> JSONResponse:
    """
    Return brand -> products mapping loaded from brands.json (or defaults).
    """
    data = _load_brands()
    return JSONResponse(content=data)


@app.get("/api/list")
def list_artifacts(limit: int = 50) -> JSONResponse:
    """
    List recent JSON artifacts from KRA_OUTPUT_DIR (sorted by mtime desc).
    Returns: [{name, size, size_human, modified, path}]
    """
    out_dir = _outputs_dir()
    items = []
    for p in sorted(out_dir.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True)[: max(1, limit)]:
        st = p.stat()
        size = st.st_size
        size_h = f"{size/1024:.1f} KB" if size < 1024*1024 else f"{size/1024/1024:.2f} MB"
        from datetime import datetime
        modified = datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        items.append({
            "name": p.name,
            "size": size,
            "size_human": size_h,
            "modified": modified,
            "path": str(p),
        })
    return JSONResponse(content=items)


@app.get("/api/load")
def load_artifact(name: str = Query(..., description="Artifact file name, e.g. kra_result_1234.json")) -> JSONResponse:
    """
    Load a single artifact JSON by file name (prevent path traversal).
    """
    out_dir = _outputs_dir()
    if "/" in name or "\\" in name or name.startswith("."):
        return JSONResponse(status_code=400, content={"error": "Invalid file name"})
    p = out_dir / name
    if not (p.exists() and p.is_file() and p.suffix.lower() == ".json"):
        return JSONResponse(status_code=404, content={"error": "Artifact not found"})
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return JSONResponse(content=data)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"Failed to parse JSON: {e}"})


@app.post("/api/run")
async def api_run(
    file: Optional[UploadFile] = File(default=None),
    brand: str = Form(default="Aspose"),
    product: str = Form(default="Aspose.Cells"),
    locale: str = Form(default="en-US"),
    top_clusters: int = Form(default=12),
    k: Optional[int] = Form(default=None),
) -> JSONResponse:
    """
    Run the agent with an optional uploaded file.
    If no file is provided, the importer will look in KRA_DATA_DIR for keywords.(csv|xlsx).
    Saves JSON to KRA_OUTPUT_DIR and returns the full RunResult + artifact_path.
    """
    try:
        if not settings.ASPOSE_LLM_API_KEY:
            raise HTTPException(status_code=400, detail="Missing OPENAI_API_KEY in environment/.env")

        root = _project_root()
        data_dir = Path(settings.KRA_DATA_DIR)
        if not data_dir.is_absolute():
            data_dir = (root / data_dir).resolve()
        _ensure_dir(data_dir)

        file_path = ""
        if file is not None:
            ext = Path(file.filename).suffix.lower() if file.filename else ".csv"
            tmp_name = f"upload_{uuid.uuid4().hex[:8]}{ext}"
            save_path = data_dir / tmp_name
            content = await file.read()
            save_path.write_bytes(content)
            file_path = str(save_path)

        req = RunRequest(
            brand=brand,
            product=product,
            locale=locale,
            file_path=file_path,          # empty => importer searches defaults
            clustering_k=k,
            top_clusters=int(top_clusters),
            max_rows=settings.MAX_ROWS,
        )

        result = run_sync(req)

        out_dir = _outputs_dir()
        out_path = out_dir / f"kra_result_{result.run_id}.json"
        out_path.write_text(result.model_dump_json(indent=2), encoding="utf-8")

        payload = result.model_dump()
        payload["artifact_path"] = str(out_path)
        return JSONResponse(content=payload)

    except HTTPException as he:
        return JSONResponse(status_code=he.status_code, content={"error": he.detail})
    except ValidationError as ve:
        return JSONResponse(status_code=400, content={"error": "Invalid request", "detail": ve.errors()})
    except Exception as e:
        payload = {"error": str(e)}
        if getattr(settings, "DEBUG", False):
            payload["trace"] = traceback.format_exc()
        return JSONResponse(status_code=500, content=payload)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
