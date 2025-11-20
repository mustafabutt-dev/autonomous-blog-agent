# Blog Keyword Analyzer Agent

**Blog Keyword Analyzer** groups your keywords, scores real opportunity, and spits out on-brand topics you can ship next—no spreadsheet wrangling required.

**Turns raw keyword exports into a ranked content plan.**
Upload a CSV/XLSX (or plug in Google Keyword Planner / Ahrefs), the agent clusters related queries, scores opportunity (volume, difficulty, CPC, competition, brand-fit, intent), and generates on-brand topic ideas—available via API + a lightweight web UI.

---

## Features

* **File ingest**: `.xlsx` / `.csv` (robust encoding + delimiter detection).
* **Clustering**: groups semantically related keywords.
* **Scoring**: blends volume, KD, CPC, competition, brand-fit, and intent.
* **Topic generation**: LLM-guided, on-brand titles + outline + supporting keywords.
* **Web UI**: upload or run defaults; pretty topic cards; spinner; debug JSON.
* **API**: single `POST /api/run` returns full JSON and writes an artifact file.

---

## Project Structure

```
my-agents/
  .env
  pyproject.toml
  requirements.txt
  src/
    agents/
      __init__.py
      kra/
        __init__.py
        config.py          # Settings via .env (paths, weights, model)
        schemas.py         # Pydantic models (RunRequest, KeywordRecord, Cluster, Topic, etc.)
        agent.py           # LLM prompts + topic generation
        runner.py          # Orchestrator (import → preprocess → cluster → score → topics)
        tools/
          __init__.py
          file_import.py   # Robust CSV/XLSX reader + header aliasing + number cleaning
          preprocess.py    # Text cleanups, dedupe
          cluster.py       # Vectorize + clustering
          intent_brand.py  # Heuristics/LLM for search intent + brand-fit
          scoring.py       # Cluster scoring (weights + normalization)
    apps/
      __init__.py
      api/
        __init__.py
        main.py            # FastAPI app + single-page UI
  src/data/
    keywords.xlsx          # your default dataset (optional)
    outputs/               # JSON run artifacts land here
```

---

## Setup

### 1) Python env + install

```bash
# macOS/Linux
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

```powershell
# Windows PowerShell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -e .
```

### 2) Environment variables (`.env`)

```env
# OpenAI
OPENAI_API_KEY=sk-xxx
DEFAULT_MODEL=gpt-4.1-mini

# Paths
KRA_DATA_DIR=./src/data
KRA_OUTPUT_DIR=./src/data/outputs

# Orchestration knobs
TOP_CLUSTERS=12
MAX_ROWS=50000
DEBUG=true

# (Optional) Scoring weights
W_VOLUME=0.35
W_KD=0.25
W_CPC=0.15
W_BRAND=0.15
W_INTENT=0.10
# W_COMP=0.00   # enable later if you want competition to affect score
```

> Put `keywords.xlsx` or `keywords.csv` in `src/data/` to run without uploading.

---

## Running

### A) Web UI (+ API)

```bash
uvicorn apps.api.main:app --reload --port 8000 --app-dir src
```

Open [http://localhost:8000](http://localhost:8000)

* Fill **Brand/Product/Locale/Top clusters**
* Optionally **upload `.xlsx`/`.csv`** or use default file in `KRA_DATA_DIR`
* Click **Run Agent** (spinner shows) → topic cards render.
* Full JSON saved to `KRA_OUTPUT_DIR/kra_result_<run_id>.json`.

### B) CLI (orchestrator only)

```bash
python -m agents.kra.runner --brand Aspose --product "Aspose.Cells" --top 12
# or point to a file
python -m agents.kra.runner --file ./src/data/keywords.xlsx --brand Aspose --product "Aspose.Cells"
```

---

## API

### `POST /api/run` (multipart/form-data)

**Fields**

* `file` *(optional)*: CSV/XLSX upload
* `brand` *(str, default “Aspose”)*
* `product` *(str, default “Aspose.Cells”)*
* `locale` *(str, default “en-US”)*
* `top_clusters` *(int, default `.env`)*
* `k` *(int, optional)*: force number of clusters

**Response 200**

```json
{
  "run_id": "a1b2c3d4",
  "brand": "Aspose",
  "product": "Aspose.Cells",
  "locale": "en-US",
  "clusters": [ /* top clusters with metrics + members */ ],
  "topics": [ /* titles, persona, angle, keywords, outline */ ],
  "artifact_path": "src/data/outputs/kra_result_a1b2c3d4.json"
}
```

**Errors** return JSON `{ "error": "...", "trace": "..." }` when `DEBUG=true`.

**Curl examples**

```bash
# Using default file in KRA_DATA_DIR
curl -X POST http://localhost:8000/api/run -F brand=Aspose -F product="Aspose.Cells"

