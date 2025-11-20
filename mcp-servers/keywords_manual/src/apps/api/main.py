# src/apps/api/main.py
from __future__ import annotations

import uuid
import traceback
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import ValidationError

from agents.kra.config import settings
from agents.kra.schemas import RunRequest
from agents.kra.runner import run_sync

app = FastAPI(title="Blog Keyword Analyzer UI/API", version="0.1.0")

# CORS for local dev (tighten in prod)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

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

@app.get("/", response_class=HTMLResponse)
def index() -> str:
    """Single-page UI (plain string; no f-string to avoid JS/CSS interpolation issues)."""
    return """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>Blog Keyword Analyzer</title>
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
      :root {
        --bg: #0c1220; --text: #eaf0ff; --muted: #a8b3cf;
        --card: #0f172a; --border: #1e2a44; --shadow: 0 10px 25px rgba(0,0,0,0.35);
      }
    }
    * { box-sizing: border-box; }
    body { margin: 0; padding: 32px; background: var(--bg); color: var(--text); font-family: Inter, ui-sans-serif, system-ui, -apple-system, Segoe UI, Arial, sans-serif; }
    .container { max-width: 1200px; margin: 0 auto; }

    .form-card { background: var(--card); border: 1px solid var(--border); border-radius: 18px; padding: 24px; box-shadow: var(--shadow); }
    .hdr { display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px; }
    .hdr h1 { font-size: 22px; margin: 0; letter-spacing: .2px; }
    .desc { color: var(--muted); margin: 0 0 14px 0; }

    .grid { display: grid; gap: 16px; grid-template-columns: repeat(12, 1fr); }
    .col-6 { grid-column: span 6; } .col-12 { grid-column: span 12; }
    label { display:block; font-weight: 600; margin-bottom: 6px; }
    input[type="text"], input[type="number"] { width: 100%; border-radius: 12px; border: 1px solid var(--border); padding: 10px 12px; background: #fff; color: var(--text); outline: none; }
    input[type="file"] { margin-top: 6px; }

    .actions { display:flex; gap: 12px; align-items:center; margin-top: 10px; }
    button.primary {
      border: 1px solid #cde6ff; background: linear-gradient(180deg, #e8f5ff 0%, #dff1ff 100%);
      color: #0b3a6a; font-weight: 700; padding: 10px 14px; border-radius: 12px; cursor: pointer;
      box-shadow: 0 6px 20px rgba(14,165,233,0.25); display: inline-flex; align-items: center; gap: 10px;
    }
    button.primary[disabled] { opacity: .6; cursor: not-allowed; }
    .spinner {
      width: 16px; height: 16px; border: 2px solid #94caff; border-top-color: transparent; border-radius: 50%;
      display: none; animation: spin 0.9s linear infinite;
    }
    .show .spinner { display: inline-block; }
    @keyframes spin { to { transform: rotate(360deg); } }
    .hint { font-size: 12px; color: var(--muted); margin-top: 4px; }
    .status { font-size: 13px; color: var(--muted); }

    .results { margin-top: 24px; display: grid; gap: 16px; grid-template-columns: repeat(12, 1fr); }
    .topic { grid-column: span 12; background: var(--card); border: 1px solid var(--border); border-radius: 16px; padding: 18px; box-shadow: var(--shadow); }
    .topic .t-head { display:flex; align-items:center; justify-content: space-between; gap: 12px; }
    .topic h3 { margin: 0; font-size: 18px; line-height: 1.35; }
    .pill { font-size: 12px; font-weight: 700; padding: 4px 10px; border-radius: 999px; display:inline-flex; align-items:center; gap:8px; border: 1px solid transparent; }
    .pill.info { color: var(--info); background: var(--info-soft); border-color: rgba(37,99,235,.2); }
    .pill.comm { color: var(--comm); background: var(--comm-soft); border-color: rgba(180,83,9,.2); }
    .pill.trans { color: var(--trans); background: var(--trans-soft); border-color: rgba(5,150,105,.2); }
    .pill.nav { color: var(--nav); background: var(--nav-soft); border-color: rgba(124,58,237,.2); }
    .small { font-size: 12px; color: var(--muted); }
    .meta-row { display:flex; align-items:center; gap: 12px; margin: 10px 0 6px; color: var(--muted); font-size: 13px; }
    .score { padding: 3px 8px; border-radius: 8px; background: var(--accent-soft); color: #0b4d6a; font-weight: 700; border: 1px solid #cde6ff; }
    .bar { height: 8px; background: #eef3f9; border: 1px solid var(--border); border-radius: 999px; overflow: hidden; }
    .bar > div { height: 100%; background: linear-gradient(90deg, #22c55e, #16a34a); width: 0%; }
    .topic-grid { display: grid; gap: 16px; margin-top: 12px; grid-template-columns: 2fr 1fr; }
    .kw-list { display:flex; flex-wrap: wrap; gap: 8px; margin-top: 8px; }
    .kw { background: #f1f5f9; border: 1px solid #e2e8f0; color: #0f172a; padding: 4px 10px; border-radius: 999px; font-size: 12px; font-weight: 600; }
    .kw .vol { color: #64748b; font-weight: 600; margin-left: 6px; }
    .outline li { margin: 4px 0; }
    .artifact { margin-top: 12px; display:flex; align-items:center; gap: 12px; font-size: 13px; color: var(--muted); }
    .artifact a { color: var(--accent); font-weight: 700; text-decoration: none; border-bottom: 1px dashed var(--accent); }
    .json-raw { margin-top: 18px; background: #f9fbff; border: 1px solid var(--border); border-radius: 12px; padding: 12px; max-height: 380px; overflow: auto; color: #1f2937; }
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

      <!-- Important: method/action/enctype for graceful fallback; JS will intercept via onRun(...) -->
      <form id="runForm" method="post" action="/api/run" enctype="multipart/form-data" onsubmit="return onRun(event);" novalidate>
        <div class="grid">
          <div class="col-6">
            <label>Brand</label>
            <input name="brand" type="text" value="Aspose" required />
          </div>
          <div class="col-6">
            <label>Product</label>
            <input name="product" type="text" value="Aspose.Cells" required />
          </div>

          <div class="col-6">
            <label>Locale</label>
            <input name="locale" type="text" value="en-US" />
          </div>
          <div class="col-6">
            <label>Top clusters</label>
            <input name="top_clusters" type="number" value="12" />
            <div class="hint">How many clusters to summarize & generate topics for</div>
          </div>

          <div class="col-12">
            <label>Keyword file (.csv / .xlsx) — optional</label>
            <input name="file" type="file" accept=".csv,.xlsx" />
          </div>
        </div>

        <div class="actions">
          <button type="submit" id="runBtn" class="primary">
            <span class="spinner" aria-hidden="true"></span>
            <span>Run Agent</span>
          </button>
          <span id="status" class="status"></span>
        </div>
      </form>
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

    function setBusy(busy) {
      if (busy) {
        btn.classList.add('show');
        btn.setAttribute('disabled', 'disabled');
        statusEl.textContent = 'Running…';
      } else {
        btn.classList.remove('show');
        btn.removeAttribute('disabled');
        statusEl.textContent = '';
      }
    }

    async function parseJsonSafe(res) {
      const text = await res.text();
      try { return [res.ok, JSON.parse(text)]; }
      catch { return [res.ok, { error: 'Non-JSON response from server', status: res.status, statusText: res.statusText, body: text.slice(0, 1000) }]; }
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

    function renderResults(data) {
      resultsEl.innerHTML = "";
      if (!data || !data.topics || !data.clusters) {
        resultsEl.innerHTML = "<div class='small'>No topics found.</div>";
        return;
      }
      const clusters = {};
      for (const c of data.clusters) clusters[c.cluster_id] = c;

      const frag = document.createDocumentFragment();
      for (const t of data.topics) {
        const c = clusters[t.cluster_id] || null;
        const intent = c?.metrics?.intent ?? "informational";
        const score = c?.metrics?.score ?? 0;
        const brandFit = c?.metrics?.brand_fit ?? 0;
        const label = c?.label ?? "—";

        let members = [];
        if (c?.members?.length) {
          members = [...c.members]
            .map(m => ({
              kw: m.keyword,
              vol: (m.volume ?? null),
              comp: (m.competition ?? null),
              compLabel: (m.competition_label ?? null)
            }))
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
            <span class="score">Score: ${score?.toFixed ? score.toFixed(3) : score}</span>
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

      out.innerHTML = `<div><b>Raw JSON (debug):</b></div><pre>${JSON.stringify(data, null, 2)}</pre>`;
      if (data.artifact_path) {
        const a = document.createElement("div");
        a.className = "artifact";
        a.innerHTML = `Saved to: <a href="#" onclick="return false;">${data.artifact_path}</a>`;
        resultsEl.appendChild(a);
      }
    }

    // Bound via onsubmit HTML attribute so we *always* intercept
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
          renderResults(data);
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
      return false; // prevent default navigation
    }
  </script>
</body>
</html>
"""

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
        if not settings.OPENAI_API_KEY:
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
            file_path=file_path,
            clustering_k=k,
            top_clusters=int(top_clusters),
            max_rows=settings.MAX_ROWS,
        )

        result = run_sync(req)

        out_root = Path(settings.KRA_OUTPUT_DIR)
        if not out_root.is_absolute():
            out_root = (root / out_root).resolve()
        _ensure_dir(out_root)
        out_path = out_root / f"kra_result_{result.run_id}.json"
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
