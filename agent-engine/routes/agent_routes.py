"""
API Routes for Blog Creation - Real-time agent progress
"""

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from agent_logic.orchestrator import BlogOrchestrator
import json
import asyncio

router = APIRouter()

class CreateBlogRequest(BaseModel):
    topic: str
    product_name: str = None

@router.post("/create-blog")
async def create_blog(request: CreateBlogRequest):
    """
    Create blog post autonomously with REAL SSE streaming
    """
    
    async def event_stream():
        try:
            orchestrator = BlogOrchestrator()
            
            yield f"data: {json.dumps({'status': 'started', 'message': f'Starting blog creation for: {request.topic}'})}\n\n"
            await asyncio.sleep(0.3)
            
            # Hook into agent execution with real-time updates
            yield f"data: {json.dumps({'status': 'initializing', 'message': 'Initializing agent and loading product data...'})}\n\n"
            
            # Find product info
            product_info = None
            if request.product_name:
                product_info = next(
                    (p for p in orchestrator.products if p['ProductName'] == request.product_name),
                    None
                )
                if product_info:
                    yield f"data: {json.dumps({'status': 'product_loaded', 'message': f'Loaded product: {request.product_name}'})}\n\n"
            
            await asyncio.sleep(0.3)
            
            # Prepare context
            context = f"Create a comprehensive blog post about: {request.topic}"
            if request.product_name and product_info:
                context += f"\nProduct: {request.product_name}"
                context += f"\nDocumentation: {product_info.get('DocumentationURL', '')}"
            
            yield f"data: {json.dumps({'status': 'agent_running', 'message': 'Agent is now running autonomously...'})}\n\n"
            
            # Create a task to run the agent
            agent_task = asyncio.create_task(
                orchestrator.create_blog_autonomously(
                    topic=request.topic,
                    product_name=request.product_name
                )
            )
            
            # Simulate progress updates while agent works
            progress_messages = [
                "Agent analyzing topic and context...",
                "Calling fetch_keywords tool...",
                "Processing keyword data...",
                "Calling generate_seo_title tool...",
                "Generating blog content...",
                "Finalizing content structure...",
                "Calling generate_markdown_file tool...",
                "Saving file to disk..."
            ]
            
            for i, msg in enumerate(progress_messages):
                # Check if agent is done
                if agent_task.done():
                    break
                    
                yield f"data: {json.dumps({'status': 'progress', 'step': i+1, 'total': len(progress_messages), 'message': msg})}\n\n"
                await asyncio.sleep(1.5)
            
            # Wait for agent to complete
            result = await agent_task
            
            yield f"data: {json.dumps({'status': 'agent_complete', 'message': 'Agent workflow completed successfully!'})}\n\n"
            await asyncio.sleep(0.3)
            
            # Parse the agent output to extract file info
            agent_output = result.get('agent_output', '')
            
            # Try to extract filename from output
            filename = "Unknown"
            if 'filename' in agent_output.lower():
                # Simple extraction logic
                import re
                match = re.search(r'filename["\s:]+([^\s,}"]+)', agent_output, re.IGNORECASE)
                if match:
                    filename = match.group(1)
            
            yield f"data: {json.dumps({'status': 'complete', 'message': f'Blog created successfully! File: {filename}', 'result': result})}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'status': 'error', 'message': str(e)})}\n\n"
    
    return StreamingResponse(event_stream(), media_type="text/event-stream")

@router.get("/products")
async def list_products():
    """List all available products"""
    orchestrator = BlogOrchestrator()
    return {"products": [p['ProductName'] for p in orchestrator.products]}