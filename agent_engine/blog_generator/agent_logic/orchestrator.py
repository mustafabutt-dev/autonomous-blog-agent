"""
Orchestrator with OpenAI Agents SDK + Runner + Metrics Tracking
"""
from openai import AsyncOpenAI
from agents import Agent, Runner, OpenAIChatCompletionsModel, set_tracing_disabled, ModelSettings
from config import settings
from tools.mcp_tools import generate_markdown_file, fetch_category_related_articles, gist_injector
from utils import prompts
from utils.helpers import sanitize_markdown_title, prepare_context, get_productInfo, get_topic_by_index
from utils.metricsRecorder import MetricsRecorder
import json
import os

class BlogOrchestrator: 
    def __init__(self, brand="aspose.com", agent_owner="Muhammad Mustafa", run_env=None):
        """
        Initialize Blog Orchestrator
        
        Args:
            brand: Brand name (aspose.com, groupdocs.com, conholdate.com)
            agent_owner: Name of the agent owner
            run_env: Environment - "DEV" or "PROD" (auto-detected if None)
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
        
        # Initialize metrics recorder with updated parameters
        self.metrics = MetricsRecorder(
            agent_name="Blog Post Generator",
            agent_owner=agent_owner,
            job_type="Blog Post Generation",
            run_env=run_env
        )
        
        print(f"🤖 Orchestrator initialized")
        print(f"   Run ID: {self.metrics.run_id}")
        print(f"   Environment: {self.metrics.run_env}")
        print(f"   Owner: {self.metrics.agent_owner}")

    def load_products(self):
        """Load products from correct JSON based on brand name"""
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_dir = os.path.join(base_dir, "../../", "content/productsData")
        
        if not os.path.exists(data_dir):
            raise FileNotFoundError(f"Data directory not found: {data_dir}")
        
        filename = f"{self.brand}.json"
        products_path = os.path.join(data_dir, filename)
        
        if not os.path.exists(products_path):
            available_files = [f for f in os.listdir(data_dir) if f.endswith('.json')]
            available_brands = [f.replace('.json', '') for f in available_files]
            raise FileNotFoundError(
                f"Products file not found for brand '{self.brand}'. "
                f"Available brands: {', '.join(available_brands)}"
            )
        
        with open(products_path, "r") as f:
            return json.load(f)

    async def create_blog_autonomously(
        self, 
        topics_file: str, 
        author: str = ""
    ):
        """Let the agent autonomously create a blog with metrics tracking"""
        set_tracing_disabled(disabled=True)
        topics_raw_data = get_topic_by_index(topics_file)
        post_topic = topics_raw_data.pop("topic")
        product_name = topics_raw_data.pop("product")
        platform = topics_raw_data.pop("platform")

        print(f"updateee --- {topics_raw_data}", flush=True)
        return
        # Get product info
        product_info = get_productInfo(product_name, platform, self.products)
        
        # Start metrics tracking
        self.metrics.start_job(
            product=product_name,
            platform=platform,
            website=self.brand
        )
        product_name = product_info.get("ProductName")
        try:
            context = prepare_context(product_info)
            
            print("📚 Connecting to fetch_category_related_articles MCP server")
            related_links = await fetch_category_related_articles(
                post_topic, 
                product_name, 
                product_info.get('BlogsURL'), 
                3
            )
    
            print(f"response keyword -- {topics_raw_data}", flush=True)
            primary = topics_raw_data.get("keywords", {}).get("primary", [])
            secondary = topics_raw_data.get("keywords", {}).get("secondary", [])
            f_keywords = primary + secondary
            blog_outline = topics_raw_data.get("outline")
            post_topic = sanitize_markdown_title(post_topic)
            
            print(" Generating content now")
            agent = Agent(
                name="blog-writer-agent",
                instructions=prompts.get_blog_writer_prompt(
                    post_topic,
                    f_keywords,
                    blog_outline,
                    related_links,
                    context,
                    author,
                    platform
                ),
                model=self.model,
                model_settings=ModelSettings(temperature=0.6)
            )

            result = await Runner.run(agent, context, max_turns=10)
            print(f" Injecting gists now -- {result.final_output}", flush=True)
            
            jistified = await gist_injector(result.final_output, post_topic)
            text_output = jistified.content[0].text
            data = json.loads(text_output)
            final_content = data["jistified_content"]

            print(f"💾 Generating markdown file")
            file_res = await generate_markdown_file(
                title=post_topic,
                content=final_content,
                brand= self.brand
            )
            filepath = file_res.get("output", {}).get("filepath")
            
            # Record success
            self.metrics.record_success(f"Blog post created: {filepath}")
            
            # End job and send metrics
            self.metrics.end_job()
            
            print(f"\n✅ Blog post generation completed!")
            print(f"📄 File: {filepath}")
            print(f"⏱️  Duration: {self.metrics.run_duration_ms}ms\n")
            
            # Print and send metrics
            self.metrics.print_summary()
            print("📊 Sending metrics to Google Script...")
            # metrics_sent_for_team = await self.metrics.send_metrics_to_team()
            # metrics_sent_for_pro = await self.metrics.send_metrics_to_prod()
            
            # if metrics_sent_for_team and metrics_sent_for_pro:
            #     print("Metrics sent successfully\n")
            # else:
            #     print("Failed to send metrics (check logs)\n")

            return {
                "agent_output": result.final_output,
                "filepath": filepath,
                "product": product_name,
                "brand": self.brand,
                "run_id": self.metrics.run_id,
                "duration_ms": self.metrics.run_duration_ms,
                "status": "success"
            }

        except Exception as e:
            import traceback
            print(f"\n Blog generation failed!", flush=True)
            print(f"Error: {e}", flush=True)
            traceback.print_exc()
            
            # Record failure
            self.metrics.record_failure(str(e))
            self.metrics.end_job()
            
            # Print and send metrics even on failure
            self.metrics.print_summary()
            print(" Sending failure metrics...")
            # await self.metrics.send_metrics_to_team()
            # await self.metrics.send_metrics_to_prod()
            
            return {
                "status": "error", 
                "message": str(e),
                "run_id": self.metrics.run_id
            }