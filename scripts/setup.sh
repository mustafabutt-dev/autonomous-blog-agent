#!/bin/bash

echo "🔧 Setting up Blog Agent Backend..."

# Install uv if needed
if ! command -v uv &> /dev/null; then
    echo "📦 Installing uv..."
    pip3 install uv --user
fi

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install agent engine dependencies
echo "📦 Installing Agent Engine dependencies..."
cd agent-engine
pip install -r requirements.txt
cd ..

# Install MCP server dependencies using uv
echo "📦 Installing MCP Server dependencies with uv..."
uv pip install fastmcp pydantic python-dotenv httpx

# Create __init__.py files
touch agent-engine/agents/__init__.py
touch agent-engine/mcp_client/__init__.py
touch agent-engine/routes/__init__.py

# Copy env file
if [ ! -f "agent-engine/.env" ]; then
    cp agent-engine/.env.example agent-engine/.env
    echo "✅ Created .env file"
fi

echo "✅ Setup complete!"