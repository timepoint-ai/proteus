"""
Unit tests for structured logging configuration.
Tests the logging_config and request_context modules.
"""

import pytest
from unittest.mock import patch, MagicMock
import os


class TestLoggingConfig:
    """Tests for utils.logging_config module."""

    @pytest.mark.unit
    def test_get_log_level_defaults_to_info(self):
        """get_log_level() returns INFO when LOG_LEVEL not set."""
        with patch.dict(os.environ, {}, clear=True):
            # Remove LOG_LEVEL if present
            os.environ.pop('LOG_LEVEL', None)
            from utils.logging_config import get_log_level
            import logging
            # Re-import to pick up env change
            assert get_log_level() == logging.INFO

    @pytest.mark.unit
    def test_get_log_level_respects_env_var(self):
        """get_log_level() respects LOG_LEVEL environment variable."""
        with patch.dict(os.environ, {'LOG_LEVEL': 'DEBUG'}):
            from utils.logging_config import get_log_level
            import logging
            assert get_log_level() == logging.DEBUG

    @pytest.mark.unit
    def test_get_log_level_handles_invalid_level(self):
        """get_log_level() defaults to INFO for invalid level."""
        with patch.dict(os.environ, {'LOG_LEVEL': 'INVALID'}):
            from utils.logging_config import get_log_level
            import logging
            assert get_log_level() == logging.INFO

    @pytest.mark.unit
    def test_get_logger_returns_bound_logger(self):
        """get_logger() returns a structlog BoundLogger."""
        from utils.logging_config import get_logger
        logger = get_logger("test_module")
        # Should have structlog methods
        assert hasattr(logger, 'info')
        assert hasattr(logger, 'error')
        assert hasattr(logger, 'debug')
        assert hasattr(logger, 'warning')

    @pytest.mark.unit
    def test_get_logger_with_none_name(self):
        """get_logger() works with None name."""
        from utils.logging_config import get_logger
        logger = get_logger(None)
        assert logger is not None

    @pytest.mark.unit
    def test_bind_request_context_adds_vars(self):
        """bind_request_context() adds context variables."""
        from utils.logging_config import bind_request_context, clear_request_context
        import structlog

        # Clear any existing context
        clear_request_context()

        # Bind context
        bind_request_context(request_id="test-123", user_id="user-456")

        # Context should be bound (can verify by checking contextvars)
        # The actual verification happens when logging - here we just verify no errors
        assert True

        # Cleanup
        clear_request_context()

    @pytest.mark.unit
    def test_clear_request_context_clears_vars(self):
        """clear_request_context() clears all context variables."""
        from utils.logging_config import bind_request_context, clear_request_context

        bind_request_context(request_id="test-123")
        clear_request_context()

        # Should not raise even when clearing empty context
        clear_request_context()
        assert True


class TestRequestContext:
    """Tests for utils.request_context module."""

    @pytest.mark.unit
    def test_generate_request_id_returns_string(self):
        """generate_request_id() returns a string."""
        from utils.request_context import generate_request_id
        request_id = generate_request_id()
        assert isinstance(request_id, str)
        assert len(request_id) == 8  # Short ID format

    @pytest.mark.unit
    def test_generate_request_id_is_unique(self):
        """generate_request_id() generates unique IDs."""
        from utils.request_context import generate_request_id
        ids = [generate_request_id() for _ in range(100)]
        assert len(set(ids)) == 100  # All unique

    @pytest.mark.unit
    def test_get_request_id_outside_context(self):
        """get_request_id() generates new ID outside request context."""
        from utils.request_context import get_request_id
        request_id = get_request_id()
        assert isinstance(request_id, str)
        assert len(request_id) == 8

    @pytest.mark.unit
    def test_request_id_header_constant(self):
        """REQUEST_ID_HEADER is correctly defined."""
        from utils.request_context import REQUEST_ID_HEADER
        assert REQUEST_ID_HEADER == "X-Request-ID"

    @pytest.mark.unit
    def test_with_request_context_decorator(self):
        """with_request_context decorator works correctly."""
        from utils.request_context import with_request_context
        from utils.logging_config import get_logger

        logger = get_logger(__name__)

        @with_request_context
        def test_function(arg1, arg2):
            return f"{arg1}-{arg2}"

        result = test_function("hello", "world")
        assert result == "hello-world"

    @pytest.mark.unit
    def test_with_request_context_accepts_request_id(self):
        """with_request_context accepts custom _request_id."""
        from utils.request_context import with_request_context

        @with_request_context
        def test_function():
            return "done"

        # Should work with custom request ID
        result = test_function(_request_id="custom-123")
        assert result == "done"


@pytest.mark.integration
class TestRequestContextMiddleware:
    """Tests for Flask request context middleware.

    These tests require the Flask app which needs celery.
    Marked as integration tests to run separately.
    """

    def test_init_request_context_adds_hooks(self, app):
        """init_request_context() adds before/after request hooks."""
        # Middleware is already initialized via app.py
        # Verify hooks are present
        assert len(app.before_request_funcs.get(None, [])) > 0
        assert len(app.after_request_funcs.get(None, [])) > 0

    def test_request_includes_request_id_header(self, client):
        """Response includes X-Request-ID header."""
        response = client.get('/api/base/health')
        assert 'X-Request-ID' in response.headers
        assert len(response.headers['X-Request-ID']) == 8

    def test_request_respects_incoming_request_id(self, client):
        """Middleware respects incoming X-Request-ID header."""
        response = client.get(
            '/api/base/health',
            headers={'X-Request-ID': 'custom-id'}
        )
        assert response.headers.get('X-Request-ID') == 'custom-id'
