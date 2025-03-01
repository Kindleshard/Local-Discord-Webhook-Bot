"""
Base API Connector.

Abstract base class for all API connectors.
"""

from abc import ABC, abstractmethod
import logging
import sys
import os

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.error_handler import APIError, log_api_call

logger = logging.getLogger(__name__)


class PlatformConnector(ABC):
    """Abstract base class for platform-specific API connectors."""
    
    def __init__(self, credentials):
        """
        Initialize connector with credentials.
        
        Args:
            credentials: Dictionary with credentials for the API
        """
        self.credentials = credentials
        self.platform_name = self.__class__.__name__.replace('Connector', '').lower()
        self.initialized = self._initialize()
    
    @abstractmethod
    def _initialize(self):
        """
        Initialize the connector.
        
        Returns:
            bool: True if initialization was successful, False otherwise
        """
        pass
    
    @abstractmethod
    def validate_credentials(self):
        """
        Validate the credentials.
        
        Returns:
            bool: True if credentials are valid, False otherwise
        """
        pass
    
    @abstractmethod
    def fetch(self, **kwargs):
        """
        Fetch content from the platform.
        
        Args:
            **kwargs: Platform-specific arguments
            
        Returns:
            list: List of content items
        """
        pass
    
    def log_error(self, message, exception=None):
        """
        Log an error.
        
        Args:
            message: Error message
            exception: Exception object (optional)
        """
        if exception:
            logger.error(f"{self.platform_name}: {message}: {exception}")
            # Log detailed exception info at debug level
            logger.debug(f"Exception details:", exc_info=True)
        else:
            logger.error(f"{self.platform_name}: {message}")
    
    def log_info(self, message):
        """
        Log an informational message.
        
        Args:
            message: Info message
        """
        logger.info(f"{self.platform_name}: {message}")
    
    def log_debug(self, message):
        """
        Log a debug message.
        
        Args:
            message: Debug message
        """
        logger.debug(f"{self.platform_name}: {message}")
    
    def is_initialized(self):
        """
        Check if connector is initialized.
        
        Returns:
            bool: True if initialized, False otherwise
        """
        return self.initialized
    
    def log_api_call(self, method, **params):
        """
        Log an API call.
        
        Args:
            method: API method name
            **params: API call parameters
        """
        log_api_call(self.platform_name, method, **params)
