# Copyright 2025 © Kubernetes Admin Agent
# SPDX-License-Identifier: Apache-2.0
"""Core utilities for K8s Admin Agent"""

from k8s_admin_agent.core.config import config
from k8s_admin_agent.core.log import logger, setup_logging

__all__ = ["config", "logger", "setup_logging"]

# Made with Bob
