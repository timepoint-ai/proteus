"""
Flask error handlers for standardized API error responses.

Usage in app.py:
    from routes.error_handlers import register_error_handlers
    register_error_handlers(app)
"""

import logging
from flask import Flask, jsonify
from utils.api_errors import APIError, ErrorCode

logger = logging.getLogger(__name__)


def register_error_handlers(app: Flask) -> None:
    """
    Register error handlers with the Flask application.

    This should be called during app initialization to ensure
    all API errors are returned in the standard format.
    """

    @app.errorhandler(APIError)
    def handle_api_error(error: APIError):
        """Handle custom APIError exceptions."""
        logger.warning(f"API Error: {error.code} - {error.message}")
        response = {
            "success": False,
            "error": error.to_dict()
        }
        return jsonify(response), error.status

    @app.errorhandler(400)
    def handle_bad_request(error):
        """Handle 400 Bad Request errors."""
        message = str(error.description) if hasattr(error, 'description') else "Bad request"
        return jsonify({
            "success": False,
            "error": {
                "code": ErrorCode.INVALID_REQUEST,
                "message": message
            }
        }), 400

    @app.errorhandler(401)
    def handle_unauthorized(error):
        """Handle 401 Unauthorized errors."""
        message = str(error.description) if hasattr(error, 'description') else "Authentication required"
        return jsonify({
            "success": False,
            "error": {
                "code": ErrorCode.UNAUTHORIZED,
                "message": message
            }
        }), 401

    @app.errorhandler(403)
    def handle_forbidden(error):
        """Handle 403 Forbidden errors."""
        message = str(error.description) if hasattr(error, 'description') else "Permission denied"
        return jsonify({
            "success": False,
            "error": {
                "code": ErrorCode.FORBIDDEN,
                "message": message
            }
        }), 403

    @app.errorhandler(404)
    def handle_not_found(error):
        """Handle 404 Not Found errors."""
        message = str(error.description) if hasattr(error, 'description') else "Resource not found"
        return jsonify({
            "success": False,
            "error": {
                "code": ErrorCode.NOT_FOUND,
                "message": message
            }
        }), 404

    @app.errorhandler(429)
    def handle_rate_limit(error):
        """Handle 429 Too Many Requests errors."""
        message = str(error.description) if hasattr(error, 'description') else "Too many requests"
        return jsonify({
            "success": False,
            "error": {
                "code": ErrorCode.RATE_LIMITED,
                "message": message
            }
        }), 429

    @app.errorhandler(500)
    def handle_internal_error(error):
        """Handle 500 Internal Server errors."""
        # Log the actual error for debugging
        logger.error(f"Internal Server Error: {error}", exc_info=True)
        return jsonify({
            "success": False,
            "error": {
                "code": ErrorCode.INTERNAL_ERROR,
                "message": "An unexpected error occurred"
            }
        }), 500

    @app.errorhandler(503)
    def handle_service_unavailable(error):
        """Handle 503 Service Unavailable errors."""
        message = str(error.description) if hasattr(error, 'description') else "Service temporarily unavailable"
        return jsonify({
            "success": False,
            "error": {
                "code": ErrorCode.SERVICE_UNAVAILABLE,
                "message": message
            }
        }), 503

    @app.errorhandler(Exception)
    def handle_generic_exception(error):
        """Catch-all handler for unhandled exceptions."""
        # Log the full exception for debugging
        logger.exception(f"Unhandled exception: {error}")

        # Don't expose internal error details in production
        return jsonify({
            "success": False,
            "error": {
                "code": ErrorCode.INTERNAL_ERROR,
                "message": "An unexpected error occurred"
            }
        }), 500
