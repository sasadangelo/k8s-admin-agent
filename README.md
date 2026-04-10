# Kubernetes Admin Agent

An AI-powered Kubernetes cluster administrator built on the BeeAI framework and integrated with AgentStack platform.

## Overview

The Kubernetes Admin Agent provides intelligent cluster management capabilities through natural language interactions. It leverages the Model Context Protocol (MCP) to communicate with Kubernetes clusters, offering a conversational interface for DevOps tasks.

## Features

- **Resource Management**: List, inspect, and manage Kubernetes resources (pods, deployments, services, etc.)
- **Scaling Operations**: Scale deployments and manage replicas
- **Log Analysis**: View and analyze pod logs for debugging
- **Manifest Management**: Apply and manage YAML manifests
- **Cluster Monitoring**: Monitor cluster health and resource usage
- **Safety Features**: Confirms destructive operations before executing
- **Context-Aware**: Maintains conversation history for intelligent responses

## Architecture

```
┌─────────────────────────────────────────┐
│         AgentStack Platform             │
│  (UI, Auth, Context Store, LLM Proxy)   │
└────────────────┬────────────────────────┘
                 │
                 │ A2A Protocol
                 │
┌────────────────▼────────────────────────┐
│      Kubernetes Admin Agent             │
│                                         │
│  ┌──────────────────────────────────┐  │
│  │   BeeAI RequirementAgent         │  │
│  │   - Conversation Management      │  │
│  │   - Tool Orchestration           │  │
│  │   - Trajectory Tracking          │  │
│  └──────────────┬───────────────────┘  │
│                 │                       │
│  ┌──────────────▼───────────────────┐  │
│  │   K8sMCPTool                     │  │
│  │   - MCP Protocol Handler         │  │
│  │   - Request/Response Mapping     │  │
│  └──────────────┬───────────────────┘  │
└─────────────────┼───────────────────────┘
                  │
                  │ HTTP/MCP
                  │
┌─────────────────▼───────────────────────┐
│      Kubernetes MCP Server              │
│  - kubectl operations                   │
│  - Cluster API access                   │
└─────────────────────────────────────────┘
```

## Installation

### Prerequisites

- Python 3.14+
- UV package manager
- Access to AgentStack platform
- Kubernetes MCP Server deployed and accessible

### Setup

1. Install dependencies:
```bash
uv sync
```

2. Configure environment variables:
```bash
export MCP_SERVER_URL="http://k8s-mcp-server:8080"
export HOST="0.0.0.0"
export PORT="8000"
```

## Usage

### Testing Locally with AgentStack

Before deploying to Kubernetes, you can test the agent locally with AgentStack platform:

#### Prerequisites
1. **AgentStack platform running locally:**
   ```bash
   agentstack platform start
   ```

2. **Kubernetes MCP Server accessible via port-forward:**
   ```bash
   kubectl port-forward svc/k8s-mcp-server 8080:8080
   ```

3. **Configure `/etc/hosts` (required for macOS/Linux):**
   Add this line to `/etc/hosts`:
   ```
   127.0.0.1 host.docker.internal
   ```
   This allows AgentStack to resolve `host.docker.internal` to localhost.

#### Quick Start
Use the provided test script:
```bash
./test-local.sh
```

This script will:
- Check if AgentStack platform is running (localhost:8333)
- Verify K8s MCP Server accessibility (localhost:8080)
- Set environment variables for local testing
- Install dependencies if needed
- Start the agent server with auto-registration

#### Manual Testing
Alternatively, run manually:
```bash
# Set environment variables
export MCP_SERVER_URL="http://localhost:8080"
export HOST="127.0.0.1"
export PORT="8000"
export PLATFORM_AUTH__PUBLIC_URL="http://127.0.0.1:8000"

# Install dependencies
uv sync

# Run the server
uv run server
```

The agent will automatically register with AgentStack platform. Access the UI at **http://localhost:8334** to interact with your agent.

#### Testing with AgentStack CLI
Once the agent is running, you can test it via CLI:
```bash
# List registered agents
agentstack agent list

# Run the agent
agentstack run k8s-admin-agent "List all pods in default namespace"
```

### Running with Docker (Local Testing)

For local testing with Docker:
```bash
# Build the image
docker build -t k8s-admin-agent:latest .

# Run with localhost MCP Server (use host.docker.internal on Mac/Windows)
docker run -p 8000:8000 \
  -e MCP_SERVER_URL="http://host.docker.internal:8080" \
  -e HOST="0.0.0.0" \
  -e PORT="8000" \
  k8s-admin-agent:latest
```

**Note:** On Linux, use `--network host` instead:
```bash
docker run --network host \
  -e MCP_SERVER_URL="http://localhost:8080" \
  k8s-admin-agent:latest
```

### Deploying to AgentStack on Minikube

#### Prerequisites
- Minikube running locally
- AgentStack platform deployed on minikube
- Kubernetes MCP Server running on minikube
- AgentStack CLI installed

#### Deployment Steps

1. **Build the Docker image first:**
```bash
# Build the image
docker build -t k8s-admin-agent:latest .

# Load into minikube
minikube image load k8s-admin-agent:latest
```

