# Copyright 2025 © Kubernetes Admin Agent
# SPDX-License-Identifier: Apache-2.0
"""
Test dynamic tool discovery from MCP Server
"""
import pytest
from k8s_admin_agent.tools.k8s_mcp_tool import K8sMCPTool


@pytest.mark.asyncio
async def test_get_available_tools():
    """Test fetching available tools from MCP Server"""
    # Use localhost for testing
    tool = K8sMCPTool(mcp_url="http://localhost:8080")

    try:
        tools = await tool.get_available_tools()

        # Verify we got tools
        assert isinstance(tools, list)
        assert len(tools) > 0

        # Verify tool structure
        for t in tools:
            assert "name" in t
            assert "description" in t
            assert "inputSchema" in t

        # Verify specific expected tools
        tool_names = [t["name"] for t in tools]
        assert "namespaces_list" in tool_names
        assert "pods_list" in tool_names
        assert "pods_list_in_namespace" in tool_names

        print(f"\n✓ Found {len(tools)} tools from MCP Server")
        print("\nAvailable tools:")
        for t in tools:
            print(f"  - {t['name']}: {t['description'][:60]}...")

    finally:
        await tool.close()


@pytest.mark.asyncio
async def test_tool_caching():
    """Test that tools are cached after first fetch"""
    tool = K8sMCPTool(mcp_url="http://localhost:8080")

    try:
        # First call - should fetch from server
        tools1 = await tool.get_available_tools()

        # Second call - should use cache
        tools2 = await tool.get_available_tools()

        # Should be the same object (cached)
        assert tools1 is tools2

        print("\n✓ Tool caching works correctly")

    finally:
        await tool.close()


if __name__ == "__main__":
    import asyncio

    print("Testing dynamic tool discovery...")
    asyncio.run(test_get_available_tools())
    asyncio.run(test_tool_caching())
    print("\n✓ All tests passed!")

# Made with Bob
