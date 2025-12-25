# Blog Keyword Analyzer Agent

Version: 1.0

**Blog Keyword Analyzer** groups your keywords, scores real opportunity, and spits out on-brand topics you can ship next.

## Overview

**Turns raw keywords into a ranked content plan.**

Upload a CSV/XLSX from Google Keyword Planner (or connect via API when available), and the agent clusters related queries, scores opportunity (volume, difficulty, intent, brand-fit), and generates ready-to-publish topic ideas. It understands semantic relationships and search intent to deliver actionable content strategies, not just keyword lists.

Built for content teams managing multiple blog properties (aspose.com, groupdocs.com, etc.), this agent eliminates hours of manual keyword analysis and turns data into decisions in minutes.

---

## What It Does / Features

- **Smart Clustering**: Groups keywords by semantic similarity and user intent
- **Intent Classification**: Identifies commercial, informational, and navigational queries
- **Opportunity Scoring**: Ranks clusters by volume, competition, and brand alignment
- **Topic Generation**: Produces SEO-optimized blog titles mapped to specific keyword clusters
- **Dual Interface**: CLI for automation + Web UI for quick testing
- **File ingest**: `.xlsx` / `.csv` (robust encoding + delimiter detection).

---

## Built With

- **LLM**: Professionalize LLM’s gpt-oss model
- **Backend**: Python 3.x
- **Web UI**: FastAPI + Uvicorn
- **Input Formats**: CSV, XLSX (Google Keyword Planner exports)

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
# === Required ===
CUSTOM_LLM_BASE_URL="https://llm.professionalize.com/v1"
CUSTOM_LLM_API_KEY="sk-"

# Which model name the agent should use by default
DEFAULT_LLM_MODEL="gpt-oss"
```

> Put `keywords.csv` in the relevant folder:
> For Aspose: `content/keywrods_data/Asposes/`.
> For Conholdate: `content/keywrods_data/Conholdate/`.
> For Familiarize: `content/keywrods_data/Familiarize/`.
> For GroupDocs: `content/keywrods_data/GroupDocs/`.

---

## Running via CLI or Script

From the project root:

### 1. Config-based Run – Using `kra_run.yaml` (recommended)

Each brand has a `kra_run.yaml` describing:

* Input CSV (`engine.input_file`)
* Brand / product / platform
* Whether to use content index
* Content index settings (local root, repo URL, etc.)

The helper script `scripts/run_kra_from_config.py` reads that file and runs the agent with the right parameters. You can always change the parameters in `kra_run.yaml` as per the requirements.

#### Aspose

```bash
python scripts/run_kra_from_config.py --config content/Aspose/kra_run.yaml
```

#### GroupDocs

```bash
python scripts/run_kra_from_config.py --config content/GroupDocs/kra_run.yaml
```

#### Conholdate

```bash
python scripts/run_kra_from_config.py --config content/Conholdate/kra_run.yaml
```

#### Familiarize

```bash
python scripts/run_kra_from_config.py --config content/Familiarize/kra_run.yaml
```

---

### 2. Direct CLI – Run KRA via `runner.py`

These commands call the agent directly using the Python module entrypoint.

#### Aspose

```bash
python -m src.agent_engine.kra.runner \
  --file content/Aspose/keywords.csv \
  --brand Aspose \
  --product "Aspose.Cells" \
  --locale en-US \
  --top 10 \
  --max-rows 50000 \
  --platform python
```

To temporarily disable content index:

```bash
python -m src.agent_engine.kra.runner \
  --file content/Aspose/keywords.csv \
  --brand Aspose \
  --product "Aspose.Cells" \
  --locale en-US \
  --top 10 \
  --max-rows 50000 \
  --platform python \
  --no-content-index
```

#### GroupDocs

```bash
python -m src.agent_engine.kra.runner \
  --file content/GroupDocs/keywords.csv \
  --brand GroupDocs \
  --product "GroupDocs.Viewer" \
  --locale en-US \
  --top 10 \
  --max-rows 50000 \
  --platform csharp
```

#### Conholdate

```bash
python -m src.agent_engine.kra.runner \
  --file content/Conholdate/keywords.csv \
  --brand Conholdate \
  --product "Conholdate.Total" \
  --locale en-US \
  --top 10 \
  --max-rows 50000 \
  --platform python
```

#### Familiarize

```bash
python -m src.agent_engine.kra.runner \
  --file content/Familiarize/keywords.csv \
  --brand Familiarize \
  --product "Risk Management" \
  --locale en-US \
  --top 10 \
  --max-rows 50000
```

---

### 3. Outputs

Each run produces:

* **Topics Markdown** (human-friendly list of generated topics)

  * e.g. `content/kra_results/kra_result_<brand>_<id>_topics.md`
  
* **Metrics DB JSON** (small “database” of all runs)

  * e.g. `src/data/kra_metrics_db.json` or the path configured via `KRA_METRICS_DB_PATH`

You can change the metrics DB location via environment:

```bash
export KRA_METRICS_DB_PATH="content/kra_results/kra_metrics_db.json"
```

## Running Web UI (+ API)

```bash
python -m uvicorn src.apps.api.main:app --reload --port 8000
```

Open [http://localhost:8000](http://localhost:8000)

* Fill **Brand/Product/Locale/Top clusters**
* Optionally **upload `.csv`/`.xlsx`** or use default file in `KRA_DATA_DIR`
* Click **Run Agent** (spinner shows) → topic cards render.
* Full JSON saved to `KRA_OUTPUT_DIR/kra_result_<run_id>.json`.


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

## Troubleshooting

* **“ModuleNotFoundError: No module named apps.api”**
  Ensure `src/apps/__init__.py` and `src/apps/api/__init__.py` exist and run uvicorn with `--app-dir src`.

* **“Unexpected token 'I' … not valid JSON” in UI**
  Server sent an HTML 500. Backend now returns JSON errors; keep `DEBUG=true` to see `trace`.

* **“Input file not found” (no upload)**
  Put `keywords.xlsx` or `keywords.csv` in `KRA_DATA_DIR` (`./content/keywords_data` by default) or pass `--file`/upload.

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
