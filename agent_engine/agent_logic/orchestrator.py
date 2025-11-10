"""
Orchestrator with OpenAI Agents SDK + Runner
Agent autonomously decides tool sequence
"""
from openai import OpenAI
from agents import Agent, Runner
from config import settings
from tools.mcp_tools import fetch_keywords, generate_seo_title, generate_markdown_file
from utils import prompts
import json

class BlogOrchestrator:
    def __init__(self):
        self.client = OpenAI(
            base_url=settings.ASPOSE_LLM_BASE_URL,
            api_key=settings.ASPOSE_LLM_API_KEY
        )
        self.products = self.load_products()
    
    def load_products(self):
        """Load products from JSON"""
        import os
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        products_path = os.path.join(base_dir, '..', 'data', 'products.json')
        
        with open(products_path, 'r') as f:
            return json.load(f)
    
    async def create_blog_autonomously(self, topic: str, product_name: str = None):
        """Let the agent autonomously create a blog"""

        # Find product info
        product_info = None
        if product_name:
            product_info = next(
                (p for p in self.products if p['ProductName'] == product_name),
                None
            )
            if not product_info:
                raise ValueError(f"No product found with name '{product_name}'")
        
        # Prepare context for agent
        context = f"Create a comprehensive blog post about: {topic}"
        if product_name:
            context += f"\nProduct: {product_name}"
            if product_info:
                context += f"\nDocumentation: {product_info.get('DocumentationURL', '')}"
                context += f"\nAPI Reference: {product_info.get('APIReferenceURL', '')}"
                context += f"\nCategory: {product_info.get('Category', '')}"
                context += f"\nProductURL: {product_info.get('ProductURL', '')}"
                context += f"\nDownloadURL: {product_info.get('DownloadURL', '')}"
                context += f"\nExternalDownloadURL: {product_info.get('ExternalDownloadURL', '')}"
                context += f"\nForumsURL: {product_info.get('ForumsURL', '')}"
                context += f"\nInstallCommand: {product_info.get('InstallCommand', '')}"
                context += f"\nurlPrefix: {product_info.get('urlPrefix', '')}"
                context += f"\nlicense: {product_info.get('license', '')}"
        
        print(f" Connecting to MCP server fetch_keywords...")
      
        res_keywords = await fetch_keywords(topic=topic, product_name=product_name)
        keywords_data = json.loads(res_keywords)
        f_keywords = keywords_data.get('keywords', {}).get('primary', [topic])
       
        res_title = await generate_seo_title(topic=topic, keywords_json=res_keywords, product_name=product_name)

        agent = Agent(
            name="blog-writer-agent",
            instructions=prompts.get_blog_writer_prompt(res_title,f_keywords,context),     
            model=settings.ASPOSE_LLM_MODEL,   
        )
    
        try:
            result = await Runner.run(agent, context, max_turns=10 )
            final_content = (
                "\n\n".join(result.final_output)
                if isinstance(result.final_output, list)
                else str(result.final_output)
            )

            file_res = await generate_markdown_file(title=res_title, content=final_content, keywords_json=f_keywords)  
            filepath = file_res.get('output', {}).get('filepath')
        except Exception as e:
            import traceback
            print("Runner.run failed:", e, flush=True)
            traceback.print_exc()
            return {"status": "error", "message": str(e)}
        
        print("Runner.run done.")

        
        return {
            "agent_output": result.final_output,
            "filepath" : filepath,
            "product": product_name,
            "status": "success"
        }
