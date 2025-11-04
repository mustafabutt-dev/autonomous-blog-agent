#!/bin/bash
export PYTHONDONTWRITEBYTECODE=1
# Start all services for blog agent backend

echo "🚀 Starting Blog Agent Backend Services..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Run setup.sh first."
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Start MCP servers in background
echo "📡 Starting Keyword Search MCP Server..."
cd mcp-servers/keyword-search
python server.py &
KEYWORD_PID=$!
cd ../..

sleep 2

echo "📡 Starting FAQ Generator MCP Server..."
cd mcp-servers/faq-generator
python server.py &
FAQ_PID=$!
cd ../..

sleep 2

# Start Agent Engine
echo "🤖 Starting Agent Engine..."
cd agent-engine
uvicorn main:app
cd ..

echo ""
echo "✅ All services started!"
echo ""
echo "📍 Service URLs:"
echo "   Agent Engine:       http://localhost:8000"
echo "   Keyword Search MCP: Port 3001 (stdio)"
echo "   FAQ Generator MCP:  Port 3002 (stdio)"
echo ""
echo "💡 To stop all services:"
echo "   kill $KEYWORD_PID $FAQ_PID $AGENT_PID"
echo ""
echo "📖 API Documentation: http://localhost:8000/docs"

# Wait for user input to stop
read -p "Press Enter to stop all services..."

# Kill all processes
kill $KEYWORD_PID $FAQ_PID $AGENT_PID
echo "✅ All services stopped."