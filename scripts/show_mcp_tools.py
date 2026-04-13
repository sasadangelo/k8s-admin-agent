#!/usr/bin/env python3
# Copyright 2025 © Kubernetes Admin Agent
# SPDX-License-Identifier: Apache-2.0
"""
Script to display all available tools from MCP Server
"""
import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from k8s_admin_agent.tools.k8s_mcp_tool import K8sMCPTool


async def main():
    """Display all available tools from MCP Server"""
    print("=" * 80)
    print("Fetching tools from MCP Server...")
    print("=" * 80)

    tool = K8sMCPTool(mcp_url="http://localhost:8080")

    try:
        tools = await tool.get_available_tools()

        print(f"\n✓ Found {len(tools)} tools\n")

        for i, t in enumerate(tools, 1):
            name = t.get("name", "unknown")
            description = t.get("description", "No description")
            schema = t.get("inputSchema", {})
            properties = schema.get("properties", {})
            required = schema.get("required", [])

            print(f"{i}. {name}")
            print(f"   Description: {description}")

            if properties:
                print("   Parameters:")
                for param_name, param_info in properties.items():
                    param_type = param_info.get("type", "string")
                    param_desc = param_info.get("description", "")
                    is_req = " (required)" if param_name in required else " (optional)"
                    print(f"     - {param_name} ({param_type}){is_req}")
                    if param_desc:
                        print(f"       {param_desc}")
            else:
                print("   Parameters: none")

            print()

        print("=" * 80)
        print("Tool names for LLM:")
        print("=" * 80)
        for t in tools:
            print(f"  - {t['name']}")

    except Exception as e:
        print(f"\n✗ Error: {e}")
        return 1
    finally:
        await tool.close()

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))

# Made with Bob
