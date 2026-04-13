# Copyright 2025 © Kubernetes Admin Agent
# SPDX-License-Identifier: Apache-2.0
"""
Kubernetes Admin Agent
An AI-powered agent for managing Kubernetes clusters via MCP Server
"""
from __future__ import annotations

from textwrap import dedent
from typing import Annotated

from k8s_admin_agent.core import config, logger
from k8s_admin_agent.core.log import mask_sensitive_data

from a2a.types import AgentSkill, Message
from agentstack_sdk.a2a.extensions import (
    AgentDetail,
    AgentDetailContributor,
    AgentDetailTool,
    ErrorExtensionParams,
    ErrorExtensionServer,
    ErrorExtensionSpec,
    LLMServiceExtensionServer,
    LLMServiceExtensionSpec,
    TrajectoryExtensionServer,
    TrajectoryExtensionSpec,
    PlatformApiExtensionServer,
    PlatformApiExtensionSpec,
)
from agentstack_sdk.a2a.types import AgentMessage
from agentstack_sdk.server import Server
from agentstack_sdk.server.context import RunContext
from agentstack_sdk.server.middleware.platform_auth_backend import (
    PlatformAuthBackend,
)
from agentstack_sdk.server.store.platform_context_store import (
    PlatformContextStore,
)
from beeai_framework.adapters.agentstack.backend.chat import AgentStackChatModel, ProviderConfig  # noqa: F401
from beeai_framework.agents.requirement import RequirementAgent
from agentstack_sdk.platform import ModelProviderType  # noqa: F401
from beeai_framework.agents.requirement.events import (
    RequirementAgentFinalAnswerEvent,
    RequirementAgentSuccessEvent,
)
from beeai_framework.agents.requirement.utils._tool import FinalAnswerTool
from beeai_framework.backend import (
    AssistantMessage,
    ChatModelParameters,
    UserMessage,
)
from beeai_framework.errors import FrameworkError
from beeai_framework.middleware.trajectory import GlobalTrajectoryMiddleware
from beeai_framework.tools import AnyTool, Tool
from openinference.instrumentation.beeai import BeeAIInstrumentor

from k8s_admin_agent.helpers.trajectory import TrajectoryContent
from k8s_admin_agent.tools.k8s_mcp_tool import K8sMCPTool


beeai_instrumentor = BeeAIInstrumentor()
if beeai_instrumentor:
    beeai_instrumentor.instrument()

server = Server()

# Fix Ollama tool_choice_support BEFORE creating the agent
# Ollama only supports "auto" and "none", not "single"
# This must be done at module level, before the @agent decorator
AgentStackChatModel.providers_mapping[ModelProviderType.OLLAMA] = lambda: ProviderConfig(
    name="ollama",
    tool_choice_support={"none", "auto"},  # Remove "single" - Ollama doesn't support it
    openai_native=False,
)


