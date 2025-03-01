"""
Error handling utilities for Discord Webhook Bot.

This module provides standardized error handling for API connectors and other components.
"""

import logging
import traceback
from typing import Dict, Any, Callable, Optional, TypeVar, Union, List

# Setup logger
logger = logging.getLogger('content_curator.utils.error_handler')

# Define a type variable for function return types
T = TypeVar('T')


class APIError(Exception):
    """Base exception for API-related errors."""
    
    def __init__(self, message: str, status_code: Optional[int] = None, 
                 details: Optional[Dict[str, Any]] = None):
        """
        Initialize APIError.
        
        Args:
            message: Error message
            status_code: HTTP status code (if applicable)
            details: Additional error details
        """
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class APIConnectionError(APIError):
    """Exception for connection errors."""
    pass


class APIAuthenticationError(APIError):
    """Exception for authentication errors."""
    pass


class APIRateLimitError(APIError):
    """Exception for rate limit errors."""
    pass


class APIDataError(APIError):
    """Exception for data-related errors."""
    pass


def handle_api_error(func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator for handling API errors.
    
    Args:
        func: Function to decorate
        
    Returns:
        Decorated function
    """
    def wrapper(*args, **kwargs) -> T:
        try:
            return func(*args, **kwargs)
        except APIError as e:
            # Already a specific API error, so just log and re-raise
            logger.error(f"API Error ({type(e).__name__}): {e.message}")
            if e.status_code:
                logger.error(f"Status Code: {e.status_code}")
            if e.details:
                logger.error(f"Details: {e.details}")
            raise
        except Exception as e:
            # Convert generic exception to APIError
            logger.error(f"Unexpected error in {func.__name__}: {str(e)}")
            logger.debug(traceback.format_exc())
            raise APIError(f"Unexpected error: {str(e)}")
    
    return wrapper


def safe_api_call(fallback_value: T) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator that ensures a function always returns a value, even if it fails.
    
    Args:
        fallback_value: Value to return if the function fails
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        def wrapper(*args, **kwargs) -> T:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error in {func.__name__}: {str(e)}")
                logger.debug(traceback.format_exc())
                return fallback_value
        
        return wrapper
    
    return decorator


def validate_api_response(
    response: Dict[str, Any], 
    required_fields: List[str],
    error_message: str = "Invalid API response"
) -> Dict[str, Any]:
    """
    Validate that an API response contains the required fields.
    
    Args:
        response: API response to validate
        required_fields: List of fields that must be present
        error_message: Message to use if validation fails
        
    Returns:
        The validated response
        
    Raises:
        APIDataError: If validation fails
    """
    missing_fields = [field for field in required_fields if field not in response]
    
    if missing_fields:
        raise APIDataError(
            f"{error_message}: Missing required fields: {', '.join(missing_fields)}",
            details={"missing_fields": missing_fields}
        )
    
    return response


def log_api_call(platform: str, method: str, **params) -> None:
    """
    Log an API call.
    
    Args:
        platform: Platform name (e.g., 'youtube', 'reddit')
        method: API method name
        **params: API call parameters
    """
    # Filter out sensitive parameters
    safe_params = {k: v for k, v in params.items() 
                  if not any(sensitive in k.lower() for sensitive in 
                           ['key', 'token', 'secret', 'password', 'auth', 'credential'])}
    
    logger.info(f"API Call: {platform}.{method}({safe_params})")
