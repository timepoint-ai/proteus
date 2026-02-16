"""
Structured logging configuration using structlog.

Provides JSON output for production and colored console output for development.
Includes request ID binding for tracing requests across log entries.
"""

import logging
import os
import sys
from typing import Any

import structlog


def get_log_level() -> int:
    """Get log level from environment variable."""
    level_name = os.environ.get("LOG_LEVEL", "INFO").upper()
    return getattr(logging, level_name, logging.INFO)


def add_app_context(
    logger: logging.Logger, method_name: str, event_dict: dict[str, Any]
) -> dict[str, Any]:
    """Add application context to log entries."""
    event_dict["app"] = "proteus"
    event_dict["environment"] = os.environ.get("FLASK_ENV", "development")
    return event_dict


def configure_structlog(json_output: bool = None) -> None:
    """
    Configure structlog for the application.

    Args:
        json_output: Force JSON output. If None, uses JSON in production,
                    colored console in development.
    """
    if json_output is None:
        json_output = os.environ.get("FLASK_ENV") == "production"

    # Shared processors for all environments
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
        add_app_context,
    ]

    if json_output:
        # Production: JSON output
        processors = shared_processors + [
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ]
    else:
        # Development: Colored console output
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer(colors=True),
        ]

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure standard logging to work with structlog
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=get_log_level(),
    )

    # Reduce noise from third-party libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("werkzeug").setLevel(logging.WARNING)
    logging.getLogger("web3").setLevel(logging.WARNING)
    logging.getLogger("celery").setLevel(logging.INFO)


def get_logger(name: str = None) -> structlog.stdlib.BoundLogger:
    """
    Get a structured logger instance.

    Args:
        name: Logger name. If None, uses the caller's module name.

    Returns:
        A structlog BoundLogger instance.

    Usage:
        from utils.logging_config import get_logger
        logger = get_logger(__name__)

        logger.info("Processing market", market_id=123, action="resolve")
        logger.error("Failed to resolve", market_id=123, error=str(e))
    """
    return structlog.get_logger(name)


def bind_request_context(**kwargs) -> None:
    """
    Bind context variables to all subsequent log entries in this request.

    Usage:
        bind_request_context(request_id="abc-123", user_id="user-456")
    """
    structlog.contextvars.bind_contextvars(**kwargs)


def clear_request_context() -> None:
    """Clear all bound context variables."""
    structlog.contextvars.clear_contextvars()
