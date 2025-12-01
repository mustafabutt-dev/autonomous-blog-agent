
# Blog Agent Backend

Blog post creation engine using OpenAI Agents SDK and MCP servers.

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

Update `agent_engine/.env`:

### 3. Run


```bash
python3 main.py --topic "Create a Pie Chart" --product "Aspose.Slides" --platform "Java" --brand "aspose.com"  --keyword_source "auto (using SerpApi)" --author "Muhammad Mustafa"   
```

or

For Google Keyword Planner Sheet
```bash
python3 main.py --topic "Convert PPTX to PDF" --product "Aspose.Slides" --platform "Java" --brand "aspose.com"  --keyword_source "manual (using Google Keyword Planner Sheet)" --author "Muhammad Mustafa"
```

**The following brands are currently supported:**

- aspose.com
- groupdocs.com
- conholdate.cloud
- conholdate.com

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

