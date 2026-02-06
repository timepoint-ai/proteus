"""
Request context middleware for Flask.

Generates a unique request ID for each request and binds it to structlog context
for distributed tracing and log correlation.
"""

import uuid
from functools import wraps

from flask import Flask, g, request

from utils.logging_config import bind_request_context, clear_request_context, get_logger

logger = get_logger(__name__)

REQUEST_ID_HEADER = "X-Request-ID"


def generate_request_id() -> str:
    """Generate a unique request ID."""
    return str(uuid.uuid4())[:8]  # Short ID for readability


def get_request_id() -> str:
    """
    Get the current request ID.

    Returns the request ID from Flask's g object, or generates a new one
    if called outside a request context.
    """
    try:
        return g.get("request_id") or generate_request_id()
    except RuntimeError:
        # Outside request context
        return generate_request_id()


def init_request_context(app: Flask) -> None:
    """
    Initialize request context middleware for a Flask app.

    This adds before/after request hooks that:
    1. Generate or extract a request ID
    2. Bind the request ID to structlog context
    3. Add the request ID to response headers
    4. Log request start/end with timing

    Args:
        app: The Flask application instance.
    """

    @app.before_request
    def before_request():
        # Get request ID from header or generate new one
        request_id = request.headers.get(REQUEST_ID_HEADER) or generate_request_id()
        g.request_id = request_id

        # Bind context for all log entries in this request
        bind_request_context(
            request_id=request_id,
            method=request.method,
            path=request.path,
            remote_addr=request.remote_addr,
        )

        # Log request start (debug level to avoid noise)
        logger.debug(
            "Request started",
            url=request.url,
            content_length=request.content_length,
        )

    @app.after_request
    def after_request(response):
        # Add request ID to response headers for client correlation
        request_id = getattr(g, "request_id", None)
        if request_id:
            response.headers[REQUEST_ID_HEADER] = request_id

        # Log request completion
        logger.debug(
            "Request completed",
            status_code=response.status_code,
            content_length=response.content_length,
        )

        return response

    @app.teardown_request
    def teardown_request(exception=None):
        # Clear context at end of request
        if exception:
            logger.error("Request failed with exception", error=str(exception))
        clear_request_context()


def with_request_context(func):
    """
    Decorator to add request context to background tasks.

    Use this for Celery tasks or other async operations that need
    their own request context for logging.

    Usage:
        @celery.task
        @with_request_context
        def my_background_task(arg1, arg2):
            logger.info("Processing in background", arg1=arg1)
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        request_id = kwargs.pop("_request_id", None) or generate_request_id()
        bind_request_context(
            request_id=request_id,
            task_name=func.__name__,
        )
        try:
            return func(*args, **kwargs)
        finally:
            clear_request_context()

    return wrapper
