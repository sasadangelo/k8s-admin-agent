# Copyright 2025 © Kubernetes Admin Agent
# SPDX-License-Identifier: Apache-2.0
"""
Unit tests for K8sMCPTool
Tests the MCP tool integration with Kubernetes MCP Server
"""
import pytest
import httpx
from unittest.mock import AsyncMock, MagicMock, patch
from k8s_admin_agent.tools.k8s_mcp_tool import K8sMCPTool, K8sMCPToolInput
from beeai_framework.context import RunContext


@pytest.fixture
def mcp_tool():
    """Create a K8sMCPTool instance for testing"""
    return K8sMCPTool(mcp_url="http://localhost:8080")


@pytest.fixture
def mock_context():
    """Create a mock RunContext"""
    return MagicMock(spec=RunContext)


@pytest.mark.asyncio
async def test_tool_initialization(mcp_tool):
    """Test that the tool initializes correctly"""
    assert mcp_tool.name == "kubernetes_mcp"
    assert "Execute Kubernetes operations" in mcp_tool.description
    assert mcp_tool.mcp_url == "http://localhost:8080"
    assert mcp_tool._session_initialized is False


@pytest.mark.asyncio
async def test_parse_sse_response(mcp_tool):
    """Test SSE response parsing"""
    sse_text = 'event: message\ndata: {"result": {"test": "value"}}\n\n'
    result = mcp_tool._parse_sse_response(sse_text)
    assert result == {"result": {"test": "value"}}


@pytest.mark.asyncio
async def test_parse_sse_response_empty(mcp_tool):
    """Test SSE response parsing with empty data"""
    result = mcp_tool._parse_sse_response("invalid data")
    assert result == {}


@pytest.mark.asyncio
async def test_session_initialization_success(mcp_tool):
    """Test successful MCP session initialization"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = (
        'data: {"result": {"serverInfo": {"name": "k8s-mcp", "version": "1.0.0"}}}'
    )

    with patch.object(mcp_tool, "_get_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client

        await mcp_tool._initialize_session()

        assert mcp_tool._session_initialized is True
        assert mock_client.post.call_count == 2  # initialize + initialized notification


@pytest.mark.asyncio
async def test_session_initialization_error(mcp_tool):
    """Test MCP session initialization with error response"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = (
        'data: {"error": {"code": -32600, "message": "Invalid request"}}'
    )

    with patch.object(mcp_tool, "_get_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client

        with pytest.raises(Exception) as exc_info:
            await mcp_tool._initialize_session()

        assert "MCP session initialization error" in str(exc_info.value)


@pytest.mark.asyncio
async def test_run_tool_success(mcp_tool, mock_context):
    """Test successful tool execution"""
    tool_input = K8sMCPToolInput(
        tool_name="pods_list", arguments={"namespace": "default"}
    )

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = 'data: {"result": {"content": [{"text": "pod1, pod2"}]}}'

    with patch.object(mcp_tool, "_get_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client

        # Mock session initialization
        mcp_tool._session_initialized = True

        result = await mcp_tool._run(tool_input, None, mock_context)

        assert result.result.success is True
        assert result.result.error is None
        assert "content" in result.result.result


@pytest.mark.asyncio
async def test_run_tool_mcp_error(mcp_tool, mock_context):
    """Test tool execution with MCP error response"""
    tool_input = K8sMCPToolInput(tool_name="invalid_tool", arguments={})

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = (
        'data: {"error": {"code": -32601, "message": "Method not found"}}'
    )

    with patch.object(mcp_tool, "_get_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client

        mcp_tool._session_initialized = True

        result = await mcp_tool._run(tool_input, None, mock_context)

        assert result.result.success is False
        assert "MCP Error" in result.result.error


@pytest.mark.asyncio
async def test_run_tool_http_error(mcp_tool, mock_context):
    """Test tool execution with HTTP error"""
    tool_input = K8sMCPToolInput(tool_name="pods_list", arguments={})

    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.text = "Internal Server Error"

    with patch.object(mcp_tool, "_get_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client

        mcp_tool._session_initialized = True

        result = await mcp_tool._run(tool_input, None, mock_context)

        assert result.result.success is False
        assert "500" in result.result.error


@pytest.mark.asyncio
async def test_run_tool_connection_error(mcp_tool, mock_context):
    """Test tool execution with connection error"""
    tool_input = K8sMCPToolInput(tool_name="pods_list", arguments={})

    with patch.object(mcp_tool, "_get_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(
            side_effect=httpx.ConnectError("Connection refused")
        )
        mock_get_client.return_value = mock_client

        mcp_tool._session_initialized = True

        with pytest.raises(Exception) as exc_info:
            await mcp_tool._run(tool_input, None, mock_context)

        assert "Failed to connect to MCP Server" in str(exc_info.value)


@pytest.mark.asyncio
async def test_close_client(mcp_tool):
    """Test closing the HTTP client"""
    mock_client = AsyncMock()
    mcp_tool._client = mock_client

    await mcp_tool.close()

    mock_client.aclose.assert_called_once()
    assert mcp_tool._client is None


# Made with Bob
