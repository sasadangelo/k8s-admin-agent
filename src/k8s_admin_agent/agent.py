# Copyright 2025 © Kubernetes Admin Agent
# SPDX-License-Identifier: Apache-2.0
"""
Kubernetes Admin Agent
An AI-powered agent for managing Kubernetes clusters via MCP Server
"""
from __future__ import annotations

import logging
import os
from textwrap import dedent
from typing import Annotated

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
from beeai_framework.adapters.agentstack.backend.chat import AgentStackChatModel
from beeai_framework.agents.requirement import RequirementAgent
from beeai_framework.agents.requirement.events import (
    RequirementAgentFinalAnswerEvent,
    RequirementAgentSuccessEvent,
)
from beeai_framework.agents.requirement.utils._tool import FinalAnswerTool
from beeai_framework.backend import (
    AssistantMessage,
    ChatModelParameters,
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

logger = logging.getLogger(__name__)

server = Server()


@server.agent(
    name="Kubernetes Admin",
    documentation_url="https://github.com/your-org/k8s-admin-agent",
    version="1.0.0",
    default_input_modes=["text", "text/plain"],
    default_output_modes=["text", "text/plain"],
    detail=AgentDetail(
        interaction_mode="multi-turn",
        user_greeting="Hello! I'm your Kubernetes administrator. "
        "How can I help you manage your cluster today?",
        tools=[
            AgentDetailTool(
                name="Kubernetes Operations",
                description="Manage Kubernetes clusters: list/scale/delete "
                "resources, view logs, apply manifests",
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

    # Send initial trajectory
    yield trajectory.trajectory_metadata(
        title="Starting", content="Received your Kubernetes request"
    )

    # Initialize with empty history to avoid meta attribute issues
    # The current message is already stored in context
    history = []

    # Initialize LLM
    llm = AgentStackChatModel(parameters=ChatModelParameters(stream=True))
    llm.set_context(llm_ext)

    # Agent instructions
    instructions = dedent(
        """\
        You are a Kubernetes cluster administrator assistant with deep expertise.

        ## Your Role
        Help users manage their Kubernetes clusters safely and efficiently.
        You have access to Kubernetes operations via the MCP Server.

        ## Core Guidelines
        - Always be helpful, accurate, and security-conscious
        - Maintain conversation context
        - Explain what you're doing in clear terms

        ## Safety Rules
        - ALWAYS confirm destructive operations (delete, scale to 0) before executing
        - Warn about potential impacts of changes
        - Suggest rollback strategies for risky operations
        - Check resource status before and after operations

        ## Best Practices
        - When troubleshooting, gather comprehensive information first
        - Suggest Kubernetes best practices when appropriate
        - Provide context and explanations with technical details
        - Use proper formatting (code blocks, lists) for clarity

        ## Tool Usage
        Use the kubernetes_mcp tool to execute Kubernetes operations.

        Available tools (specify in tool_name parameter):
        - pods_list: List all pods across all namespaces
        - pods_list_in_namespace: List pods in a specific namespace
        - pods_get: Get details of a specific pod
        - pods_delete: Delete a pod
        - pods_log: Get logs from a pod
        - pods_exec: Execute command in a pod
        - pods_run: Run a new pod
        - pods_top: Get resource usage of pods
        - namespaces_list: List all namespaces
        - nodes_top: Get resource usage of nodes
        - nodes_stats_summary: Get detailed node statistics
        - nodes_log: Get logs from a node
        - events_list: List cluster events
        - resources_list: List any Kubernetes resource type
        - resources_get: Get a specific resource
        - resources_create_or_update: Create or update a resource
        - resources_delete: Delete a resource
        - resources_scale: Scale a resource
        - configuration_view: View current kubeconfig

        Example usage:
        - To list pods: tool_name="pods_list", arguments={}
        - To list pods in namespace: tool_name="pods_list_in_namespace", arguments={"namespace": "default"}
        - To get pod logs: tool_name="pods_log", arguments={"name": "pod-name", "namespace": "default"}

        ## Response Quality
        - Provide complete, well-structured answers
        - Break down complex operations into steps
        - Always complete tasks fully before providing final answers
        - Include relevant details (pod names, statuses, resource usage, etc.)
        """
    )

    # Configure tools
    mcp_url = os.getenv("MCP_SERVER_URL", "http://k8s-mcp-server:8080")
    tools: list[AnyTool] = [
        K8sMCPTool(mcp_url=mcp_url),
    ]

    # Create agent
    agent = RequirementAgent(
        llm=llm,
        tools=tools,
        instructions=instructions,
        middlewares=[GlobalTrajectoryMiddleware(included=[Tool])],
    )

    final_answer: AssistantMessage | None = None
    new_messages = list(history)

    try:
        async for event, meta in agent.run(
            new_messages,
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
            message = AgentMessage(text=final_answer.text)
            await context.store(message)

    except FrameworkError as err:
        raise RuntimeError(err.explain())


def serve():
    """Start the Kubernetes Admin Agent server"""
    try:
        server.run(
            host=os.getenv("HOST", "0.0.0.0"),
            port=int(os.getenv("PORT", 8000)),
            configure_telemetry=True,
            context_store=PlatformContextStore(),
            auth_backend=PlatformAuthBackend(),
        )
    except KeyboardInterrupt:
        logger.info("Shutting down Kubernetes Admin Agent")
        pass


if __name__ == "__main__":
    serve()
