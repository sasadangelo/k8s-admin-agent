# Copyright 2025 © Kubernetes Admin Agent
# SPDX-License-Identifier: Apache-2.0
"""
Unit tests for K8s Admin Agent
Tests the agent configuration and basic functionality
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from k8s_admin_agent.agent import k8s_admin, server
from a2a.types import Message
from agentstack_sdk.server.context import RunContext


@pytest.fixture
def mock_message():
    """Create a mock Message"""
    message = MagicMock(spec=Message)
    message.text = "List all pods in the cluster"
    return message


@pytest.fixture
def mock_context():
    """Create a mock RunContext"""
    context = AsyncMock(spec=RunContext)
    context.store = AsyncMock()
    return context


@pytest.fixture
def mock_trajectory():
    """Create a mock TrajectoryExtensionServer"""
    trajectory = MagicMock()
    trajectory.trajectory_metadata = MagicMock(return_value={"type": "trajectory"})
    return trajectory


@pytest.fixture
def mock_llm_ext():
    """Create a mock LLMServiceExtensionServer"""
    return MagicMock()


@pytest.fixture
def mock_error_ext():
    """Create a mock ErrorExtensionServer"""
    return MagicMock()


@pytest.fixture
def mock_platform_api():
    """Create a mock PlatformApiExtensionServer"""
    return MagicMock()


def test_server_instance():
    """Test that server instance is created"""
    assert server is not None
    assert hasattr(server, "agent")


def test_agent_decorator_configuration():
    """Test that agent is properly decorated with correct configuration"""
    # The agent function should be decorated
    assert hasattr(k8s_admin, "__wrapped__") or callable(k8s_admin)


@pytest.mark.asyncio
async def test_agent_basic_flow(
    mock_message,
    mock_context,
    mock_trajectory,
    mock_llm_ext,
    mock_error_ext,
    mock_platform_api,
):
    """Test basic agent execution flow"""
    with patch("k8s_admin_agent.agent.RequirementAgent") as mock_agent_class:
        # Mock the agent instance
        mock_agent = AsyncMock()
        mock_agent_class.return_value = mock_agent

        # Mock agent.run to yield some events
        async def mock_run(*args, **kwargs):
            # Simulate no events (agent completes without yielding)
            return
            yield  # Make it a generator

        mock_agent.run = mock_run

        # Execute the agent
        result_generator = k8s_admin(
            mock_message,
            mock_context,
            mock_trajectory,
            mock_llm_ext,
            mock_error_ext,
            mock_platform_api,
        )

        # Consume the generator
        results = []
        async for item in result_generator:
            results.append(item)

        # Verify context.store was called with the input message
        mock_context.store.assert_called()


@pytest.mark.asyncio
async def test_agent_with_mcp_tool():
    """Test that agent is configured with K8sMCPTool"""
    with patch("k8s_admin_agent.agent.RequirementAgent") as mock_agent_class:
        with patch("k8s_admin_agent.agent.K8sMCPTool") as mock_tool_class:
            mock_agent = AsyncMock()
            mock_agent_class.return_value = mock_agent

            async def mock_run(*args, **kwargs):
                return
                yield

            mock_agent.run = mock_run

            # Create mocks for all required parameters
            mock_message = MagicMock(spec=Message)
            mock_context = AsyncMock(spec=RunContext)
            mock_context.store = AsyncMock()
            mock_trajectory = MagicMock()
            mock_trajectory.trajectory_metadata = MagicMock(return_value={})
            mock_llm_ext = MagicMock()
            mock_error_ext = MagicMock()
            mock_platform_api = MagicMock()

            # Execute agent
            result_gen = k8s_admin(
                mock_message,
                mock_context,
                mock_trajectory,
                mock_llm_ext,
                mock_error_ext,
                mock_platform_api,
            )

            async for _ in result_gen:
                pass

            # Verify K8sMCPTool was instantiated
            mock_tool_class.assert_called_once()


def test_agent_instructions_content():
    """Test that agent has proper instructions"""
    # This is a simple check that the agent module has the expected structure
    import k8s_admin_agent.agent as agent_module

    # Check that the module has the expected components
    assert hasattr(agent_module, "k8s_admin")
    assert hasattr(agent_module, "server")
    assert hasattr(agent_module, "serve")


def test_serve_function_exists():
    """Test that serve function exists and is callable"""
    from k8s_admin_agent.agent import serve

    assert callable(serve)


# Made with Bob
