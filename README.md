
# Blog Agent Backend

Autonomous blog creation engine using OpenAI Agents SDK and MCP servers.

## Features

- ✅ Keyword research via MCP
- ✅ Title via MCP
- ✅ Aspose LLM integration
- ✅ Autonomous agent capabilities

## Quick Start

### 1. Setup

```bash
# Clone the repository
git clone <repo-url>
cd blog-agent-backend

# Run setup script
chmod +x setup.sh
./setup.sh
```

### 2. Configure

Edit `agent_engine/.env`:

```env
ASPOSE_LLM_BASE_URL=http://your-llm-server.com/v1
ASPOSE_LLM_API_KEY=your-api-key
```
Put your OPENAI_API_KEY in `mcp-servers/keywords/.env`:

### 3. Run

```bash
python3 main.py --topic "Convert AI to JPEG" --product "Aspose.PSD for Java" --platform Aspose"
```

## Project Structure

```
blog-agent-backend/
├── agent_engine/
│   ├── main.py                 # Main file
│   ├── config.py               # Configuration
│   ├── agent_logic/
│   │   └── orchestrator.py     # Main orchestration layer
│   ├── services/
│   │   └── serpapi_keyword_service.py  # External service to fetch keywords from Google SERP       
│   ├── tools/
│   │   └── mcp_tools.py        # Wrapper functions for MCP tools
│   ├── utils/
│   │   └── helpers.py          # Contains helper functions
│   │   └── prompts.py          # Returns prompts for LLM
│   ├── requirements.txt
│   └── .env
│
├── mcp-servers/
│   ├── file-generator/   
│   │   └── server.py           
│   └── requirements.txt
│   ├── keywords_auto/          # Keyword research tool using SERPAPI
│   │   └── server.py           # MD file generation tools
│   ├── keywords_manual/.       # Keyword research tool using Keyword.csv file
│   │   └── server.py  
│   ├── outline_generator/      # Generates blog post outline
│   │   └── server.py  
│   ├── related-topics/         # Fetch relevant articles from the relevant category  
│   │   └── server.py  
│   ├── title_generator/        # Generates SEO-optimized title for blog post 
│   │   └── server.py  
│   └── requirements.txt
│── data/
│   │   └── aspose.json          # Contains source products data for aspose
│   │   └── groupdocs.json       # Contains source products data for groupdocs
│   │   └── conholdate.json      # Contains source products data for conholdate
│── output/
│   │   └── blogs               # Contains generated MD files of blog post
└── setup.sh                    # Initial setup

```

## Deployment

### Using Docker (Coming Soon)
```bash
docker-compose up
```

### Manual Deployment

**Agent Engine:** Deploy to Railway/Render/Heroku
**MCP Servers:** Deploy as separate services

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ASPOSE_LLM_BASE_URL` | Your LLM API endpoint | - |
| `ASPOSE_LLM_API_KEY` | Your LLM API key | - |
| `KEYWORD_SEARCH_URL` | Keyword MCP server URL | `http://localhost:3001` |
| `SEO_TOOL` | FAQ MCP server URL | `http://localhost:3002` |

## Troubleshooting

**Port already in use:**
```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9
```

**Virtual environment issues:**
```bash
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r agent_engine/requirements.txt
```


