"""
app/main.py

Purpose:
--------
FastAPI application factory and structured logging configuration.

Responsibilities:
-----------------
- Configure structured logging with request_id context.
- Create and configure the FastAPI application instance.
- Register all API routers.
- Add startup/shutdown lifecycle hooks.

This module DOES NOT:
---------------------
- Contain business logic.
- Call services or repositories directly.
- Know about graph internals.

Structured Logging:
-------------------
All loggers in the application use extra={} to attach context:

    logger.info("event", extra={
        "request_id":  "abc-123",
        "customer_id": "C001",
        "tool_used":   "create_ticket_tool",
    })

The JSON formatter (in production) converts these into structured
fields readable by log aggregators (Datadog, CloudWatch, Loki).
In development, a readable format is used instead.

Run with:
    uvicorn app.main:app --reload
"""

import logging
import sys

from fastapi import FastAPI

from app.api.routes.support import router as support_router
from app.database.init_db import init_db


# ---------------------------------------------------------------------------
# Logging Configuration
# ---------------------------------------------------------------------------

def configure_logging() -> None:
    """
    Configure application-wide structured logging.

    Development: human-readable format with request context fields.
    Production:  JSON format (switch formatter to JSON when adding a
                 log aggregator — no other code changes needed).

    The format includes %(request_id)s as an optional field — not all
    log records will have it (e.g., startup logs), so the formatter
    uses a LogRecord filter to provide a default value.
    """

    class RequestContextFilter(logging.Filter):
        """Ensure request_id and customer_id are always present in log records."""

        def filter(self, record: logging.LogRecord) -> bool:
            if not hasattr(record, "request_id"):
                record.request_id = "-"      # type: ignore[attr-defined]
            if not hasattr(record, "customer_id"):
                record.customer_id = "-"     # type: ignore[attr-defined]
            return True

    formatter = logging.Formatter(
        fmt=(
            "%(asctime)s | %(levelname)-8s | "
            "req=%(request_id)s | cust=%(customer_id)s | "
            "%(name)s | %(message)s"
        ),
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    handler.addFilter(RequestContextFilter())

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    if not root_logger.handlers:
        root_logger.addHandler(handler)

    # Silence noisy third-party loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


configure_logging()
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Application Factory
# ---------------------------------------------------------------------------

def create_app() -> FastAPI:
    application = FastAPI(
        title="Multi-Agent Customer Support Platform",
        description=(
            "A production-grade AI customer support system built with "
            "LangGraph, FastAPI, and PostgreSQL."
        ),
        version="0.1.0",
    )

    # Register routers
    application.include_router(support_router)

    @application.on_event("startup")
    def on_startup() -> None:
        logger.info("Application startup: initialising database tables.")
        init_db()
        logger.info("Application startup: complete.")

    @application.on_event("shutdown")
    def on_shutdown() -> None:
        logger.info("Application shutdown: cleanup complete.")

    return application


app = create_app()