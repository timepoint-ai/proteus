"""
Standardized API error handling for Proteus Markets.

Usage:
    from utils.api_errors import error_response, success_response, APIError, ErrorCode

    # Return error response
    return error_response(ErrorCode.VALIDATION_ERROR, "Invalid market ID", status=400)

    # Return success response
    return success_response({"market": market_data})

    # Raise APIError (caught by error handlers)
    raise APIError(ErrorCode.NOT_FOUND, "Market not found", status=404)
"""

from flask import jsonify
from typing import Any, Dict, Optional, Tuple
from functools import wraps


class ErrorCode:
    """Standard error codes for API responses."""

    # Client errors (4xx)
    VALIDATION_ERROR = "VALIDATION_ERROR"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    NOT_FOUND = "NOT_FOUND"
    RATE_LIMITED = "RATE_LIMITED"
    INVALID_REQUEST = "INVALID_REQUEST"

    # Server errors (5xx)
    INTERNAL_ERROR = "INTERNAL_ERROR"
    BLOCKCHAIN_ERROR = "BLOCKCHAIN_ERROR"
    CONTRACT_ERROR = "CONTRACT_ERROR"
    RPC_ERROR = "RPC_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"

    # Auth-specific errors
    INVALID_TOKEN = "INVALID_TOKEN"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    INVALID_SIGNATURE = "INVALID_SIGNATURE"
    WALLET_ERROR = "WALLET_ERROR"

    # Market-specific errors
    MARKET_NOT_FOUND = "MARKET_NOT_FOUND"
    MARKET_ENDED = "MARKET_ENDED"
    MARKET_NOT_ENDED = "MARKET_NOT_ENDED"
    MARKET_RESOLVED = "MARKET_RESOLVED"
    INSUFFICIENT_FUNDS = "INSUFFICIENT_FUNDS"


class APIError(Exception):
    """
    Custom exception for API errors.

    Raised in route handlers and caught by Flask error handlers
    to return standardized error responses.
    """

    def __init__(
        self,
        code: str,
        message: str,
        status: int = 400,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status
        self.details = details

    def to_dict(self) -> Dict[str, Any]:
        """Convert error to response dictionary."""
        error_dict = {
            "code": self.code,
            "message": self.message
        }
        if self.details:
            error_dict["details"] = self.details
        return error_dict


def error_response(
    code: str,
    message: str,
    status: int = 400,
    details: Optional[Dict[str, Any]] = None
) -> Tuple[Any, int]:
    """
    Create a standardized error response.

    Args:
        code: Error code from ErrorCode class
        message: Human-readable error message
        status: HTTP status code (default 400)
        details: Optional additional error details

    Returns:
        Tuple of (JSON response, status code)

    Example:
        return error_response(ErrorCode.NOT_FOUND, "Market 123 not found", 404)
    """
    response = {
        "success": False,
        "error": {
            "code": code,
            "message": message
        }
    }
    if details:
        response["error"]["details"] = details

    return jsonify(response), status


def success_response(
    data: Optional[Dict[str, Any]] = None,
    message: Optional[str] = None,
    status: int = 200
) -> Tuple[Any, int]:
    """
    Create a standardized success response.

    Args:
        data: Response data dictionary
        message: Optional success message
        status: HTTP status code (default 200)

    Returns:
        Tuple of (JSON response, status code)

    Example:
        return success_response({"market": market_data}, "Market created")
    """
    response: Dict[str, Any] = {"success": True}

    if data is not None:
        response["data"] = data

    if message:
        response["message"] = message

    return jsonify(response), status


def validation_error(message: str, field: Optional[str] = None) -> Tuple[Any, int]:
    """
    Shorthand for validation error responses.

    Args:
        message: Validation error message
        field: Optional field name that failed validation

    Returns:
        Tuple of (JSON response, 400 status)
    """
    details = {"field": field} if field else None
    return error_response(ErrorCode.VALIDATION_ERROR, message, 400, details)


def not_found(resource: str, identifier: Any = None) -> Tuple[Any, int]:
    """
    Shorthand for not found error responses.

    Args:
        resource: Type of resource not found (e.g., "Market", "User")
        identifier: Optional identifier of the resource

    Returns:
        Tuple of (JSON response, 404 status)
    """
    if identifier is not None:
        message = f"{resource} {identifier} not found"
    else:
        message = f"{resource} not found"
    return error_response(ErrorCode.NOT_FOUND, message, 404)


def unauthorized(message: str = "Authentication required") -> Tuple[Any, int]:
    """
    Shorthand for unauthorized error responses.

    Returns:
        Tuple of (JSON response, 401 status)
    """
    return error_response(ErrorCode.UNAUTHORIZED, message, 401)


def forbidden(message: str = "Permission denied") -> Tuple[Any, int]:
    """
    Shorthand for forbidden error responses.

    Returns:
        Tuple of (JSON response, 403 status)
    """
    return error_response(ErrorCode.FORBIDDEN, message, 403)


def blockchain_error(message: str, details: Optional[Dict] = None) -> Tuple[Any, int]:
    """
    Shorthand for blockchain-related error responses.

    Returns:
        Tuple of (JSON response, 500 status)
    """
    return error_response(ErrorCode.BLOCKCHAIN_ERROR, message, 500, details)


def internal_error(message: str = "An unexpected error occurred") -> Tuple[Any, int]:
    """
    Shorthand for internal server error responses.

    Returns:
        Tuple of (JSON response, 500 status)
    """
    return error_response(ErrorCode.INTERNAL_ERROR, message, 500)


# Backward compatibility helpers - for gradual migration
def legacy_error(message: str, status: int = 400) -> Tuple[Any, int]:
    """
    Create a legacy-format error response for backward compatibility.

    This maintains the old format: {"error": "message"}
    Use during migration period, then replace with error_response().
    """
    return jsonify({"error": message}), status


def migrate_error_response(old_response: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert old error format to new format.

    Useful for updating existing code gradually.
    """
    if "error" in old_response and isinstance(old_response["error"], str):
        return {
            "success": False,
            "error": {
                "code": ErrorCode.INTERNAL_ERROR,
                "message": old_response["error"]
            }
        }
    return old_response
