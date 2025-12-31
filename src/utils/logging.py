"""
Structured Logging Setup - Configure structlog for consistent logging.

Provides a pre-configured logger instance for use throughout the application.
"""

import logging
import sys
from typing import Any

import structlog

from .config import get_settings


def setup_logging() -> None:
    """Configure structured logging for the application."""
    settings = get_settings()

    # Configure structlog
    structlog.configure(
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, settings.app_log_level.upper(), "info")
        ),
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.dev.ConsoleRenderer(
                sort_keys=False,
                colors=True,
                level_styles={
                    "debug": "dim",
                    "info": "green",
                    "warning": "yellow",
                    "error": "red",
                    "critical": "bold red",
                },
            ),
        ],
        logger_factory=structlog.PrintLoggerFactory(
            file=sys.stdout,
            ensure_ascii=False,
        ),
        cache_logger_on_first_use=True,
    )

    # Configure standard logging
    root_logger = logging.getLogger()
    handler = logging.StreamHandler(sys.stdout)
    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.stdlib.add_log_level,
            structlog.dev.ConsoleRenderer(),
        ],
    )
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)
    root_logger.setLevel(getattr(logging, settings.app_log_level.upper(), "info"))


def get_logger(name: str | None = None) -> Any:
    """
    Get a structured logger instance.

    Args:
        name: Optional logger name (defaults to calling module)

    Returns:
        Configured logger instance
    """
    return structlog.get_logger(name)


class LoggerMixin:
    """Mixin class that provides a logger property."""

    @property
    def log(self) -> Any:
        """Get logger for this instance."""
        return structlog.get_logger(self.__class__.__name__)
