"""
API Connectors package.

Initializes connectors for different platforms.
"""

from .youtube import YouTubeConnector
from .discord import DiscordConnector


def get_connector(platform, credentials=None):
    """
    Get the appropriate connector for the specified platform.
    
    Args:
        platform (str): Platform name (e.g., 'youtube', 'discord')
        credentials (dict, optional): Credentials for the platform
    
    Returns:
        PlatformConnector: Appropriate connector instance
    """
    platform = platform.lower()
    
    if platform == "youtube":
        return YouTubeConnector(credentials)
    elif platform == "discord":
        return DiscordConnector(credentials)
    else:
        raise ValueError(f"Unsupported platform: {platform}")
