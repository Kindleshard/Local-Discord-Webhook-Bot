"""
Discord API Connector.

Handles communication with Discord webhooks.
"""

import json
import logging
import requests
from datetime import datetime
from .base_connector import PlatformConnector
from ..utils.error_handler import (
    APIError,
    APIAuthenticationError,
    APIConnectionError,
    handle_api_error
)

logger = logging.getLogger(__name__)


class DiscordConnector(PlatformConnector):
    """Discord API connector."""
    
    def __init__(self, credentials=None):
        """
        Initialize Discord connector.
        
        Args:
            credentials: Not required for Discord webhooks
        """
        super().__init__(credentials)
        logger.info("Discord connector initialized")
    
    def _initialize(self):
        """
        Initialize Discord connector.
        
        Returns:
            bool: True if initialization was successful, False otherwise
        """
        # No special initialization needed for Discord
        return True
    
    def validate_credentials(self):
        """
        Validate the credentials.
        
        Returns:
            bool: True if credentials are valid, False otherwise
        """
        # Discord webhook usage doesn't require API credentials
        # This is only used when testing specific webhook URLs
        return True
    
    def fetch(self, **kwargs):
        """
        Fetch content from Discord.
        
        Not applicable for Discord webhooks as they are outbound only.
        
        Returns:
            list: Empty list (Discord webhooks don't support fetching)
        """
        logger.warning("Discord webhooks do not support fetching content")
        return []
    
    def test_webhook(self, webhook_url):
        """
        Test a Discord webhook by sending a test message.
        
        Args:
            webhook_url: The Discord webhook URL to test
            
        Returns:
            dict: Result of the test with keys 'success' and 'error'
        """
        try:
            # Create a simple test message
            payload = {
                "content": "Test message from Discord Webhook Bot",
                "username": "Webhook Tester",
                "embeds": [{
                    "title": "Webhook Test",
                    "description": "This is a test message to verify the webhook is working correctly.",
                    "color": 3066993,  # Green color
                    "footer": {
                        "text": f"Test completed on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    }
                }]
            }
            
            # Send the test message
            response = requests.post(
                webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            # Check if the request was successful
            if response.status_code == 204:  # Discord returns 204 No Content on success
                return {"success": True}
            else:
                return {
                    "success": False, 
                    "error": f"HTTP {response.status_code}: {response.text}"
                }
                
        except Exception as e:
            logger.error(f"Error testing webhook: {str(e)}")
            return {"success": False, "error": str(e)}
    
    @handle_api_error
    def send_message(self, message, embeds=None):
        """
        Send a message to the Discord webhook.
        
        Args:
            message (str): Text content of the message
            embeds (list, optional): List of embedded rich content
            
        Returns:
            bool: True if message was sent successfully, False otherwise
            
        Raises:
            APIConnectionError: If webhook URL is not set
            APIAuthenticationError: If webhook returns authentication error
            APIError: For other API errors
        """
        if not hasattr(self, 'webhook_url') or not self.webhook_url:
            webhook_url = self.credentials.get("webhook_url")
            if not webhook_url:
                raise APIConnectionError("Discord webhook URL is not set")
            self.webhook_url = webhook_url
        
        payload = {"content": message}
        if embeds:
            payload["embeds"] = embeds
            
        try:
            response = requests.post(self.webhook_url, json=payload)
            
            # Check for HTTP error status
            if response.status_code == 401 or response.status_code == 403:
                raise APIAuthenticationError(
                    "Discord webhook authentication error", 
                    status_code=response.status_code
                )
            elif response.status_code != 204:  # Discord returns 204 No Content on success
                raise APIError(
                    f"Discord webhook error: HTTP {response.status_code}", 
                    status_code=response.status_code
                )
                
            return True
            
        except requests.exceptions.RequestException as e:
            raise APIConnectionError(f"Error connecting to Discord webhook: {str(e)}")
            
    def send_webhook_message(self, webhook_url, **kwargs):
        """
        Send a message to a Discord webhook.
        
        Args:
            webhook_url: Discord webhook URL
            **kwargs: Message parameters
                content: Text content of the message
                username: Override the default username
                avatar_url: Override the default avatar
                tts: Text-to-speech flag
                embeds: List of embedded rich content
        
        Returns:
            dict: Response data
        """
        if not webhook_url:
            raise ValueError("Webhook URL is required")
        
        logger.debug(f"Sending webhook message to {webhook_url}")
        
        payload = {}
        
        # Add message content
        if "content" in kwargs:
            payload["content"] = kwargs["content"]
        
        # Add username override
        if "username" in kwargs:
            payload["username"] = kwargs["username"]
        
        # Add avatar override
        if "avatar_url" in kwargs:
            payload["avatar_url"] = kwargs["avatar_url"]
        
        # Add TTS flag
        if "tts" in kwargs:
            payload["tts"] = kwargs["tts"]
        
        # Add embeds
        if "embeds" in kwargs:
            payload["embeds"] = kwargs["embeds"]
        
        # Log payload (excluding potential sensitive info)
        log_payload = payload.copy()
        if "embeds" in log_payload:
            log_payload["embeds"] = f"[{len(log_payload['embeds'])} embeds]"
        logger.debug(f"Webhook payload: {log_payload}")
        
        try:
            response = requests.post(webhook_url, json=payload)
            response.raise_for_status()
            
            return {
                "success": True,
                "status_code": response.status_code,
                "message": "Webhook message sent successfully"
            }
        
        except requests.exceptions.RequestException as e:
            error_message = f"Error sending webhook message: {str(e)}"
            logger.error(error_message)
            
            # Try to extract response data if available
            response_data = None
            if hasattr(e, "response") and e.response:
                try:
                    response_data = e.response.json()
                except ValueError:
                    response_data = e.response.text
            
            return {
                "success": False,
                "error": error_message,
                "response": response_data
            }
    
    def create_embed(self, **kwargs):
        """
        Create an embed object for Discord messages.
        
        Args:
            **kwargs: Embed parameters
                title: Embed title
                description: Embed description
                url: URL to be linked in the title
                timestamp: ISO8601 timestamp
                color: RGB color in decimal (integer)
                footer: Dict with text and icon_url
                image: Dict with url
                thumbnail: Dict with url
                author: Dict with name, url, and icon_url
                fields: List of field dicts with name, value, and inline
        
        Returns:
            dict: Embed object
        """
        embed = {}
        
        # Add title
        if "title" in kwargs:
            embed["title"] = kwargs["title"]
        
        # Add description
        if "description" in kwargs:
            embed["description"] = kwargs["description"]
        
        # Add URL
        if "url" in kwargs:
            embed["url"] = kwargs["url"]
        
        # Add timestamp
        if "timestamp" in kwargs:
            embed["timestamp"] = kwargs["timestamp"]
        elif kwargs.get("use_current_time", False):
            embed["timestamp"] = datetime.utcnow().isoformat()
        
        # Add color
        if "color" in kwargs:
            embed["color"] = kwargs["color"]
        
        # Add footer
        if "footer" in kwargs:
            embed["footer"] = kwargs["footer"]
        
        # Add image
        if "image" in kwargs:
            embed["image"] = kwargs["image"]
        
        # Add thumbnail
        if "thumbnail" in kwargs:
            embed["thumbnail"] = kwargs["thumbnail"]
        
        # Add author
        if "author" in kwargs:
            embed["author"] = kwargs["author"]
        
        # Add fields
        if "fields" in kwargs:
            embed["fields"] = kwargs["fields"]
        
        return embed
    
    def test_webhook(self, webhook_url):
        """
        Test a Discord webhook.
        
        Args:
            webhook_url: Discord webhook URL
        
        Returns:
            dict: Test result with success status and message
        """
        logger.info(f"Testing webhook: {webhook_url}")
        
        test_embed = self.create_embed(
            title="Webhook Test",
            description="This is a test message from the Discord Webhook Bot",
            color=3447003,  # Blue color
            use_current_time=True,
            footer={"text": "Discord Webhook Bot"}
        )
        
        # Send test message
        return self.send_webhook_message(
            webhook_url,
            content="**Webhook Test**",
            embeds=[test_embed]
        )
    
    def send_youtube_video(self, webhook_url, video, username=None, avatar_url=None):
        """
        Send a YouTube video to a Discord webhook.
        
        Args:
            webhook_url: Discord webhook URL
            video: YouTube video data
            username: Override webhook username
            avatar_url: Override webhook avatar
        
        Returns:
            dict: Response data
        """
        logger.info(f"Sending YouTube video to webhook: {webhook_url}")
        
        # Extract video data
        title = video.get("title", "Unknown Title")
        description = video.get("description", "")
        url = video.get("url", "")
        thumbnail = video.get("thumbnail", "")
        channel = video.get("channel", "Unknown Channel")
        published = video.get("published", "")
        
        # Truncate description if too long
        if len(description) > 200:
            description = description[:197] + "..."
        
        # Create embed
        embed = self.create_embed(
            title=title,
            description=description,
            url=url,
            color=16711680,  # Red color (YouTube)
            timestamp=published if published else None,
            use_current_time=not published,
            author={"name": channel},
            thumbnail={"url": thumbnail} if thumbnail else None,
            footer={"text": "YouTube"}
        )
        
        # Send message
        return self.send_webhook_message(
            webhook_url,
            content=f"New YouTube Video: {url}",
            username=username,
            avatar_url=avatar_url,
            embeds=[embed]
        )
