"""
Discord Bot Module
Handles interactions with Discord webhooks and commands
"""
import json
import logging
import requests
import time
from datetime import datetime

logger = logging.getLogger('content_curator.bot')

class DiscordBot:
    def __init__(self, config, credentials, database):
        """
        Initialize Discord bot.
        
        Args:
            config (dict): Bot configuration
            credentials (dict): Authentication credentials
            database (Database): Database instance
        """
        self.config = config
        self.credentials = credentials
        self.database = database
        
        # Initialize webhook URLs
        self.webhooks = credentials.get('discord', {}).get('webhooks', [])
        
        # If no webhooks in credentials, check config (for backwards compatibility)
        if not self.webhooks:
            self.webhooks = config.get('discord', {}).get('webhook_urls', [])
            
        self.username = config.get('discord', {}).get('username', 'Content Curator')
        self.avatar_url = config.get('discord', {}).get('avatar_url', '')
        
        # Dictionary to store API connector instances (created on demand)
        self.api_connectors = {}
        
        logger.info(f"Bot initialized with {len(self.webhooks)} webhooks")

    def run(self):
        """
        Start the bot
        This method should be called from main.py
        """
        logger.info("Bot is now running. Press Ctrl+C to stop.")
        
        # In a real application, we'd start a web server or event loop here
        # For this simplified version, we'll just keep the script running
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Bot stopped by user")
    
    def _get_api_connector(self, platform):
        """
        Get (or create) an API connector for the specified platform
        
        Args:
            platform (str): The platform to connect to (youtube, reddit, etc.)
            
        Returns:
            object: The API connector instance
        """
        if platform in self.api_connectors:
            return self.api_connectors[platform]
        
        # Import the appropriate connector based on the platform
        if platform == 'youtube':
            from src.api_connectors.youtube import YouTubeConnector
            connector = YouTubeConnector(self.credentials['youtube'])
        elif platform == 'reddit':
            from src.api_connectors.reddit import RedditConnector
            connector = RedditConnector(self.credentials['reddit'])
        elif platform == 'twitter':
            from src.api_connectors.twitter import TwitterConnector
            connector = TwitterConnector(self.credentials['twitter'])
        else:
            logger.error(f"Unknown platform: {platform}")
            return None
        
        # Store the connector for future use
        self.api_connectors[platform] = connector
        return connector
    
    def fetch_content(self, platform, **kwargs):
        """
        Fetch content from the specified platform
        
        Args:
            platform (str): The platform to fetch from (youtube, reddit, etc.)
            **kwargs: Additional arguments to pass to the connector
            
        Returns:
            list: List of content items
        """
        logger.info(f"Fetching content from {platform}")
        
        connector = self._get_api_connector(platform)
        if not connector:
            return []
        
        # Get the content from the connector
        content = connector.fetch(**kwargs)
        
        # Apply filters
        filtered_content = self._apply_filters(platform, content)
        
        # Store content in database
        self.database.store_content(platform, filtered_content)
        
        return filtered_content
    
    def _apply_filters(self, platform, content):
        """
        Apply filters to content based on configuration
        
        Args:
            platform (str): The platform the content is from
            content (list): List of content items
            
        Returns:
            list: Filtered list of content items
        """
        logger.info(f"Applying filters to {len(content)} items from {platform}")
        
        global_filters = self.config['filters']['global']
        platform_filters = self.config['filters'].get(platform, {})
        
        filtered_content = []
        for item in content:
            # Apply global filters
            if not self._passes_global_filters(item, global_filters):
                continue
                
            # Apply platform-specific filters
            if not self._passes_platform_filters(platform, item, platform_filters):
                continue
                
            filtered_content.append(item)
        
        logger.info(f"{len(filtered_content)} items passed filters")
        return filtered_content
    
    def _passes_global_filters(self, item, filters):
        """
        Check if an item passes the global filters
        
        Args:
            item (dict): Content item
            filters (dict): Global filters
            
        Returns:
            bool: True if the item passes all filters
        """
        # Check keywords to include
        if filters.get('keywords_include'):
            if not any(kw.lower() in str(item).lower() for kw in filters['keywords_include']):
                return False
        
        # Check keywords to exclude
        if filters.get('keywords_exclude'):
            if any(kw.lower() in str(item).lower() for kw in filters['keywords_exclude']):
                return False
        
        return True
    
    def _passes_platform_filters(self, platform, item, filters):
        """
        Check if an item passes the platform-specific filters
        
        Args:
            platform (str): The platform the content is from
            item (dict): Content item
            filters (dict): Platform-specific filters
            
        Returns:
            bool: True if the item passes all filters
        """
        if platform == 'youtube':
            # YouTube-specific filters
            if 'min_views' in filters and item.get('views', 0) < filters['min_views']:
                return False
            if 'min_likes' in filters and item.get('likes', 0) < filters['min_likes']:
                return False
            if 'channels' in filters and filters['channels'] and item.get('channel') not in filters['channels']:
                return False
        
        elif platform == 'reddit':
            # Reddit-specific filters
            if 'min_upvotes' in filters and item.get('upvotes', 0) < filters['min_upvotes']:
                return False
            if 'subreddits' in filters and filters['subreddits'] and item.get('subreddit') not in filters['subreddits']:
                return False
            if 'post_types' in filters and filters['post_types'] and item.get('type') not in filters['post_types']:
                return False
        
        elif platform == 'twitter':
            # Twitter-specific filters
            if 'min_likes' in filters and item.get('likes', 0) < filters['min_likes']:
                return False
            if 'min_retweets' in filters and item.get('retweets', 0) < filters['min_retweets']:
                return False
            if 'accounts' in filters and filters['accounts'] and item.get('username') not in filters['accounts']:
                return False
        
        return True
    
    def format_content(self, platform, item):
        """
        Format content for Discord using the configured template
        
        Args:
            platform (str): The platform the content is from
            item (dict): Content item
            
        Returns:
            str: Formatted content
        """
        template = self.config['formatting'].get(platform, {}).get('template', '{url}')
        
        # Replace placeholders in the template with values from the item
        message = template
        for key, value in item.items():
            message = message.replace(f"{{{key}}}", str(value))
        
        return message
    
    def send_to_discord(self, webhook_name, message, embed=None):
        """
        Send a message to a Discord webhook
        
        Args:
            webhook_name (str): Name of the webhook to send to
            message (str): Message content
            embed (dict, optional): Discord embed object
            
        Returns:
            bool: True if successful
        """
        # Find the webhook URL by name
        webhook_url = None
        for hook in self.webhooks:
            if hook['name'] == webhook_name:
                webhook_url = hook['url']
                break
        
        if not webhook_url:
            logger.error(f"Webhook '{webhook_name}' not found")
            return False
        
        # Prepare the payload
        payload = {
            'content': message,
            'username': self.username,
        }
        
        if self.avatar_url:
            payload['avatar_url'] = self.avatar_url
            
        if embed:
            payload['embeds'] = [embed]
        
        # Send the request
        try:
            response = requests.post(webhook_url, json=payload)
            response.raise_for_status()
            logger.info(f"Message sent to webhook '{webhook_name}'")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send message to webhook '{webhook_name}': {e}")
            return False

def post_to_webhook(webhook_url, content, embeds=None, username=None, avatar_url=None):
    """
    Post content to a Discord webhook
    
    Args:
        webhook_url (str): Discord webhook URL
        content (str): Message content to post
        embeds (list, optional): List of embeds to include
        username (str, optional): Override the webhook's username
        avatar_url (str, optional): Override the webhook's avatar
        
    Returns:
        requests.Response: Response from the webhook request
    """
    logger.info(f"Posting content to webhook: {webhook_url[:40]}...")
    
    payload = {
        "content": content
    }
    
    if embeds:
        payload["embeds"] = embeds
    
    if username:
        payload["username"] = username
    
    if avatar_url:
        payload["avatar_url"] = avatar_url
    
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(
            webhook_url,
            data=json.dumps(payload),
            headers=headers
        )
        
        if response.status_code == 204:
            logger.info("Successfully posted to webhook")
        else:
            logger.error(f"Failed to post to webhook: {response.status_code} - {response.text}")
        
        return response
    
    except Exception as e:
        logger.error(f"Error posting to webhook: {e}")
        raise
