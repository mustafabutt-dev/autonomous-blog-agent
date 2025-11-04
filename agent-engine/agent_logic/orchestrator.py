"""
Orchestrator with OpenAI Agents SDK + Runner
Agent autonomously decides tool sequence
"""
from openai import OpenAI
from agents import Agent, Runner, ModelSettings
from config import settings
from tools.mcp_tools import fetch_keywords, generate_seo_title, generate_markdown_file
import json

class BlogOrchestrator:
    def __init__(self):
        self.client = OpenAI(
            base_url=settings.ASPOSE_LLM_BASE_URL,
            api_key=settings.ASPOSE_LLM_API_KEY
        )
        self.products = self.load_products()
        self.agent = self.create_agent()
    
    def load_products(self):
        """Load products from JSON"""
        import os
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        products_path = os.path.join(base_dir, '..', 'data', 'products.json')
        
        with open(products_path, 'r') as f:
            return json.load(f)
    
    def create_agent(self):
        """
        Create the autonomous blog writing agent
        Agent decides which tools to use and when
        """
        
        agent = Agent(
            name="blog-writer-agent",
            instructions="""You are an expert blog writer agent. Your job is to create SEO-optimized technical blog posts.

FOLLOW THIS EXACT WORKFLOW:

1. First, call the fetch_keywords tool with the topic to get high-ranking keywords
2. Then, call the generate_seo_title tool with the topic and the keywords you received to create an optimized title
3. Write comprehensive blog content yourself:
   - Introduction (2-3 paragraphs)
   - Main Content (3-4 sections with explanations and examples)
   - Conclusion (1-2 paragraphs)
   Make it informative, SEO-friendly, and practical.
4. CRITICALLY IMPORTANT: You MUST call the generate_markdown_file tool at the end with:
   - The title you generated
   - The blog content you wrote
   - The keywords as JSON string

Do not skip step 4! The blog must be saved to a file. If you finish without saving the file, you have FAILED your task.""",
            
            tools=[
                fetch_keywords,
                generate_seo_title,
                generate_markdown_file
            ],
            
            model=settings.ASPOSE_LLM_MODEL,
            model_settings=ModelSettings(
                tool_choice="required"  # Force tool usage
            )
        )
        
        return agent
    
    async def create_blog_autonomously(self, topic: str, product_name: str = None):
        """Let the agent autonomously create a blog"""
        
        # Find product info
        product_info = None
        if product_name:
            product_info = next(
                (p for p in self.products if p['ProductName'] == product_name),
                None
            )
        
        # Prepare context for agent
        context = f"Create a comprehensive blog post about: {topic}"
        if product_name:
            context += f"\nProduct: {product_name}"
            if product_info:
                context += f"\nDocumentation: {product_info.get('DocumentationURL', '')}"
                context += f"\nAPI Reference: {product_info.get('APIReferenceURL', '')}"
                context += f"\Category: {product_info.get('Category', '')}"
                context += f"\nProductURL: {product_info.get('ProductURL', '')}"
                context += f"\DownloadURL: {product_info.get('DownloadURL', '')}"
                context += f"\nExternalDownloadURL: {product_info.get('ExternalDownloadURL', '')}"
                context += f"\nForumsURL: {product_info.get('ForumsURL', '')}"
                context += f"\nInstallCommand: {product_info.get('InstallCommand', '')}"
                context += f"\nurlPrefix: {product_info.get('urlPrefix', '')}"
                context += f"\nlicense: {product_info.get('license', '')}"
        
        print(f" Running agent with context: {context}")
        
        # Run the agent
        result = await Runner.run(self.agent, context, max_turns=20 )
        
        print(f" Agent finished!")
        print(f" Final output: {result.final_output}")
        
        return {
            "agent_output": result.final_output,
            "product": product_name,
            "status": "success"
        }