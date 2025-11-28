"""
Orchestrator with OpenAI Agents SDK + Runner
Agent autonomously decides tool sequence
"""
from openai import AsyncOpenAI
from agents import Agent, Runner, OpenAIChatCompletionsModel, set_tracing_disabled, ModelSettings
from config import settings
from tools.mcp_tools import fetch_keywords_auto, fetch_keywords_manual, generate_markdown_file, fetch_category_related_articles, generate_seo_title, generate_blog_outline
from utils import prompts
from utils.helpers import sanitize_markdown_title, prepare_context, get_productInfo
import json
import os

class BlogOrchestrator: 
    def __init__(self, brand="aspose.com"):
        """
        brand can be: aspose, groupdocs, conholdate
        """
        self.brand = brand.lower().strip()

        self.client = AsyncOpenAI(
            base_url=settings.ASPOSE_LLM_BASE_URL,
            api_key=settings.ASPOSE_LLM_API_KEY
        )
        self.model = OpenAIChatCompletionsModel(
            model=settings.ASPOSE_LLM_MODEL,
            openai_client=self.client
        )

        self.products = self.load_products()

    def load_products(self):
        """Load products from correct JSON based on brand name"""
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_dir = os.path.join(base_dir, "..", "data")
        
        # Check if data directory exists
        if not os.path.exists(data_dir):
            raise FileNotFoundError(f"Data directory not found: {data_dir}")
        
        # Construct expected filename from brand name
        filename = f"{self.brand}.json"
        products_path = os.path.join(data_dir, filename)
        
        # Check if the specific brand file exists
        if not os.path.exists(products_path):
            # List available brands for helpful error message
            available_files = [f for f in os.listdir(data_dir) if f.endswith('.json')]
            available_brands = [f.replace('.json', '') for f in available_files]
            raise FileNotFoundError(
                f"Products file not found for brand '{self.brand}'. "
                f"Available brands: {', '.join(available_brands)}"
            )
        
        with open(products_path, "r") as f:
            return json.load(f)

    async def create_blog_autonomously(self, topic: str, product_name: str = None, platform: str = "", keyword_source: str=""):
        """Let the agent autonomously create a blog"""
        set_tracing_disabled(disabled=True)
      
        product_info = get_productInfo(product_name, platform, self.products)
        context = prepare_context(product_info)
        product_name = product_info.get("ProductName")
        print("Connecting to fetch_category_related_articles MCP server")
        related_links = await fetch_category_related_articles(topic, product_name, product_info.get('BlogsURL'),3)
        print(f" Connecting to keywords MCP server - {keyword_source}")
        if keyword_source == "manual (using Google Keyword Planner Sheet)":
            
            res_keywords = await fetch_keywords_manual( product_name=product_name, brand=self.brand)
            primary = res_keywords.get("keywords", {}).get("primary", [])
            secondary = res_keywords.get("keywords", {}).get("secondary", [])
            f_keywords = primary + secondary
            blog_outline = res_keywords.get("outline")
            res_title = sanitize_markdown_title(res_keywords.get("topic")) 
            
        elif keyword_source == "auto (using SerpApi)":
          
            f_keywords = await fetch_keywords_auto(topic=topic, product_name=product_name)
            print("Connecting to SEO-Title MCP server")
            res_title = await generate_seo_title(topic=topic, keywords_json=f_keywords, product_name=product_name)
            res_title = sanitize_markdown_title(res_title)
            print("Connecting to generate_blog_outline MCP server")
            blog_outline = await generate_blog_outline(res_title, f_keywords)
      
        print("Generating content now")
        agent = Agent(
            name="blog-writer-agent",
            instructions=prompts.get_blog_writer_prompt(
                res_title,
                f_keywords,
                blog_outline,
                related_links,
                context
            ),
            model=self.model,
            model_settings=ModelSettings(temperature=0.6)
        )

        try:
            result = await Runner.run(agent, context, max_turns=10)

            final_content = (
                "\n\n".join(result.final_output)
                if isinstance(result.final_output, list)
                else str(result.final_output)
            )
            print("Generating markdown file")
            file_res = await generate_markdown_file(
                title=res_title,
                content=final_content,
            )
            filepath = file_res.get("output", {}).get("filepath")

        except Exception as e:
            import traceback
            print("Runner.run failed:", e, flush=True)
            traceback.print_exc()
            return {"status": "error", "message": str(e)}

        return {
            "agent_output": result.final_output,
            "filepath": filepath,
            "product": product_name,
            "brand": self.brand,
            "status": "success"
        }
