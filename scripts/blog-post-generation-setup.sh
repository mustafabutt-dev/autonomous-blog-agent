#!/bin/bash

# ===============================================
# Blog Agent Backend Setup Script
# ===============================================

# Required Python version
REQUIRED_VERSION="3.11"

# Check current Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
if [[ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]]; then
    echo "❌ Python $REQUIRED_VERSION or higher is required. Current version: $PYTHON_VERSION"
    exit 1
fi

export PYTHONDONTWRITEBYTECODE=1

echo "🔧 Setting up Blog Agent Backend..."

# Install uv if needed
if ! command -v uv &> /dev/null; then
    echo "📦 Installing uv..."
    python3 -m pip install --user uv
fi

# Create virtual environment
if [ -d "venv" ]; then
    echo "⚠️  Removing existing venv..."
    rm -rf venv
fi

echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate venv (only works if script is sourced)
source venv/bin/activate

# Upgrade pip inside venv
python -m pip install --upgrade pip

# Install agent_engine dependencies
echo " Installing Agent Engine dependencies..."
cd agent_engine
cd blog_generator || { echo "❌ agent_engine folder not found"; exit 1; }
python -m pip install -r requirements.txt
cd ..

# Install MCP server dependencies
echo "📦 Installing MCP Server dependencies..."
cd ..
cd mcp-servers || { echo "❌ mcp-servers folder not found"; exit 1; }
python -m pip install -r requirements.txt
cd ..

echo "✅ Setup complete!"

# Instructions for the user
echo "-----------------------------------------"
echo "To start working:"
echo "1. Activate virtual environment: source venv/bin/activate"
echo "2. Navigate to agent_engine: cd agent_engine/blog_generator"
echo "3. Run your scripts normally."
echo "-----------------------------------------"
