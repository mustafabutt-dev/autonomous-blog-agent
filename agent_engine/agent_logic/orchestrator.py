"""
Orchestrator with OpenAI Agents SDK + Runner
Agent autonomously decides tool sequence
"""
from openai import AsyncOpenAI
from agents import Agent, Runner, OpenAIChatCompletionsModel, set_tracing_disabled, ModelSettings
from config import settings
from tools.mcp_tools import fetch_keywords_auto, fetch_keywords_manual, generate_markdown_file, fetch_category_related_articles, generate_seo_title, generate_blog_outline
from utils import prompts
from utils.helpers import sanitize_markdown_title
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
        brand_file_map = {
            "aspose.com": "aspose.com.json",
            "groupdocs.com": "groupdocs.com.json",
            "conholdate.com": "conholdate.com.json"
        }
   
        filename = brand_file_map.get(self.brand)
        if not filename:
            raise ValueError(f"Invalid brand '{self.brand}'. Must be: aspose.com, groupdocs.com, conholdate.com")

        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        products_path = os.path.join(base_dir, "..", "data", filename)

        if not os.path.exists(products_path):
            raise FileNotFoundError(f"Products file not found: {products_path}")

        with open(products_path, "r") as f:
            return json.load(f)

    async def create_blog_autonomously(self, topic: str, product_name: str = None, platform: str = "", keyword_source: str=""):
        """Let the agent autonomously create a blog"""
        set_tracing_disabled(disabled=True)
   
        context = ""
        base_name = product_name.strip()
        platform_clean = platform.strip()

        # Build expected product name EXACTLY as in your data
        expected_name = f"{base_name} for {platform_clean}"

        # Case-insensitive matching
        product_info = next(
            (p for p in self.products
            if p["ProductName"].lower() == expected_name.lower()),
            None
        )

        if not product_info:
            raise ValueError(
                f"No product found for '{product_name}' with platform '{platform}'"
            )

        # Prepare context
        for k, v in product_info.items():
            context += f"\n{k}: {v}"
            
        product_name = product_info.get("ProductName")
        print(f"product is -- {product_name}")
        print(f" Connecting to MCP server fetch_keywords...{keyword_source}")
        related_links = await fetch_category_related_articles(topic, product_name, product_info.get('BlogsURL'),3)
        # related_links = format_related_posts(related_links)
        if keyword_source == "manual":
            
            res_keywords = await fetch_keywords_manual( product_name=product_name, brand=self.brand)
            primary = res_keywords.get("keywords", {}).get("primary", [])
            secondary = res_keywords.get("keywords", {}).get("secondary", [])
            f_keywords = primary + secondary
            blog_outline = res_keywords.get("outline")
            res_title = sanitize_markdown_title(res_keywords.get("topic")) 
            
        elif keyword_source == "auto":
          
            res_keywords = await fetch_keywords_auto(topic=topic, product_name=product_name)
        
            keywords_data = json.loads(res_keywords)
            f_keywords = keywords_data.get('keywords', {}).get('primary', [topic])
            res_title = await generate_seo_title(topic=topic, keywords_json=res_keywords, product_name=product_name)
            
            res_title = sanitize_markdown_title(res_title)
            print(f"title izz -- {res_title}")
            blog_outline = await generate_blog_outline(res_title, f_keywords)
      

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
