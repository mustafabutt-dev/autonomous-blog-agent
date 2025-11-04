# Blog Agent - Autonomous Blog Creation with MCP Servers

AI-powered autonomous blog creation system using OpenAI Agents SDK, MCP servers, and dynamic keyword research.

## Features

* 🤖 Autonomous agent workflow with OpenAI Agents SDK
* 🔍 Dynamic keyword research via SerpAPI & Google Search Console
* 📝 SEO-optimized title generation
* 📄 Automated markdown blog generation
* 🔌 Modular MCP server architecture (plug & play)

## Prerequisites

* Python 3.10+
* SerpAPI key (free tier: 100 searches/month)
* Aspose LLM or OpenAI-compatible LLM

## Quick Start

### 1. Clone & Setup

```bash
git clone <repo-url>
cd blog-agent-backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
cd agent-engine && pip install -r requirements.txt
cd ../mcp-servers && uv pip install fastmcp --system
```

### 3. Configure Environment

```bash
# Copy and edit .env in agent-engine/
cp agent-engine/.env.example agent-engine/.env

# Add your keys:
# - ASPOSE_LLM_BASE_URL
# - ASPOSE_LLM_API_KEY
# - SERPAPI_API_KEY
```

### 4. Add Product Data

```bash
# Place your products.json in data/
mkdir -p data
# Copy your products JSON to data/products.json
```

### 5. Run

```bash
# Terminal 1 - Agent Engine
cd agent-engine
uvicorn main:app --port 8000

# Access: http://localhost:8000/docs
```

## Project Structure

```
blog-agent-backend/
├── agent-engine/          # FastAPI orchestrator
│   ├── agent_logic/       # Agent with OpenAI SDK
│   ├── services/          # Keyword research services (modular)
│   └── tools/             # MCP tool definitions
├── mcp-servers/           # MCP servers (stdio)
│   ├── keywords/          # Keyword research
│   ├── seo/              # SEO title generation
│   └── file-generator/   # Markdown file creation
├── data/                 # products.json
└── output/blogs/         # Generated markdown files
```

## API Usage

```bash
# Create blog post
curl -X POST http://localhost:8000/api/create-blog \
  -H "Content-Type: application/json" \
  -d '{"topic": "Convert Word to PDF", "product_name": "Aspose.Words for .NET"}'
```

## Adding New Keyword Services

1. Create service in `agent-engine/services/`
2. Extend `BaseKeywordService`
3. Add to `KeywordAggregator` - auto-detected if configured

## Tech Stack

* OpenAI Agents SDK (autonomous orchestration)
* FastMCP (MCP server implementation)
* FastAPI (API layer)
* SerpAPI (keyword research)
* Pydantic (configuration)