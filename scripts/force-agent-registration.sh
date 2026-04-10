#!/bin/bash
# Force agent registration utility
# This script removes any existing agent registration and starts the agent with custom configuration

set -e

# ============================================================================
# CONFIGURATION - Modify these variables as needed
# ============================================================================

# MCP Server URL (default: localhost:8080)
MCP_SERVER_URL="${MCP_SERVER_URL:-http://localhost:8080}"

# Host IP address where the agent will listen (default: 0.0.0.0 for all interfaces)
# For Mac with specific IP: use your Mac's IP address (e.g., 192.168.1.16)
HOST="${HOST:-0.0.0.0}"

# Port where the agent will listen (default: 8000)
PORT="${PORT:-8000}"

# ============================================================================
# SCRIPT EXECUTION - Do not modify below this line
# ============================================================================

echo "🔧 Force Agent Registration Utility"
echo "===================================="
echo ""

# Remove old registration
echo "📝 Checking for existing agent registration..."
AGENT_ID=$(agentstack agent list 2>/dev/null | grep "Kubernetes Admin" | awk '{print $1}' || echo "")

if [ -n "$AGENT_ID" ]; then
    echo "   Found existing registration: $AGENT_ID"
    echo "   Removing old registration..."
    echo "y" | agentstack agent remove "$AGENT_ID" 2>/dev/null || true
    echo "   ✅ Removed"
    sleep 2
else
    echo "   No existing registration found"
fi
echo ""

# Stop any running agent
echo "🛑 Stopping any running agent processes..."
pkill -f "uv run server" 2>/dev/null || true
sleep 2
echo "   ✅ Stopped"
echo ""

# Export configuration
export MCP_SERVER_URL
export HOST
export PORT

# Display configuration
echo "📝 Agent Configuration:"
echo "   MCP_SERVER_URL: $MCP_SERVER_URL"
echo "   HOST: $HOST"
echo "   PORT: $PORT"
echo ""

# Start agent
echo "🚀 Starting agent server..."
echo "   Agent will listen on: http://$HOST:$PORT"
echo "   Access AgentStack UI at: http://localhost:8333"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Run the server
uv run server

# Made with Bob