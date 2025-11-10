#!/bin/bash

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
REQUIRED_VERSION="3.10"

if [[ "$PYTHON_VERSION" < "$REQUIRED_VERSION" ]]; then
    echo "Python 3.10 or higher is required. Please install it first."
    exit 1
fi

export PYTHONDONTWRITEBYTECODE=1

echo "🔧 Setting up Blog Agent Backend..."

# Install uv if needed
if ! command -v uv &> /dev/null; then
    echo "📦 Installing uv..."
    pip3 install uv --user
fi

# Create virtual environment
echo "📦 Creating virtual environment..."
python3.10 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install agent engine dependencies
echo "📦 Installing Agent Engine dependencies..."
cd agent_engine
pip install -r requirements.txt
cd ..

# Install MCP server dependencies using uv
echo "📦 Installing MCP Server dependencies with uv..."
cd mcp-servers
pip install -r requirements.txt
cd ..
echo "✅ Setup complete!"
source venv/bin/activate  
cd agent_engine
