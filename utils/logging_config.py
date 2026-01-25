# ═══════════════════════════════════════════════════════════════════════════════
# RepoGraph AI - Logging Configuration
# ═══════════════════════════════════════════════════════════════════════════════
# Structured logging setup with rich console output and JSON file logging.
# ═══════════════════════════════════════════════════════════════════════════════

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import structlog
from rich.console import Console
from rich.logging import RichHandler

console = Console()


def setup_logging(
    level: str = "INFO",
    log_format: str = "json",
    log_file: Optional[Path] = None,
) -> None:
    """
    Configure structured logging for the application.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Output format ("json" or "console")
        log_file: Optional path to log file
    """
    # Create logs directory if needed
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)

    # Configure standard logging
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(message)s",
        datefmt="[%X]",
        handlers=[
            RichHandler(
                console=console,
                rich_tracebacks=True,
                show_path=False,
            )
        ],
    )

    # Reduce noise from third-party libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    # Configure structlog
    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    if log_format == "json":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.BoundLogger:
    """
    Get a logger instance for the given name.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Configured structlog logger
    """
    return structlog.get_logger(name)


class LogContext:
    """Context manager for logging with timing."""

    def __init__(self, logger: structlog.BoundLogger, operation: str, **kwargs):
        self.logger = logger
        self.operation = operation
        self.kwargs = kwargs
        self.start_time: Optional[datetime] = None

    def __enter__(self):
        self.start_time = datetime.utcnow()
        self.logger.info(f"Starting {self.operation}", **self.kwargs)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration_ms = (datetime.utcnow() - self.start_time).total_seconds() * 1000

        if exc_type is None:
            self.logger.info(
                f"Completed {self.operation}",
                duration_ms=round(duration_ms, 2),
                **self.kwargs
            )
        else:
            self.logger.error(
                f"Failed {self.operation}",
                duration_ms=round(duration_ms, 2),
                error=str(exc_val),
                **self.kwargs
            )
        return False
