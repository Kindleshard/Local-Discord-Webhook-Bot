"""
Tests for the error handling utility module.
"""

import unittest
import logging
from unittest.mock import patch, MagicMock
from src.utils.error_handler import (
    APIError, 
    APIConnectionError, 
    APIAuthenticationError,
    APIRateLimitError,
    APIDataError,
    handle_api_error,
    validate_api_response,
    safe_api_call,
    log_api_call
)


class TestAPIErrorClasses(unittest.TestCase):
    """Test cases for API error classes."""
    
    def test_api_error_basic(self):
        """Test basic APIError initialization."""
        error = APIError("Test error")
        self.assertEqual(error.message, "Test error")
        self.assertIsNone(error.status_code)
        self.assertEqual(error.details, {})
        
    def test_api_error_with_status(self):
        """Test APIError with status code."""
        error = APIError("Test error", status_code=404)
        self.assertEqual(error.message, "Test error")
        self.assertEqual(error.status_code, 404)
        self.assertEqual(error.details, {})
        
    def test_api_error_with_details(self):
        """Test APIError with details."""
        error = APIError("Test error", 
                         status_code=429, 
                         details={"retry_after": 30})
        self.assertEqual(error.message, "Test error")
        self.assertEqual(error.status_code, 429)
        self.assertEqual(error.details, {"retry_after": 30})
        
    def test_api_error_subclasses(self):
        """Test APIError subclasses."""
        errors = [
            APIConnectionError("Connection error"),
            APIAuthenticationError("Auth error"),
            APIRateLimitError("Rate limit error"),
            APIDataError("Data error")
        ]
        
        for error in errors:
            self.assertIsInstance(error, APIError)


class TestHandleAPIError(unittest.TestCase):
    """Test cases for handle_api_error decorator."""
    
    def test_successful_function(self):
        """Test that decorator passes through successful function results."""
        @handle_api_error
        def successful_function():
            return "success"
        
        self.assertEqual(successful_function(), "success")
        
    def test_api_error_raised(self):
        """Test that decorator re-raises API errors."""
        @handle_api_error
        def failing_function():
            raise APIError("Test error")
        
        with self.assertRaises(APIError):
            failing_function()
            
    def test_regular_exception_wrapped(self):
        """Test that decorator wraps regular exceptions in APIError."""
        @handle_api_error
        def exception_function():
            raise ValueError("Test value error")
        
        with self.assertRaises(APIError):
            exception_function()


class TestSafeAPICall(unittest.TestCase):
    """Test cases for safe_api_call decorator."""
    
    def test_successful_function(self):
        """Test that decorator passes through successful function results."""
        @safe_api_call(fallback_value="fallback")
        def successful_function():
            return "success"
        
        self.assertEqual(successful_function(), "success")
        
    def test_fallback_on_exception(self):
        """Test that decorator returns fallback value on exception."""
        @safe_api_call(fallback_value="fallback")
        def failing_function():
            raise ValueError("Test error")
        
        self.assertEqual(failing_function(), "fallback")
        
    def test_fallback_value_types(self):
        """Test different types of fallback values."""
        # Test with list
        @safe_api_call(fallback_value=[])
        def list_function():
            raise ValueError("Test error")
        
        self.assertEqual(list_function(), [])
        
        # Test with dict
        @safe_api_call(fallback_value={})
        def dict_function():
            raise ValueError("Test error")
        
        self.assertEqual(dict_function(), {})
        
        # Test with None
        @safe_api_call(fallback_value=None)
        def none_function():
            raise ValueError("Test error")
        
        self.assertIsNone(none_function())


class TestValidateAPIResponse(unittest.TestCase):
    """Test cases for validate_api_response function."""
    
    def test_valid_response(self):
        """Test validation of valid response."""
        response = {
            "items": [1, 2, 3],
            "pageInfo": {"totalResults": 3}
        }
        
        # Should not raise exception
        result = validate_api_response(response, ["items", "pageInfo"])
        self.assertEqual(result, response)
        
    def test_invalid_response(self):
        """Test validation of invalid response."""
        response = {
            "items": [1, 2, 3],
            # Missing pageInfo
        }
        
        with self.assertRaises(APIDataError):
            validate_api_response(response, ["items", "pageInfo"])
            
    def test_custom_error_message(self):
        """Test custom error message."""
        response = {
            # Missing items
            "pageInfo": {"totalResults": 0}
        }
        
        try:
            validate_api_response(response, ["items"], "Custom error message")
        except APIDataError as e:
            self.assertTrue(e.message.startswith("Custom error message"))


class TestLogAPICall(unittest.TestCase):
    """Test cases for log_api_call function."""
    
    @patch('logging.Logger.info')
    def test_log_api_call(self, mock_info):
        """Test that API calls are logged."""
        log_api_call("youtube", "search", query="test", maxResults=10)
        
        # Check that the logger was called with the expected message
        mock_info.assert_called_once()
        log_message = mock_info.call_args[0][0]
        self.assertIn("youtube.search", log_message)
        self.assertIn("query", log_message)
        self.assertIn("maxResults", log_message)
        
    @patch('logging.Logger.info')
    def test_sensitive_parameter_filtering(self, mock_info):
        """Test that sensitive parameters are filtered."""
        log_api_call(
            "youtube", 
            "search", 
            api_key="secret123", 
            auth_token="token123",
            query="test"
        )
        
        # Check that the logger was called with the expected message
        mock_info.assert_called_once()
        log_message = mock_info.call_args[0][0]
        
        # Sensitive parameters should be filtered out
        self.assertNotIn("secret123", log_message)
        self.assertNotIn("token123", log_message)
        self.assertIn("query", log_message)


if __name__ == '__main__':
    unittest.main()