@server.agent(  # type: ignore[call-arg]
    name="Kubernetes Admin",
    documentation_url="https://github.com/sasadangelo/k8s-admin-agent",
    version="1.0.0",
    default_input_modes=["text", "text/plain"],
    default_output_modes=["text", "text/plain"],
    detail=AgentDetail(
        interaction_mode="multi-turn",
        user_greeting="Hello! I'm your Kubernetes administrator. " "How can I help you manage your cluster today?",
        tools=[
            AgentDetailTool(
                name="Kubernetes Operations",
                description="Manage Kubernetes clusters: list/scale/delete " "resources, view logs, apply manifests",
            ),
        ],
        framework="BeeAI",
        programming_language="Python",
        author=AgentDetailContributor(name="K8s Admin Team"),
        contributors=[],
        license="Apache 2.0",
    ),
    skills=[
        AgentSkill(
            id="k8s-admin",
            name="Kubernetes Administration",
            description=dedent(
                """\
                AI-powered Kubernetes cluster administrator using MCP Server.

                ## Capabilities
                - List and inspect resources (pods, deployments, services, etc.)
                - Scale deployments and manage replicas
                - View logs and debug issues
                - Apply and manage YAML manifests
                - Monitor cluster health

                ## How It Works
                Uses BeeAI framework with Kubernetes MCP Server integration.
                Maintains conversation context and provides intelligent responses.

                ## Safety Features
                - Confirms destructive operations before executing
                - Provides detailed explanations of actions
                - Suggests best practices and alternatives
                """
            ),
            tags=["kubernetes", "devops", "infrastructure"],
            examples=[
                "List all pods in the default namespace",
                "Scale the nginx deployment to 5 replicas",
                "Show me the logs from the api-server pod",
                "What pods are failing in production?",
            ],
        )
    ],
)
async def k8s_admin(
    input: Message,
    context: RunContext,
    trajectory: Annotated[TrajectoryExtensionServer, TrajectoryExtensionSpec()],
    llm_ext: Annotated[
        LLMServiceExtensionServer,
        LLMServiceExtensionSpec.single_demand(),
    ],
    _e: Annotated[
        ErrorExtensionServer,
        ErrorExtensionSpec(ErrorExtensionParams(include_stacktrace=True)),
    ],
    _p: Annotated[PlatformApiExtensionServer, PlatformApiExtensionSpec()],
):
    """Kubernetes Admin Agent with MCP Server integration"""
    await context.store(input)

    # Log user input with sensitive data masked
    logger.info("=" * 80)
    logger.info("NEW REQUEST")
    # Convert input to string and mask sensitive data
    input_str = str(input)
    masked_input = mask_sensitive_data(input_str)
    logger.info(f"User message: {masked_input}")
    logger.info("=" * 80)

    # Send initial trajectory
    yield trajectory.trajectory_metadata(title="Starting", content="Received your Kubernetes request")

    # Extract user message from input
    user_text = ""
    if input.parts:
        for part in input.parts:
            # Access the root attribute which contains TextPart with text
            part_root = getattr(part, "root", None)
            if part_root is not None:
                text = getattr(part_root, "text", None)
                if text is not None:
                    user_text += text

    # Initialize history with the current user message
    # Cast to list to satisfy type checker - UserMessage is a subtype of AnyMessage
    history = [UserMessage(user_text)] if user_text else []  # type: ignore[list-item]

    # Agent instructions - will be populated with dynamic tool documentation
    instructions_template = dedent(
        """\
        You are a Kubernetes administrator. You interact with Kubernetes through the MCP Server tools listed below.

        ## CRITICAL RULES

        1. ❌ NEVER use "kubectl" as tool_name - it does NOT exist
        2. ✅ ONLY use tool names from the list below (e.g., "namespaces_list", "pods_list")
        3. Use SPECIFIC tools when available:
           - Namespaces → use "namespaces_list"
           - All pods → use "pods_list"
           - Pods in namespace → use "pods_list_in_namespace"
           - Other resources → use "resources_list"

        ## Tool Format
        {"tool_name": "exact_name_from_list_below", "arguments": {...}}

        {DYNAMIC_TOOLS_SECTION}

        ## Examples
        - List namespaces: {"tool_name": "namespaces_list", "arguments": {}}
        - List all pods: {"tool_name": "pods_list", "arguments": {}}
        - Pods in namespace: {"tool_name": "pods_list_in_namespace", "arguments": {"namespace": "default"}}
        """
    )

    # Configure tools - use config from config.yaml
    mcp_url = config.mcp.get_server_url("kubernetes_mcp")
    logger.info(f"MCP Server URL: {mcp_url}")

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

        # Update instructions with dynamic tool list
        instructions = instructions_template.replace("{DYNAMIC_TOOLS_SECTION}", tools_doc)

        logger.info("Updated instructions with dynamic tool documentation")

    except Exception as e:
        logger.warning(f"Failed to fetch tools from MCP Server: {e}")
        logger.warning("Using fallback instructions without dynamic tools")
        # Fallback to basic instructions without dynamic tools
        instructions = instructions_template.replace(
            "{DYNAMIC_TOOLS_SECTION}",
            "\n### Available Operations\n\nFailed to load tools from MCP Server. Please check server connectivity.\n",
        )

    tools: list[AnyTool] = [k8s_tool]

    # Initialize LLM
    llm = AgentStackChatModel(parameters=ChatModelParameters(stream=True))
    llm.set_context(llm_ext)

    # Configure tool_choice support for Ollama AFTER setting context
    # Ollama doesn't support tool_choice="single", only "auto" and "none"
    # We must set this on the instance's internal _tool_choice_support attribute
    llm._tool_choice_support = {"none", "auto"}

    logger.info(f"Configured LLM tool_choice_support: {llm._tool_choice_support}")

    # Log LLM configuration
    logger.info("=" * 80)
    logger.info("LLM Configuration:")
    logger.info(f"  Model: {llm.__class__.__name__}")
    logger.info(f"  Instructions length: {len(instructions)} characters")
    logger.info("=" * 80)

    # Log full instructions sent to LLM
    logger.debug("=" * 80)
    logger.debug("INSTRUCTIONS SENT TO LLM:")
    logger.debug(instructions)
    logger.debug("=" * 80)

    # Create agent
    agent = RequirementAgent(
        llm=llm,
        tools=tools,
        instructions=instructions,
        middlewares=[GlobalTrajectoryMiddleware(included=[Tool])],
    )

    final_answer: AssistantMessage | None = None
    new_messages = list(history)  # type: ignore[arg-type]

    # Log messages being sent to LLM
    logger.info("=" * 80)
    logger.info("MESSAGES SENT TO LLM")
    logger.info(f"Number of messages: {len(new_messages)}")
    for i, msg in enumerate(new_messages):
        msg_str = str(msg)
        masked_msg = mask_sensitive_data(msg_str)
        logger.info(f"Message {i+1}: {masked_msg[:500]}...")  # First 500 chars
    logger.info("=" * 80)

    try:
        async for event, meta in agent.run(
            new_messages,  # type: ignore[arg-type]
            expected_output=dedent(
                """\
                Provide the final answer to the user's Kubernetes request.

                Include:
                - Clear summary of what was done
                - Relevant details (resource names, statuses, etc.)
                - Any warnings or recommendations
                - Next steps if applicable

                Format your response clearly with proper structure.
                """
            ),
        ):
            match event:
                case RequirementAgentFinalAnswerEvent(delta=delta):
                    yield delta
                case RequirementAgentSuccessEvent(state=state):
                    final_answer = state.answer

                    # Log LLM response
                    logger.info("=" * 80)
                    logger.info("LLM RESPONSE RECEIVED")
                    if final_answer:
                        answer_str = str(final_answer)
                        masked_answer = mask_sensitive_data(answer_str)
                        logger.info(f"Answer: {masked_answer[:1000]}...")  # First 1000 chars
                    logger.info("=" * 80)

                    last_step = state.steps[-1]
                    # Skip internal tools
                    if last_step.tool and last_step.tool.name == FinalAnswerTool.name:
                        continue

                    # Create trajectory metadata with proper serialization
                    trajectory_content = TrajectoryContent(
                        input=last_step.input,
                        output=last_step.output,
                        error=last_step.error,
                    )
                    metadata = trajectory.trajectory_metadata(
                        title=(last_step.tool.name if last_step.tool else None),
                        content=trajectory_content.model_dump_json(),
                        group_id=last_step.id,
                    )
                    yield metadata
                    await context.store(AgentMessage(metadata=metadata))

        if final_answer:
            # Yield the final answer to the user
            logger.info("=" * 80)
            logger.info("SENDING FINAL ANSWER TO USER")
            logger.info(f"Answer: {final_answer.text}")
            logger.info("=" * 80)
            message = AgentMessage(text=final_answer.text)
            yield message
            await context.store(message)

    except FrameworkError as err:
        logger.error(f"Framework error: {err.explain()}")
        raise RuntimeError(err.explain())


def serve():
    """Start the Kubernetes Admin Agent server"""
    try:
        server.run(
            host=config.server.host,
            port=config.server.port,
            configure_telemetry=True,
            context_store=PlatformContextStore(),
            auth_backend=PlatformAuthBackend(),
        )
    except KeyboardInterrupt:
        logger.info("Shutting down Kubernetes Admin Agent")
        pass


if __name__ == "__main__":
    serve()
