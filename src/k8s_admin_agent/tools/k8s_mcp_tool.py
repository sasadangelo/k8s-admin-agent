# Copyright 2025 © Kubernetes Admin Agent
# SPDX-License-Identifier: Apache-2.0
"""
Kubernetes MCP Tool Wrapper
Wraps MCP Server Kubernetes tools for use with BeeAI framework
Supports SSE transport and session management
"""
from __future__ import annotations

import httpx
import json
import re
from typing import Any, Optional
from pydantic import BaseModel, Field
from beeai_framework.tools import (
    Tool,
    ToolError,
    JSONToolOutput,
    ToolRunOptions,
)
from beeai_framework.context import RunContext
from beeai_framework.emitter import Emitter


class K8sMCPToolInput(BaseModel):
    """Input for Kubernetes MCP tool calls"""

    tool_name: str = Field(description="Name of the Kubernetes tool to execute")
    arguments: dict[str, Any] = Field(default_factory=dict, description="Arguments for the tool")


class K8sMCPToolResult(BaseModel):
    """Result from Kubernetes MCP tool calls"""

    result: Any = Field(description="Result from the tool execution")
    success: bool = Field(description="Whether the tool execution was successful")
    error: Optional[str] = Field(default=None, description="Error message if execution failed")


class K8sMCPToolOutput(JSONToolOutput[K8sMCPToolResult]):
    """Output wrapper for Kubernetes MCP tool"""

    pass


class K8sMCPTool(Tool[K8sMCPToolInput, ToolRunOptions, K8sMCPToolOutput]):
    """
    Tool for executing Kubernetes operations via MCP Server.

    This tool acts as a bridge between BeeAI framework and the
    Kubernetes MCP Server, allowing the agent to perform Kubernetes
    operations like listing pods, scaling deployments, etc.
    Supports SSE transport and automatic session management.
    """

    @property
    def name(self) -> str:
        """Tool name"""
        return "kubernetes_mcp"

    @property
    def description(self) -> str:
        """Tool description"""
        return (
            "Execute Kubernetes operations via MCP Server. "
            "This tool provides access to all Kubernetes management "
            "capabilities including: listing resources (pods, deployments, "
            "services, etc.), scaling deployments, getting logs, applying "
            "manifests, and more. Specify the tool_name and arguments to "
            "execute the desired Kubernetes operation."
        )

    def __init__(self, mcp_url: str = "http://k8s-mcp-server:8080"):
        """
        Initialize the Kubernetes MCP tool.

        Args:
            mcp_url: URL of the Kubernetes MCP Server
        """
        super().__init__()
        self.mcp_url = mcp_url
        self._client: Optional[httpx.AsyncClient] = None
        self._session_initialized = False
        self._request_id = 0
        self._available_tools: Optional[list[dict[str, Any]]] = None

    def _parse_sse_response(self, text: str) -> dict:
        """Parse Server-Sent Events response"""
        # Extract JSON from SSE format: "event: message\ndata: {...}"
        match = re.search(r"data: ({.*})", text, re.DOTALL)
        if match:
            return json.loads(match.group(1))
        return {}

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client"""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    async def _initialize_session(self) -> None:
        """Initialize MCP session if not already initialized"""
        if self._session_initialized:
            return

        client = await self._get_client()
        self._request_id += 1

        response = await client.post(
            f"{self.mcp_url}/mcp",
            json={
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "k8s-admin-agent",
                        "version": "1.0.0",
                    },
                },
                "id": self._request_id,
            },
        )

        if response.status_code != 200:
            raise ToolError(f"Failed to initialize MCP session: {response.text}")

        result = self._parse_sse_response(response.text)
        if "error" in result:
            raise ToolError(f"MCP session initialization error: {result['error']}")

        # Send initialized notification to complete handshake
        await client.post(
            f"{self.mcp_url}/mcp",
            json={
                "jsonrpc": "2.0",
                "method": "notifications/initialized",
                "params": {},
            },
        )

        self._session_initialized = True

    async def get_available_tools(self) -> list[dict[str, Any]]:
        """
        Get list of available tools from MCP Server.

        Returns:
            List of tool definitions with name, description, and input schema
        """
        if self._available_tools is not None:
            return self._available_tools

        await self._initialize_session()

        client = await self._get_client()
        self._request_id += 1

        response = await client.post(
            f"{self.mcp_url}/mcp",
            json={
                "jsonrpc": "2.0",
                "method": "tools/list",
                "params": {},
                "id": self._request_id,
            },
        )

        if response.status_code != 200:
            raise ToolError(f"Failed to list tools: {response.text}")

        result = self._parse_sse_response(response.text)
        if "error" in result:
            raise ToolError(f"Error listing tools: {result['error']}")

        tools = result.get("result", {}).get("tools", [])
        self._available_tools = tools
        return tools

    @property
    def input_schema(self) -> type[K8sMCPToolInput]:
        return K8sMCPToolInput

    def _create_emitter(self) -> Emitter:
        """Create emitter for tool execution events"""
        return Emitter.root().child(
            namespace=["tool", "kubernetes_mcp"],
            creator=self,
        )

    async def _run(
        self,
        input: K8sMCPToolInput,
        options: ToolRunOptions | None,
        context: RunContext,
    ) -> K8sMCPToolOutput:
        """
        Execute a Kubernetes operation via MCP Server.

        Args:
            input: Tool input containing tool_name and arguments

        Returns:
            K8sMCPToolOutput with the result

        Raises:
            ToolError: If the MCP Server request fails
        """
        try:
            # Initialize session if needed
            await self._initialize_session()

            client = await self._get_client()
            self._request_id += 1

            # Prepare MCP request payload (JSON-RPC 2.0 format)
            payload = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": input.tool_name,
                    "arguments": input.arguments,
                },
                "id": self._request_id,
            }

            # Execute MCP request
            response = await client.post(f"{self.mcp_url}/mcp", json=payload)

            if response.status_code != 200:
                return K8sMCPToolOutput(
                    result=K8sMCPToolResult(
                        result=None,
                        success=False,
                        error=f"MCP Server returned status " f"{response.status_code}: {response.text}",
                    )
                )

            result = self._parse_sse_response(response.text)

            # Check if MCP returned an error
            if "error" in result:
                return K8sMCPToolOutput(
                    result=K8sMCPToolResult(
                        result=None,
                        success=False,
                        error=f"MCP Error: {result['error']}",
                    )
                )

            return K8sMCPToolOutput(
                result=K8sMCPToolResult(
                    result=result.get("result", result),
                    success=True,
                    error=None,
                )
            )

        except httpx.RequestError as e:
            msg = f"Failed to connect to MCP Server at {self.mcp_url}"
            raise ToolError(f"{msg}: {str(e)}")
        except Exception as e:
            msg = "Unexpected error executing Kubernetes operation"
            raise ToolError(f"{msg}: {str(e)}")

    async def close(self):
        """Close the HTTP client"""
        if self._client:
            await self._client.aclose()
            self._client = None


# Made with Bob