# With upload
curl -X POST http://localhost:8000/api/run \
  -F brand=Aspose -F product="Aspose.Cells" \
  -F file=@src/data/keywords.xlsx
```

---

## Data Expectations

Your CSV/XLSX can use common header variants; importer maps/cleans automatically.

* **Keyword** (required): `keyword | query | search term | term`
* **Volume** (int): `volume | search volume | avg_monthly_searches ...`
* **CPC** (float): `cpc | avg cpc | cost_per_click | cpc (usd)`
* **KD** (float): `kd | difficulty | keyword difficulty`
* **Clicks** (float): `clicks | est_clicks | estimated clicks`
* **URL** (str): `url | landing_page | target_url`
* **Competition**

  * numeric index: `competition | competition_index | competitive density`
  * or **categorical**: `competition level | comp level` → mapped as:
    **low = 0.20**, **medium = 0.60**, **high = 0.90** (label preserved in JSON as `competition_label`)

Importer handles:

* Encodings: `utf-8`, `utf-8-sig`, `utf-16(le/be)`, `latin1`
* Delimiters: commas, semicolons, tabs (`sep=None`, sniffed)
* Mis-labeled files (e.g., `.csv` that’s actually Excel is sniffed by magic bytes)

---

## How Scoring Works (quick)

Each cluster gets a 0–1 **score** blending:

* **Volume** (↑ better)
* **Keyword difficulty (KD)** (↓ better → inverted)
* **CPC** (↑ indicates commercial value)
* **Brand-fit** (0–1; heuristic/LLM match to your product/brand)
* **Intent boost** (informational / commercial / transactional / navigational)

You can tune weights in `.env` (see above). Topics inherit their source **cluster** score to keep lists stable and sortable.

---

## UI Notes

* **Form card** (light theme), spinner on submit, graceful fallback if JS fails.
* **Topic cards** with intent color pills:

  * informational (blue), commercial (amber), transactional (green), navigational (purple)
* **Keyword chips** show: `keyword · volume · C Competition` (label + numeric if available).
* **Brand-fit bar** and **Score** shown for each topic’s cluster.

---

## Troubleshooting

* **“ModuleNotFoundError: No module named apps.api”**
  Ensure `src/apps/__init__.py` and `src/apps/api/__init__.py` exist and run uvicorn with `--app-dir src`.

* **“Unexpected token 'I' … not valid JSON” in UI**
  Server sent an HTML 500. Backend now returns JSON errors; keep `DEBUG=true` to see `trace`.

* **“Input file not found” (no upload)**
  Put `keywords.xlsx` or `keywords.csv` in `KRA_DATA_DIR` (`./src/data` by default) or pass `--file`/upload.

* **“UnicodeDecodeError” or “No columns to parse”**
  Likely UTF-16/TSV/mis-labeled Excel. Importer is resilient; ensure the file isn’t empty and has a header row.

* **Blank UI after clicking Run**
  Ensure the form uses `onsubmit="return onRun(event)"` and no browser console errors. The included `main.py` already wires this.

---

## Extending

* **Live data**: add tools for **Google Keyword Planner** and **Ahrefs**; merge/enrich missing metrics by keyword.
* **Filters**: UI chips for min volume, max KD, competition ≤ medium, intent type.
* **Per-topic scoring**: add editorial signals (title length, persona fit) on top of cluster score.
* **Exports**: CSV/XLSX/Notion/Jira; publish to a CMS.
* **Auth & multi-tenant**: JWT + per-brand configs.

---

## License

Proprietary (internal use). Replace with your chosen license if you plan to distribute.