2. **Deploy with AgentStack CLI:**
```bash
# Deploy using the pre-built image
agentstack add k8s-admin-agent:latest

# Or from a public Git repository
agentstack add https://github.com/your-org/k8s-admin-agent.git
```

3. **Configure environment variables:**

The agent uses these environment variables:
- `MCP_SERVER_URL`: URL of your Kubernetes MCP Server (default: http://k8s-mcp-server:8080)
- `HOST`: Server host (default: 0.0.0.0)
- `PORT`: Server port (default: 8000)

To customize, update the ConfigMap in [`k8s-deployment.yaml`](k8s-deployment.yaml) if deploying manually.

#### Verify Deployment

```bash
# Check agent status
agentstack agent list

# View agent logs
agentstack agent logs k8s-admin-agent

# Or use kubectl directly
kubectl get pods -l app=k8s-admin-agent
kubectl logs -l app=k8s-admin-agent -f
```

#### Manual Deployment (Alternative)

If you prefer manual deployment without AgentStack CLI:

1. **Use the automated script:**
```bash
./deploy.sh
```

2. **Or deploy manually:**
```bash
# Build and load image
docker build -t k8s-admin-agent:latest .
minikube image load k8s-admin-agent:latest

# Deploy to Kubernetes
kubectl apply -f k8s-deployment.yaml

# Register with AgentStack
agentstack agent register --url http://k8s-admin-agent:8000
```

## Example Interactions

### List Pods
```
User: List all pods in the default namespace
Agent: I'll list the pods for you...
[Shows pod list with status, age, and resource usage]
```

### Scale Deployment
```
User: Scale the nginx deployment to 5 replicas
Agent: I'll scale the nginx deployment to 5 replicas. This will increase
       the number of running pods. Shall I proceed?
User: Yes
Agent: Successfully scaled nginx deployment to 5 replicas.
```

### View Logs
```
User: Show me the logs from the api-server pod
Agent: I'll retrieve the logs from the api-server pod...
[Displays recent log entries]
```

### Troubleshoot Issues
```
User: What pods are failing in production?
Agent: Let me check the production namespace for failing pods...
[Analyzes pod statuses and provides diagnostic information]
```

## Configuration

### Agent Configuration

The agent can be configured through:

1. **Environment Variables**:
   - `MCP_SERVER_URL`: URL of the Kubernetes MCP Server
   - `HOST`: Server host (default: 0.0.0.0)
   - `PORT`: Server port (default: 8000)

2. **AgentStack Platform**:
   - LLM provider and model selection
   - Authentication and authorization
   - Context storage settings

### Tool Configuration

The K8sMCPTool can be customized:

```python
tools = [
    K8sMCPTool(mcp_url="http://custom-mcp-server:8080"),
]
```

## Development

### Project Structure

```
k8s-admin-agent/
├── k8s_admin_agent/
│   ├── __init__.py
│   ├── agent.py              # Main agent implementation
│   ├── helpers/
│   │   ├── __init__.py
│   │   └── trajectory.py     # Trajectory content serialization
│   └── tools/
│       ├── __init__.py
│       └── k8s_mcp_tool.py   # MCP tool wrapper
├── pyproject.toml
├── Dockerfile
└── README.md
```

### Adding New Tools

To add new Kubernetes operations:

1. Extend the K8sMCPTool or create specialized tools
2. Register tools in the agent configuration
3. Update agent instructions to include new capabilities

### Testing

```bash
uv run pytest
```

## Safety and Best Practices

The agent implements several safety features:

1. **Confirmation for Destructive Operations**: Always confirms before deleting resources or scaling to zero
2. **Impact Warnings**: Warns about potential impacts of changes
3. **Rollback Strategies**: Suggests rollback approaches for risky operations
4. **Status Verification**: Checks resource status before and after operations

## Integration with AgentStack

The agent integrates with AgentStack platform features:

- **Authentication**: Uses PlatformAuthBackend for secure access
- **Context Storage**: Leverages PlatformContextStore for conversation history
- **LLM Proxy**: Accesses LLMs through AgentStack's proxy service
- **Trajectory Tracking**: Provides detailed execution traces
- **Error Reporting**: Comprehensive error context with stack traces

## Troubleshooting

### Common Issues

1. **Cannot connect to MCP Server**
   - Verify MCP_SERVER_URL is correct
   - Check network connectivity
   - Ensure MCP Server is running

2. **Authentication failures**
   - Verify AgentStack credentials
   - Check token expiration
   - Review RBAC permissions

3. **Tool execution errors**
   - Check Kubernetes cluster connectivity
   - Verify kubectl permissions
   - Review MCP Server logs

## Contributing

Contributions are welcome! Please follow these guidelines:

1. Follow the existing code structure and patterns
2. Add tests for new features
3. Update documentation
4. Follow BeeAI framework conventions
5. Ensure code passes linting (ruff)

## License

Apache 2.0

## Support

For issues and questions:
- Check the troubleshooting guide
- Review AgentStack documentation
- Open an issue in the repository

## Acknowledgments

Built with:
- [BeeAI Framework](https://github.com/i-am-bee/beeai-framework)
- [AgentStack Platform](https://github.com/i-am-bee/agentstack)
- Model Context Protocol (MCP)