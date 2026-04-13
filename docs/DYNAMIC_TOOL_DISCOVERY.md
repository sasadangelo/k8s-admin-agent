# Dynamic Tool Discovery from MCP Server

## Problem

Previously, the K8s Admin Agent had a **static list** of Kubernetes operations hardcoded in the agent instructions. This meant:

1. **LLM couldn't see actual available tools** - It had to guess tool names from text descriptions
2. **Manual maintenance required** - Every time MCP Server added/changed tools, we had to update instructions
3. **No validation** - LLM could try to call non-existent tools
4. **Poor discoverability** - New tools weren't automatically available to the agent

## Solution

Implemented **dynamic tool discovery** that:

1. **Queries MCP Server at startup** - Fetches actual available tools via `tools/list` method
2. **Generates documentation automatically** - Creates detailed tool descriptions with parameters
3. **Updates LLM instructions** - Injects real tool definitions into agent instructions
4. **Caches results** - Avoids repeated queries to MCP Server

## Implementation

### 1. Added `get_available_tools()` method to K8sMCPTool

```python
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

    # ... parse response and cache tools
```

### 2. Updated agent.py to fetch and inject tool documentation

```python
# Initialize K8s MCP tool and fetch available tools
k8s_tool = K8sMCPTool(mcp_url=mcp_url)

try:
    available_tools = await k8s_tool.get_available_tools()
    logger.info(f"Fetched {len(available_tools)} tools from MCP Server")

    # Build dynamic tool documentation
    tools_doc = "\n\n### Available Kubernetes Operations\n\n"
    for tool in available_tools:
        tool_name = tool.get("name", "unknown")
        tool_desc = tool.get("description", "No description")
        tool_schema = tool.get("inputSchema", {})

        tools_doc += f"**{tool_name}**\n"
        tools_doc += f"  Description: {tool_desc}\n"

        # Add parameters documentation...

    # Update instructions with dynamic tool list
    instructions = instructions.replace(
        "### Available Operations",
        tools_doc
    )
```

## Benefits

### 1. Automatic Tool Discovery
- New tools in MCP Server are immediately available
- No manual updates needed to agent code

### 2. Accurate Tool Information
- LLM sees exact tool names, descriptions, and parameters
- Reduces hallucination and incorrect tool calls

### 3. Better Parameter Validation
- LLM knows which parameters are required vs optional
- Understands parameter types and descriptions

### 4. Maintainability
- Single source of truth (MCP Server)
- Changes to tools automatically propagate

## Example Tool Documentation Generated

```
**namespaces_list**
  Description: List all namespaces in the cluster
  Parameters: (none)
  Example: {"tool_name": "namespaces_list", "arguments": {}}

**pods_list_in_namespace**
  Description: List all pods in a specific namespace
  Parameters:
    - namespace (string) (required): The namespace to list pods from
  Example: {"tool_name": "pods_list_in_namespace", "arguments": {...}}

**resources_scale**
  Description: Scale a Kubernetes resource
  Parameters:
    - kind (string) (required): Resource kind (Deployment, StatefulSet, etc.)
    - name (string) (required): Resource name
    - namespace (string) (required): Namespace
    - replicas (integer) (required): Desired number of replicas
  Example: {"tool_name": "resources_scale", "arguments": {...}}
```

## Testing

Run the test suite to verify dynamic tool discovery:

```bash
pytest tests/test_dynamic_tools.py -v
```

Or run standalone:

```bash
python tests/test_dynamic_tools.py
```

## Fallback Behavior

If MCP Server is unavailable during startup:
- Agent logs a warning
- Falls back to static tool documentation in instructions
- Agent continues to function with hardcoded tool list

## Future Improvements

1. **Real-time tool updates** - Subscribe to MCP Server tool changes
2. **Tool validation** - Validate tool calls against schema before sending
3. **Tool suggestions** - Suggest similar tools when LLM uses wrong name
4. **Performance metrics** - Track which tools are used most frequently