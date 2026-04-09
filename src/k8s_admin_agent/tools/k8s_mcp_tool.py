# Copyright 2025 © Kubernetes Admin Agent
# SPDX-License-Identifier: Apache-2.0
"""
Kubernetes MCP Tool Wrapper
Wraps MCP Server Kubernetes tools for use with BeeAI framework
"""
from __future__ import annotations

import httpx
from typing import Any, Optional
from pydantic import BaseModel, Field
from beeai_framework.tools import Tool, ToolError, JSONToolOutput


class K8sMCPToolInput(BaseModel):
    """Input for Kubernetes MCP tool calls"""

    tool_name: str = Field(description="Name of the Kubernetes tool to execute")
    arguments: dict[str, Any] = Field(
        default_factory=dict, description="Arguments for the tool"
    )


class K8sMCPToolResult(BaseModel):
    """Result from Kubernetes MCP tool calls"""

    result: Any = Field(description="Result from the tool execution")
    success: bool = Field(description="Whether the tool execution was successful")
    error: Optional[str] = Field(
        default=None, description="Error message if execution failed"
    )


class K8sMCPToolOutput(JSONToolOutput[K8sMCPToolResult]):
    """Output wrapper for Kubernetes MCP tool"""

    pass


class K8sMCPTool(Tool[K8sMCPToolInput, None, K8sMCPToolOutput]):
    """
    Tool for executing Kubernetes operations via MCP Server.

    This tool acts as a bridge between BeeAI framework and the Kubernetes MCP Server,
    allowing the agent to perform Kubernetes operations like listing pods, scaling deployments, etc.
    """

    name: str = "kubernetes_mcp"
    description: str = """Execute Kubernetes operations via MCP Server.

This tool provides access to all Kubernetes management capabilities including:
- Listing resources (pods, deployments, services, etc.)
- Scaling deployments
- Getting logs
- Applying manifests
- And more

Specify the tool_name and arguments to execute the desired Kubernetes operation.
"""

    def __init__(self, mcp_url: str = "http://k8s-mcp-server:8080"):
        """
        Initialize the Kubernetes MCP tool.

        Args:
            mcp_url: URL of the Kubernetes MCP Server
        """
        super().__init__()
        self.mcp_url = mcp_url
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client"""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    @property
    def input_schema(self) -> type[K8sMCPToolInput]:
        return K8sMCPToolInput

    async def _run(
        self, input: K8sMCPToolInput, options: None, context: Any
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
            client = await self._get_client()

            # Prepare MCP request payload
            payload = {
                "method": "tools/call",
                "params": {"name": input.tool_name, "arguments": input.arguments},
            }

            # Execute MCP request
            response = await client.post(f"{self.mcp_url}/mcp", json=payload)

            if response.status_code != 200:
                return K8sMCPToolOutput(
                    result=K8sMCPToolResult(
                        result=None,
                        success=False,
                        error=f"MCP Server returned status "
                        f"{response.status_code}: {response.text}",
                    )
                )

            result = response.json()

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
                    result=result.get("result", result), success=True, error=None
                )
            )

        except httpx.RequestError as e:
            raise ToolError(
                f"Failed to connect to MCP Server at " f"{self.mcp_url}: {str(e)}"
            )
        except Exception as e:
            raise ToolError(
                f"Unexpected error executing Kubernetes " f"operation: {str(e)}"
            )

    async def close(self):
        """Close the HTTP client"""
        if self._client:
            await self._client.aclose()
            self._client = None
