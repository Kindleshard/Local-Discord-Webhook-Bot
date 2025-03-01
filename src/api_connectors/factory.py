"""
Connector Factory

Creates API connectors based on platform type.
"""

import logging
from .youtube import YouTubeConnector
from .reddit import RedditConnector
from .discord import DiscordConnector

logger = logging.getLogger('content_curator.api_connectors.factory')

class ConnectorFactory:
    """Factory for creating API connectors."""
    
    @staticmethod
    def create_connector(platform, credentials):
        """
        Create a connector for the specified platform.
        
        Args:
            platform (str): Platform type (e.g., 'youtube', 'reddit')
            credentials (dict): API credentials for the platform
            
        Returns:
            PlatformConnector: An instance of the appropriate connector
        """
        if platform == 'youtube':
            return YouTubeConnector(credentials)
        elif platform == 'reddit':
            return RedditConnector(credentials)
        elif platform == 'discord':
            return DiscordConnector(credentials)
        else:
            logger.error(f"Unknown platform: {platform}")
            return None
