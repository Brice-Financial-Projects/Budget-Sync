"""Error handling utilities for API interactions."""

from typing import Dict, Any, Optional, Union
import logging

logger = logging.getLogger(__name__)


class APIError(Exception):
    """Base class for API-related errors."""
    def __init__(self, message: str, status_code: Optional[int] = None, response: Optional[Dict[str, Any]] = None):
        self.message = message
        self.status_code = status_code
        self.response = response
        super().__init__(self.message)
    
    def __str__(self) -> str:
        status_info = f" (Status: {self.status_code})" if self.status_code else ""
        return f"{self.message}{status_info}"


class AuthenticationError(APIError):
    """Error raised when authentication with the API fails."""
    pass


class RateLimitError(APIError):
    """Error raised when rate limits are exceeded."""
    def __init__(self, message: str, retry_after: Optional[Union[int, float]] = None, **kwargs):
        self.retry_after = retry_after
        super().__init__(message, **kwargs)


class ServiceUnavailableError(APIError):
    """Error raised when the API service is unavailable."""
    pass


class InputValidationError(APIError):
    """Error raised when input validation fails."""
    pass


class ResourceNotFoundError(APIError):
    """Error raised when a requested resource is not found."""
    pass


def handle_api_error(err: APIError) -> Dict[str, Any]:
    """
    Handle API errors and return a standardized error response format.
    
    Args:
        err: The API error to handle
        
    Returns:
        A dictionary with standardized error information
    """
    error_type = type(err).__name__
    
    if err.response:
        # Log detailed error information
        logger.error(f"API Error ({error_type}): {err.message}. Response: {err.response}")
    else:
        logger.error(f"API Error ({error_type}): {err.message}")
    
    error_response = {
        "error": {
            "type": error_type,
            "message": err.message,
            "status_code": err.status_code
        },
        "success": False
    }
    
    # Add retry information for rate limit errors
    if isinstance(err, RateLimitError) and err.retry_after:
        error_response["error"]["retry_after"] = err.retry_after
    
    return error_response 