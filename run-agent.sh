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

echo "📝 Configuration:"
echo "   Server host/port configured in config.yaml"
echo "   Edit config.yaml to change the host based on your network"
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
