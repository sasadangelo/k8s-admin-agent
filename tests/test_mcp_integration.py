# Copyright 2025 © Kubernetes Admin Agent
# SPDX-License-Identifier: Apache-2.0
"""
Integration tests for Kubernetes MCP Server
These tests require the MCP Server to be running at localhost:8080
Run with: pytest tests/test_mcp_integration.py -v
"""
import pytest
import httpx
import json
import re
import os


# Skip these tests if MCP_SERVER_URL is not set or server is not available
MCP_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8080")


def parse_sse_response(text: str) -> dict:
    """Parse Server-Sent Events response"""
    match = re.search(r"data: ({.*})", text, re.DOTALL)
    if match:
        return json.loads(match.group(1))
    return {}


async def check_mcp_server_available():
    """Check if MCP server is available"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{MCP_URL}/health")
            return response.status_code == 200
    except Exception:
        return False


@pytest.fixture(scope="module")
async def mcp_client():
    """Create an HTTP client for MCP server tests"""
    if not await check_mcp_server_available():
        pytest.skip(f"MCP Server not available at {MCP_URL}")

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Initialize session
        response = await client.post(
            f"{MCP_URL}/mcp",
            json={
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "k8s-admin-test", "version": "1.0.0"},
                },
                "id": 0,
            },
        )
        assert response.status_code == 200

        # Send initialized notification
        await client.post(
            f"{MCP_URL}/mcp",
            json={
                "jsonrpc": "2.0",
                "method": "notifications/initialized",
                "params": {},
            },
        )

        yield client


@pytest.mark.integration
@pytest.mark.asyncio
async def test_mcp_session_initialization():
    """Test MCP session initialization"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{MCP_URL}/mcp",
            json={
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "k8s-admin-test", "version": "1.0.0"},
                },
                "id": 0,
            },
        )

        assert response.status_code == 200
        result = parse_sse_response(response.text)
        assert "result" in result
        assert "serverInfo" in result["result"]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_list_tools(mcp_client):
    """Test listing available MCP tools"""
    response = await mcp_client.post(
        f"{MCP_URL}/mcp",
        json={"jsonrpc": "2.0", "method": "tools/list", "params": {}, "id": 1},
    )

    assert response.status_code == 200
    result = parse_sse_response(response.text)
    assert "result" in result
    assert "tools" in result["result"]
    tools = result["result"]["tools"]
    assert len(tools) > 0

    # Check for expected tools
    tool_names = [tool["name"] for tool in tools]
    assert "pods_list" in tool_names
    assert "namespaces_list" in tool_names


@pytest.mark.integration
@pytest.mark.asyncio
async def test_list_namespaces(mcp_client):
    """Test listing Kubernetes namespaces"""
    response = await mcp_client.post(
        f"{MCP_URL}/mcp",
        json={
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {"name": "namespaces_list", "arguments": {}},
            "id": 2,
        },
    )

    assert response.status_code == 200
    result = parse_sse_response(response.text)
    assert "result" in result
    assert "content" in result["result"]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_list_pods_default_namespace(mcp_client):
    """Test listing pods in default namespace"""
    response = await mcp_client.post(
        f"{MCP_URL}/mcp",
        json={
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "pods_list_in_namespace",
                "arguments": {"namespace": "default"},
            },
            "id": 3,
        },
    )

    assert response.status_code == 200
    result = parse_sse_response(response.text)
    assert "result" in result


@pytest.mark.integration
@pytest.mark.asyncio
async def test_invalid_tool_name(mcp_client):
    """Test calling an invalid tool name"""
    response = await mcp_client.post(
        f"{MCP_URL}/mcp",
        json={
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {"name": "invalid_tool_name", "arguments": {}},
            "id": 4,
        },
    )

    assert response.status_code == 200
    result = parse_sse_response(response.text)
    # Should return an error
    assert "error" in result or (
        "result" in result and "error" in str(result["result"])
    )


# Made with Bob
