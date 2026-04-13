# Copyright 2025 © Kubernetes Admin Agent
# SPDX-License-Identifier: Apache-2.0
"""Configuration management for K8s Admin Agent"""

import os
import sys
from pathlib import Path

import yaml
from pydantic import BaseModel, Field, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict


class ServerConfig(BaseModel):
    """Server configuration"""

    host: str = Field(default="0.0.0.0", description="Server host (can be overridden by AGENT_HOST env var)")
    port: int = Field(default=8000, description="Server port")


class MCPServerConfig(BaseModel):
    """Individual MCP Server configuration"""

    url: str = Field(description="MCP Server URL")
    description: str = Field(default="", description="MCP Server description")


class MCPConfig(BaseModel):
    """MCP Servers configuration - supports multiple MCP servers"""

    kubernetes_mcp: MCPServerConfig = Field(
        default_factory=lambda: MCPServerConfig(
            url="http://k8s-mcp-server:8080",
            description="Kubernetes MCP Server for cluster operations",
        )
    )

    def get_server(self, name: str) -> MCPServerConfig | None:
        """Get MCP server configuration by name"""
        return getattr(self, name, None)

    def get_server_url(self, name: str) -> str:
        """Get MCP server URL by name"""
        server = self.get_server(name)
        return server.url if server else ""


class LogConfig(BaseModel):
    """Logging configuration"""

    level: str = Field(default="INFO", description="Log level")
    rotation: str = Field(default="10 MB", description="Log file rotation size")
    retention: str = Field(default="7 days", description="Log retention period")
    compression: str = Field(default="zip", description="Log compression format")
    console: bool = Field(default=True, description="Enable console logging")
    file: str = Field(default="logs/agent.log", description="Log file path")
    masking: bool = Field(default=True, description="Enable sensitive data masking")


class AgentConfig(BaseSettings):
    """Agent configuration loaded from config.yaml and .env"""

    server: ServerConfig = Field(default_factory=ServerConfig)
    mcp: MCPConfig = Field(default_factory=MCPConfig)
    logs: LogConfig = Field(default_factory=LogConfig)

    # Secrets from .env only
    api_key: str | None = Field(default=None, description="API Key (from .env)")
    secret_token: str | None = Field(default=None, description="Secret Token (from .env)")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @classmethod
    def load_from_yaml(cls, config_path: str = "config.yaml") -> "AgentConfig":
        """
        Load configuration from YAML file and merge with .env secrets.

        This method is called at startup and will fail fast if there are
        configuration errors. All fields have defaults, so startup should
        never fail due to missing configuration.

        Args:
            config_path: Path to the YAML configuration file

        Returns:
            AgentConfig instance with loaded configuration

        Raises:
            SystemExit: If configuration loading or validation fails
        """
        config_file = Path(config_path)
        yaml_config = {}

        # Load YAML configuration if file exists
        if config_file.exists():
            try:
                with open(config_file, "r") as f:
                    yaml_config = yaml.safe_load(f) or {}
                print(f"✓ Configuration loaded from {config_path}")
            except yaml.YAMLError as e:
                print(f"✗ ERROR: Failed to parse {config_path}: {e}", file=sys.stderr)
                sys.exit(1)
            except Exception as e:
                print(f"✗ ERROR: Failed to read {config_path}: {e}", file=sys.stderr)
                sys.exit(1)
        else:
            print(f"ℹ Configuration file {config_path} not found, using defaults")

        # Create config from YAML with validation
        try:
            instance = cls(**yaml_config)
        except ValidationError as e:
            print("✗ ERROR: Configuration validation failed:", file=sys.stderr)
            for error in e.errors():
                field = " -> ".join(str(x) for x in error["loc"])
                print(f"  - {field}: {error['msg']}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"✗ ERROR: Failed to create configuration: {e}", file=sys.stderr)
            sys.exit(1)

        # Override with environment variables for secrets
        if os.getenv("API_KEY"):
            instance.api_key = os.getenv("API_KEY")
        if os.getenv("SECRET_TOKEN"):
            instance.secret_token = os.getenv("SECRET_TOKEN")

        # Print configuration summary
        print("\n" + "=" * 60)
        print("CONFIGURATION SUMMARY")
        print("=" * 60)
        print("Server:")
        print(f"  - Host: {instance.server.host}")
        print(f"  - Port: {instance.server.port}")
        print("MCP Servers:")
        print(f"  - kubernetes_mcp: {instance.mcp.kubernetes_mcp.url}")
        print("Logging:")
        print(f"  - Level: {instance.logs.level}")
        print(f"  - File: {instance.logs.file}")
        print(f"  - Console: {instance.logs.console}")
        print(f"  - Masking: {instance.logs.masking}")
        print("=" * 60 + "\n")

        return instance


# Global config instance - loaded at module import time
# This will fail fast if there are configuration errors
try:
    config = AgentConfig.load_from_yaml()
except SystemExit:
    # Re-raise SystemExit to allow proper shutdown
    raise
except Exception as e:
    print(f"✗ FATAL: Unexpected error loading configuration: {e}", file=sys.stderr)
    sys.exit(1)

# Made with Bob
