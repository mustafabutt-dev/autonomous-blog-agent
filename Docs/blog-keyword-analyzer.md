# Blog Keyword Analyzer – User Manual

## Introduction

The **Blog Keyword Analyzer** is an AI-powered content planning tool that transforms raw keyword data into actionable blog topic recommendations. Instead of spending hours manually analyzing keyword lists, this tool automatically clusters related keywords, evaluates content opportunities, and generates ready-to-publish topic ideas tailored to your brand.

**Who is this for?**  
Content teams, SEO strategists, and blog managers working across multiple brand properties (Aspose, GroupDocs, Conholdate, Familiarize).

**What you'll get:**
- Semantically grouped keyword clusters
- Opportunity scores based on search volume, competition, and brand fit
- AI-generated blog topics mapped to each cluster
- Automated duplicate detection against existing content
- Performance metrics tracking across runs

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Understanding the Workflow](#understanding-the-workflow)
3. [Preparing Your Data](#preparing-your-data)
4. [Configuration Guide](#configuration-guide)
5. [Running the Analyzer](#running-the-analyzer)
6. [Understanding Your Results](#understanding-your-results)
7. [GitHub Actions Automation](#github-actions-automation)
8. [Adding a New Brand](#adding-a-new-brand)
9. [Troubleshooting](#troubleshooting)

---

## Getting Started

### System Requirements

- **Python**: 3.8 or higher
- **Operating System**: Windows, macOS, or Linux
- **API Key**: OpenAI API key or custom LLM provider credentials

### Installation

1. **Clone or download the repository:**
   ```bash
   cd C:\GitHub\Keyword-Analyzer-Demo
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv .venv
   ```

3. **Activate the virtual environment:**
   - **Windows:**
     ```bash
     .venv\Scripts\activate
     ```
   - **macOS/Linux:**
     ```bash
     source .venv/bin/activate
     ```

4. **Install dependencies:**
   ```bash
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```

5. **Configure your API key:**
   - Create an `.env` file in the `env/` directory
   - Add your API credentials:
     ```
     OPENAI_API_KEY=your-api-key-here
     ```
     or
     ```
     CUSTOM_LLM_API_KEY=your-api-key-here
     ```

---

## Understanding the Workflow

The Blog Keyword Analyzer follows a five-stage process:

### 1. **Data Input**
You provide a CSV file containing keywords exported from Google Keyword Planner or similar tools.

### 2. **Keyword Clustering**
The AI groups related keywords based on semantic similarity and user intent (commercial, informational, navigational).

### 3. **Content Index Check** *(Optional)*
The system scans your existing blog content to identify topics already covered, preventing duplicate recommendations.

### 4. **Opportunity Scoring**
Each cluster receives a score based on:
- **Search volume**: How many people search for these terms
- **Competition level**: Keyword difficulty
- **Brand alignment**: Relevance to your product/platform
- **Search intent**: Match with content goals

### 5. **Topic Generation**
The AI generates SEO-optimized blog titles for the highest-priority clusters, complete with:
- Target keywords
- Content angle
- platform/product context
- Publishing recommendations

---

## Preparing Your Data

### Keyword File Format

Your keyword data should be in CSV format with these columns:

| Column Name | Description | Example |
|------------|-------------|---------|
| **Keyword** | Search term or phrase | "convert excel to pdf python" |
| **Avg. monthly searches** | Search volume | 1200 |
| **Competition** | Low/Medium/High | Medium |
| **Top of page bid (low range)** | Optional CPC data | $0.50 |

**Required columns:** At minimum, include `Keyword` and search volume data.

### Exporting from Google Keyword Planner

1. Go to Google Keyword Planner
2. Run your keyword research
3. Click **Download keyword ideas**
4. Choose **CSV** or **Excel format**
5. Save the file

### File Location

Place your keyword file in the appropriate brand directory:

```
content/
├── Aspose/
│   └── keywords.csv
├── GroupDocs/
│   └── keywords.csv
├── Conholdate/
│   └── keywords.csv
└── Familiarize/
    └── keywords.csv
```

---

## Configuration Guide

Each brand has a configuration file (`kra_run.yaml`) that controls how the analyzer runs.

### Configuration File Location

```
content/<Brand>/kra_run.yaml
```

### Configuration Structure

```yaml
engine:
  input_file: "content/Aspose/keywords.csv"
  brand: "Aspose"
  product: "Aspose.Cells"
  platform: "python"
  locale: "en-US"
  top_clusters: 10
  max_rows: 50000
  use_content_index: true

content_index:
  # For local development
  local_root: "C:\\GitHub\\aspose-blog\\content\\Aspose.Blog"
  
  # For CI/CD automation
  repo_url: "https://github.com/Aspose/aspose-blog"
  branch: "main"
  subdir: "/content/Aspose.Blog"
```

### Configuration Parameters

#### Engine Settings

| Parameter | Description | Example Values |
|-----------|-------------|----------------|
| `input_file` | Path to your keyword CSV | `"content/Aspose/keywords.csv"` |
| `brand` | Brand name | `"Aspose"`, `"GroupDocs"` |
| `product` | Specific product line | `"Aspose.Cells"`, `"GroupDocs.Viewer"` |
| `platform` | Target programming language/platform | `"python"`, `"java"`, `"net"` |
| `locale` | Language/region code | `"en-US"`, `"fr-FR"` |
| `top_clusters` | Number of clusters to analyze | `10`, `20`, `50` |
| `max_rows` | Maximum keywords to process | `50000` |
| `use_content_index` | Check for existing content? | `true`, `false` |

#### Content Index Settings

| Parameter | Description | When to Use |
|-----------|-------------|-------------|
| `local_root` | Local path to blog repository | For development on your machine |
| `repo_url` | GitHub repository URL | For CI/CD automation |
| `branch` | Git branch to scan | Usually `"main"` or `"master"` |
| `subdir` | Subdirectory within repo | Path to actual blog content |

---

## Running the Analyzer

You can run the analyzer in two ways: **CLI mode** (for automation) or **config-based mode** (recommended for consistency).

### Option 1: Config-Based Run (Recommended)

This method uses your `kra_run.yaml` configuration file and mirrors the automated CI/CD process.

**For Aspose:**
```bash
python scripts/run_kra_from_config.py \
  --config content/Aspose/kra_run.yaml
```

**For GroupDocs:**
```bash
python scripts/run_kra_from_config.py \
  --config content/GroupDocs/kra_run.yaml
```

**For Conholdate:**
```bash
python scripts/run_kra_from_config.py \
  --config content/Conholdate/kra_run.yaml
```

**For Familiarize:**
```bash
python scripts/run_kra_from_config.py \
  --config content/Familiarize/kra_run.yaml
```

### Option 2: Direct CLI Run

For quick tests or custom parameters, you can run the analyzer directly:

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

**CLI Parameters:**

| Flag | Description |
|------|-------------|
| `--file` | Path to keyword file |
| `--brand` | Brand name |
| `--product` | Product name |
| `--locale` | Language/region code |
| `--top` | Number of top clusters to analyze |
| `--max-rows` | Maximum keywords to process |
| `--platform` | Target platform |

### What Happens During a Run

1. **Loading**: The system reads your keyword file and validates the data
2. **Clustering**: Keywords are grouped by semantic similarity (typically takes 10-30 seconds)
3. **Content Scanning**: If enabled, existing blog posts are indexed (30-60 seconds)
4. **AI Analysis**: The LLM evaluates clusters and generates topics (1-3 minutes)
5. **Output Generation**: Results are saved in multiple formats

**Expected runtime**: 2-5 minutes for typical datasets (1,000-10,000 keywords)

---

## Understanding Your Results

Each run produces three output files in the configured output directory:

### 1. Full Result JSON

**Filename:** `kra_result_<brand>_<run_id>.json`

**Purpose:** Complete structured data for programmatic access

**Contains:**
- All identified keyword clusters
- Opportunity scores for each cluster
- Generated topic ideas with metadata
- Processing timestamps and configuration

**Use this for:**
- Integration with other systems
- Detailed analysis
- Archival purposes

### 2. Topics Markdown

**Filename:** `kra_result_<brand>_<run_id>_topics.md`

**Purpose:** Human-readable topic recommendations for content writers

**Format Example:**

```markdown
# Blog Topics for Aspose.Cells (Python)

## Cluster 1: Excel to PDF Conversion
**Opportunity Score:** 8.5/10
**Search Volume:** 12,400/month
**Keywords:** convert excel to pdf python, xlsx to pdf, excel converter

### Recommended Topics:

1. **How to Convert Excel to PDF in Python: Complete Guide**
   - Target: "convert excel to pdf python" (1,200 searches/mo)
   - Angle: Step-by-step tutorial with Aspose.Cells
   - Priority: High

2. **5 Ways to Automate Excel to PDF Conversion**
   - Target: "automate excel pdf" (890 searches/mo)
   - Angle: Batch processing and scripting examples
   - Priority: Medium
```

**Use this for:**
- Content planning meetings
- Assigning topics to writers
- Editorial calendar creation

### 3. Metrics Database JSON

**Filename:** `kra_metrics_db.json` (configurable via `KRA_METRICS_DB_PATH`)

**Purpose:** Track performance across multiple runs

**Contains per run:**
- Run ID and timestamp
- Brand, product, platform parameters
- Number of clusters and topics generated
- LLM token usage (prompt + completion)
- Wall-clock execution time
- Input file details

**Use this for:**
- Cost tracking (token usage)
- Performance monitoring
- Comparing runs over time

---

## GitHub Actions Automation

The analyzer can run automatically whenever you update keyword data or configuration files.

### How It Works

1. **You commit changes** to any of these:
   - `content/**` (keyword files or configs)
   - `scripts/run_kra_from_config.py`
   - `.github/workflows/kra.yml`

2. **GitHub detects changes** and determines which brands were affected

3. **Brand-specific jobs run** (only for brands with changes):
   - Aspose job runs if Aspose data changed
   - GroupDocs job runs if GroupDocs data changed
   - (and so on)

4. **Results are saved**:
   - Uploaded as downloadable artifacts
   - Committed back to the repository under `content/kra_results/`

### Viewing Results in GitHub

1. Go to your repository on GitHub
2. Click **Actions** tab
3. Find the latest workflow run
4. Click on the specific brand job (e.g., "kra-aspose")
5. Download artifacts from the **Artifacts** section

### Manual Trigger

You can also trigger the workflow manually:

1. Go to **Actions** tab
2. Select **KRA Workflow**
3. Click **Run workflow**
4. Choose the branch
5. Click **Run workflow** button

### Workflow Configuration

The automation is controlled by `.github/workflows/kra.yml`. Key features:

- **Selective execution**: Only runs for brands with changed data
- **Blog content access**: Automatically clones blog repositories for duplicate checking
- **Secure credentials**: Uses GitHub secrets for private repository access
- **Artifact retention**: Stores results for 30 days by default

---

## Adding a New Brand

Need to analyze keywords for a new brand? Follow these steps:

### 1. Create Brand Directory

```bash
mkdir content/NewBrand
```

### 2. Add Keyword File

Place your `keywords.csv` in:
```
content/NewBrand/keywords.csv
```

### 3. Create Configuration File

Copy an existing `kra_run.yaml` and modify for your brand:

```yaml
engine:
  input_file: "content/NewBrand/keywords.csv"
  brand: "NewBrand"
  product: "NewBrand.ProductName"
  platform: "python"
  locale: "en-US"
  top_clusters: 10
  max_rows: 50000
  use_content_index: true

content_index:
  local_root: "C:\\GitHub\\newbrand-blog\\content"
  repo_url: "https://github.com/NewBrand/blog"
  branch: "main"
  subdir: "/content"
```

### 4. Test Locally

```bash
python scripts/run_kra_from_config.py \
  --config content/NewBrand/kra_run.yaml
```

### 5. Add GitHub Automation

Edit `.github/workflows/kra.yml` and add:

**In the `detect-changes` job**, add output:
```yaml
outputs:
  newbrand_changed: ${{ steps.changes.outputs.newbrand }}
```

**In the `changes` step**, add filter:
```yaml
newbrand:
  - 'content/NewBrand/**'
```

**Add a new job**:
```yaml
kra-newbrand:
  needs: detect-changes
  if: needs.detect-changes.outputs.newbrand_changed == 'true'
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    
    - name: Checkout NewBrand Blog
      uses: actions/checkout@v4
      with:
        repository: NewBrand/blog
        token: ${{ secrets.PERSONAL_ACCESS_TOKEN }}
        path: blog_content
    
    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    
    - name: Run KRA for NewBrand
      env:
        OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        BLOG_CONTENT_ROOT: blog_content/content
      run: |
        python scripts/run_kra_from_config.py \
          --config content/NewBrand/kra_run.yaml
    
    - name: Upload results
      uses: actions/upload-artifact@v4
      with:
        name: kra-results-newbrand
        path: content/kra_results/kra_result_newbrand_*.json
```

### 6. Commit and Push

```bash
git add content/NewBrand/
git add .github/workflows/kra.yml
git commit -m "Add NewBrand to keyword analyzer"
git push
```

---

## Troubleshooting

### Common Issues

#### "API key not found"

**Problem:** The system cannot find your LLM API credentials.

**Solution:**
1. Check that your `.env` file exists in the `env/` directory
2. Verify the key name matches: `CUSTOM_LLM_API_KEY`
3. Ensure there are no extra spaces or quotes around the key value
4. Try setting the environment variable directly:
   ```bash
   export OPENAI_API_KEY=your-key-here
   ```

#### "File not found" errors

**Problem:** The system cannot locate your keyword file or configuration.

**Solution:**
1. Verify the file path in `kra_run.yaml` is correct
2. Check that the file exists at the specified location
3. Use absolute paths if relative paths cause issues
4. On Windows, use double backslashes: `C:\\GitHub\\...`

#### "No clusters generated"

**Problem:** The analyzer completes but produces no keyword clusters.

**Solution:**
1. Check that your keyword file has data (not just headers)
2. Verify the CSV format is correct (comma-separated, proper encoding)
3. Increase `max_rows` if your dataset is very large
4. Check for encoding issues (save as UTF-8)

#### Content index not working

**Problem:** Existing blog posts are not being detected for duplicate checking.

**Solution:**

**For local development:**
1. Verify `local_root` points to the correct directory
2. Check that blog posts have the expected structure (`index.md` with front matter)
3. Ensure the path exists and is accessible

**For GitHub Actions:**
1. Verify the blog repository URL is correct
2. Check that the PAT (Personal Access Token) secret is configured
3. Confirm the `subdir` path matches the repository structure

#### Workflow not triggering

**Problem:** GitHub Actions workflow doesn't run after pushing changes.

**Solution:**
1. Ensure changes are in the monitored paths:
   - `content/**`
   - `scripts/run_kra_from_config.py`
   - `.github/workflows/kra.yml`
2. Check the Actions tab for error messages
3. Verify the workflow file syntax is valid (use a YAML validator)
4. Ensure you're pushing to the correct branch (usually `main`)

#### Out of memory errors

**Problem:** The analyzer crashes when processing large datasets.

**Solution:**
1. Reduce `max_rows` in your configuration (try 10,000-20,000)
2. Process keywords in batches
3. Increase available system memory
4. Close other applications during processing

#### Slow performance

**Problem:** Analysis takes much longer than expected.

**Solution:**
1. Disable content index if not needed: `use_content_index: false`
2. Reduce `top_clusters` to process fewer clusters
3. Use `max_rows` to limit keyword count
4. Check your network connection (affects LLM API calls)

### Getting Help

If you encounter issues not covered here:

1. **Check the logs**: Run with verbose output to see detailed error messages
2. **Review configuration**: Ensure all paths and parameters are correct
3. **Test with sample data**: Try running with a small test dataset first
4. **Consult metrics**: Check `kra_metrics_db.json` for hints about what went wrong

---

## Best Practices

### Data Preparation
- Clean your keyword data before analysis (remove duplicates, fix encoding)
- Start with smaller datasets (1,000-5,000 keywords) to test configuration
- Use descriptive file names with dates (e.g., `keywords_2024_Q1.csv`)

### Configuration
- Document any custom settings in comments within `kra_run.yaml`
- Keep separate configs for different products/platforms
- Version control all configuration changes

### Content Planning
- Review generated topics with your editorial team before publication
- Prioritize high-opportunity clusters first
- Use the markdown output for content briefs and writer assignments

### Automation
- Test locally before relying on GitHub Actions
- Monitor token usage via metrics database to control costs
- Schedule regular keyword updates (monthly or quarterly)

### Maintenance
- Archive old keyword files after processing
- Review and update brand configurations as products evolve
- Clean up old result files periodically to save space

---

## Appendix: File Structure

```
Keyword-Analyzer-Demo/
├── .github/
│   └── workflows/
│       └── kra.yml                    # GitHub Actions workflow
├── content/
│   ├── keywords_data/
│   │   ├── Aspose/
│   │   │   ├── keywords.csv           # Keyword input
│   │   │   └── kra_run.yaml           # Brand configuration
│   │   ├── GroupDocs/
│   │   ├── Conholdate/
│   │   └── Familiarize/
│   └── kra_results/                   # Committed results
│       ├── kra_result_aspose_*.json
│       └── kra_metrics_db.json
├── scripts/
│   └── run_kra_from_config.py         # Config-based runner
├── src/
│   ├── agent_engine/
│   │   └── kra/
│   │       ├── runner.py              # Main CLI entrypoint
│   │       ├── config.py              # Configuration loader
│   │       ├── schemas.py             # Data models
│   │       └── tools/
│   │       	├── cluster.py       	# Vectorize + clustering
│   │           ├── content_index.py   	# Existing content detection
│   │           ├── directory_search.py
│	│			├── file_import.py   	# Robust CSV/XLSX reader + header aliasing + number cleaning
│   │           ├── index_search.py   	# Existing content detection
│   │           ├── index_builder.py   	# Existing content detection
│	│			├── intent_brand.py  	# Heuristics/LLM for search intent + brand-fit
│	│			├── metrics.py  	 	# Metrics
│	│			├── preprocess.py    	# Text cleanups, dedupe
│	│			├── scoring.py       	# Cluster scoring (weights + normalization)
│   │
│   ├── apps/
│   │   └── brands.json          		# Source data for brands and products
│   │   └── api/
│   │       ├── main.py            		# FastAPI app + single-page UI
│   │   └── images/
│   │       ├── favicon.ico
│   ├── data/
│   │   └── outputs/                   	# Local run outputs
├── requirements.txt                   	# Python dependencies
└── README.md
├── .env                           # API keys and environment config
├── pyproject.toml

```

---

## Quick Reference Commands

```bash
# Setup
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt

# Run for specific brand (config-based)
python scripts/run_kra_from_config.py --config content/Aspose/kra_run.yaml

# Run with CLI (Aspose example)
python -m src.agent_engine.kra.runner \
  --file content/Aspose/keywords.csv \
  --brand Aspose \
  --product "Aspose.Cells" \
  --platform python \
  --top 10

# View metrics
cat src/data/kra_metrics_db.json

# View results
cat content/lra_results/kra_result_aspose_<run_id>_topics.md
```

---

**Version:** 1.0  
**Last Updated:** December 8, 2024  

For technical support or feature requests, please contact your development team or submit an issue in the project repository.