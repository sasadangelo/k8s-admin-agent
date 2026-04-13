# Copyright 2025 © Kubernetes Admin Agent
# SPDX-License-Identifier: Apache-2.0
"""Logging setup for K8s Admin Agent"""

import re
import sys
from pathlib import Path

from loguru import logger

from k8s_admin_agent.core.config import config

# Sensitive patterns to mask
SENSITIVE_PATTERNS = [
    (re.compile(r"(password[\"']?\s*[:=]\s*[\"']?)([^\"'\s]+)", re.IGNORECASE), r"\1***MASKED***"),
    (re.compile(r"(token[\"']?\s*[:=]\s*[\"']?)([^\"'\s]+)", re.IGNORECASE), r"\1***MASKED***"),
    (re.compile(r"(api[_-]?key[\"']?\s*[:=]\s*[\"']?)([^\"'\s]+)", re.IGNORECASE), r"\1***MASKED***"),
    (re.compile(r"(secret[\"']?\s*[:=]\s*[\"']?)([^\"'\s]+)", re.IGNORECASE), r"\1***MASKED***"),
    (re.compile(r"(bearer\s+)([^\s]+)", re.IGNORECASE), r"\1***MASKED***"),
    # JWT tokens (always start with eyJ which is base64 of '{"')
    (re.compile(r"eyJ[A-Za-z0-9_-]*\.eyJ[A-Za-z0-9_-]*\.[A-Za-z0-9_-]*"), r"***JWT_TOKEN_MASKED***"),
]


def mask_sensitive_data(message: str) -> str:
    """Mask sensitive data in log messages"""
    if not config.logs.masking:
        return message

    for pattern, replacement in SENSITIVE_PATTERNS:
        message = pattern.sub(replacement, message)
    return message


# Custom format string with masking
LOG_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<yellow>{thread.name: <15}</yellow> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
    "<level>{message}</level>\n"
)


def setup_logging() -> None:
    """Setup logging configuration"""
    # Remove default logger
    logger.remove()

    # Add console handler if enabled
    if config.logs.console:
        logger.add(
            sys.stderr,
            format=LOG_FORMAT,
            level=config.logs.level,
            colorize=True,
        )

    # Add file handler
    log_path = Path(config.logs.file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logger.add(
        config.logs.file,
        format=LOG_FORMAT,
        level=config.logs.level,
        rotation=config.logs.rotation,
        retention=config.logs.retention,
        compression=config.logs.compression,
        enqueue=True,  # Thread-safe logging
    )

    logger.info("Logging initialized")
    logger.info(f"Log level: {config.logs.level}")
    logger.info(f"Log file: {config.logs.file}")
    logger.info(f"Console logging: {config.logs.console}")
    logger.info(f"Sensitive data masking: {config.logs.masking}")


# Initialize logging on module import
setup_logging()

# Made with Bob
