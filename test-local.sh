#!/bin/bash
# Test script for running the K8s Admin Agent locally with AgentStack

set -e

echo "🚀 Starting K8s Admin Agent locally..."
echo ""

# Check if AgentStack platform is running
if ! curl -s http://localhost:8333/health > /dev/null 2>&1; then
    echo "❌ AgentStack platform is not running on localhost:8333"
    echo "   Start it with: agentstack platform start"
    exit 1
fi

# Check if K8s MCP Server is accessible
if ! curl -s http://localhost:8080/health > /dev/null 2>&1; then
    echo "⚠️  Warning: K8s MCP Server not accessible on localhost:8080"
    echo "   Make sure you have port-forwarding active:"
    echo "   kubectl port-forward svc/k8s-mcp-server 8080:8080"
    echo ""
fi

# Set environment variables for local testing
export MCP_SERVER_URL="http://localhost:8080"
export HOST="127.0.0.1"
export PORT="8000"
export PLATFORM_AUTH__PUBLIC_URL="http://127.0.0.1:8000"

echo "📝 Configuration:"
echo "   MCP_SERVER_URL: $MCP_SERVER_URL"
echo "   HOST: $HOST"
echo "   PORT: $PORT"
echo "   PLATFORM_AUTH__PUBLIC_URL: $PLATFORM_AUTH__PUBLIC_URL"
echo ""

# Install dependencies if needed
if [ ! -d ".venv" ]; then
    echo "📦 Installing dependencies..."
    uv sync
    echo ""
fi

echo "🎯 Starting agent server..."
echo "   The agent will auto-register with AgentStack platform"
echo "   Access the UI at: http://localhost:8333"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Run the server
uv run server

# Made with Bob
