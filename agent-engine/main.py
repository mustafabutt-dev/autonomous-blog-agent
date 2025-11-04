"""
FastAPI Agent Engine - Main Entry Point
Orchestrates blog creation using MCP servers
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.agent_routes import router as agent_router
from config import settings

app = FastAPI(
    title="Blog Agent Engine",
    description="Autonomous blog creation agent with MCP servers",
    version="1.0.0"
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_allowed_origins(),  # ← Changed this line
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(agent_router, prefix="/api")

@app.get("/")
async def root():
    return {
        "message": "Blog Agent Engine is running",
        "version": "1.0.0",
        "status": "healthy"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "mcp_servers": {
            "keyword_search": settings.KEYWORD_SEARCH_URL,
            "faq_generator": settings.FAQ_GENERATOR_URL
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )