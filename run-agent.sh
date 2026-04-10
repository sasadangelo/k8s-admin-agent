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

# Clean up any existing Kubernetes Admin agent registration
echo "🧹 Cleaning up existing agent registration..."
AGENT_ID=$(agentstack agent list 2>/dev/null | grep "Kubernetes Admin" | awk '{print $1}' | head -1 || echo "")
if [ -n "$AGENT_ID" ]; then
    echo "   Found existing registration: $AGENT_ID"
    agentstack delete "$AGENT_ID" -y 2>/dev/null || true
    echo "   ✅ Removed"
    sleep 2
else
    echo "   No existing registration found"
fi
echo ""

# Stop any running agent processes
echo "🛑 Stopping any running agent processes..."
pkill -f "uv run server" 2>/dev/null || true
sleep 2
echo ""

# Set environment variables for local testing
# IMPORTANT: Use Mac IP address directly in HOST to avoid host.docker.internal substitution
# AgentStack SDK replaces localhost/127.0.0.1 with host.docker.internal (line 345 in server.py)
# Using the actual Mac IP (9.150.161.51) bypasses this substitution
export MCP_SERVER_URL="http://localhost:8080"
export HOST="9.150.161.51"
export PORT="8000"
export PLATFORM_AUTH__PUBLIC_URL="http://9.150.161.51:8000"

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
