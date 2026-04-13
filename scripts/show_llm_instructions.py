#!/usr/bin/env python3
# Copyright 2025 © Kubernetes Admin Agent
# SPDX-License-Identifier: Apache-2.0
"""
Script to show what instructions the LLM receives
"""
import asyncio
import sys
from pathlib import Path
from textwrap import dedent

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from k8s_admin_agent.tools.k8s_mcp_tool import K8sMCPTool


async def main():
    """Show LLM instructions with dynamic tool documentation"""

    # Base instructions (same as in agent.py)
    instructions = dedent(
        """\
        You are a Kubernetes cluster administrator assistant with deep expertise.

        ## AVAILABLE TOOLS

        You have access to TWO types of tools:

        1. **kubernetes_mcp** - For ALL Kubernetes operations (listing, scaling, deleting resources, etc.)
        2. **final_answer** - ONLY for providing your final response to the user

        ### Available Operations

        (This section will be replaced with dynamic tool documentation)
        """
    )

    print("=" * 80)
    print("Fetching tools and generating LLM instructions...")
    print("=" * 80)

    tool = K8sMCPTool(mcp_url="http://localhost:8080")

    try:
        available_tools = await tool.get_available_tools()
        print(f"\n✓ Fetched {len(available_tools)} tools from MCP Server\n")

        # Build dynamic tool documentation (same logic as agent.py)
        tools_doc = "\n\n### Available Kubernetes Operations\n\n"
        for t in available_tools:
            tool_name = t.get("name", "unknown")
            tool_desc = t.get("description", "No description")
            tool_schema = t.get("inputSchema", {})

            tools_doc += f"**{tool_name}**\n"
            tools_doc += f"  Description: {tool_desc}\n"

            # Add parameters if available
            properties = tool_schema.get("properties", {})
            required = tool_schema.get("required", [])

            if properties:
                tools_doc += "  Parameters:\n"
                for param_name, param_info in properties.items():
                    param_desc = param_info.get("description", "")
                    param_type = param_info.get("type", "string")
                    is_required = " (required)" if param_name in required else " (optional)"
                    tools_doc += f"    - {param_name} ({param_type}){is_required}: {param_desc}\n"

            tools_doc += f'  Example: {{"tool_name": "{tool_name}", "arguments": {{...}}}}\n\n'

        # Update instructions
        final_instructions = instructions.replace(
            "### Available Operations\n\n(This section will be replaced with dynamic tool documentation)", tools_doc
        )

        print("=" * 80)
        print("INSTRUCTIONS SENT TO LLM:")
        print("=" * 80)
        print(final_instructions)
        print("=" * 80)
        print(f"\nTotal length: {len(final_instructions)} characters")
        print(f"Number of tools documented: {len(available_tools)}")

    except Exception as e:
        print(f"\n✗ Error: {e}")
        return 1
    finally:
        await tool.close()

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))

# Made with Bob
