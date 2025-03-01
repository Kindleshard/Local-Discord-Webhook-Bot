"""
Content Processor Module
Handles filtering, formatting, and processing of content from various platforms
"""
import re
import logging
from datetime import datetime

logger = logging.getLogger('content_curator.processor')

class ContentProcessor:
    def __init__(self, config):
        """
        Initialize the content processor
        
        Args:
            config (dict): Application configuration
        """
        self.config = config
        self.global_filters = config['filters']['global']
        self.platform_filters = config['filters']
    
    def process_content(self, platform, items):
        """
        Process content items from a platform
        
        Args:
            platform (str): The platform the content is from
            items (list): List of content items
            
        Returns:
            list: Processed content items
        """
        logger.info(f"Processing {len(items)} items from {platform}")
        
        # Apply filters
        filtered_items = self.filter_content(platform, items)
        
        # Format items for Discord
        formatted_items = [self.format_for_discord(platform, item) for item in filtered_items]
        
        return formatted_items
    
    def filter_content(self, platform, items):
        """
        Filter content based on configuration
        
        Args:
            platform (str): The platform the content is from
            items (list): List of content items
            
        Returns:
            list: Filtered list of content items
        """
        filtered_items = []
        
        for item in items:
            if self.passes_filters(platform, item):
                filtered_items.append(item)
        
        logger.info(f"{len(filtered_items)}/{len(items)} items passed filters")
        return filtered_items
    
    def passes_filters(self, platform, item):
        """
        Check if an item passes all filters
        
        Args:
            platform (str): The platform the content is from
            item (dict): Content item
            
        Returns:
            bool: True if the item passes all filters
        """
        # First apply global filters
        if not self.passes_global_filters(item):
            return False
        
        # Then apply platform-specific filters
        if not self.passes_platform_filters(platform, item):
            return False
        
        return True
    
    def passes_global_filters(self, item):
        """
        Check if an item passes global filters
        
        Args:
            item (dict): Content item
            
        Returns:
            bool: True if the item passes global filters
        """
        # Check for keywords to include
        if self.global_filters.get('keywords_include'):
            if not any(kw.lower() in self._item_to_text(item).lower() for kw in self.global_filters['keywords_include']):
                return False
        
        # Check for keywords to exclude
        if self.global_filters.get('keywords_exclude'):
            if any(kw.lower() in self._item_to_text(item).lower() for kw in self.global_filters['keywords_exclude']):
                return False
        
        # Check minimum engagement
        if self.global_filters.get('min_engagement'):
            engagement = self._calculate_engagement(item)
            if engagement < self.global_filters['min_engagement']:
                return False
        
        return True
    
    def passes_platform_filters(self, platform, item):
        """
        Check if an item passes platform-specific filters
        
        Args:
            platform (str): The platform the content is from
            item (dict): Content item
            
        Returns:
            bool: True if the item passes platform filters
        """
        # Get platform-specific filters
        filters = self.platform_filters.get(platform, {})
        
        if platform == 'youtube':
            return self._passes_youtube_filters(item, filters)
        elif platform == 'reddit':
            return self._passes_reddit_filters(item, filters)
        elif platform == 'twitter':
            return self._passes_twitter_filters(item, filters)
        
        # If platform is not recognized, pass by default
        return True
    
    def _passes_youtube_filters(self, item, filters):
        """Check if a YouTube item passes filters"""
        if 'min_views' in filters and item.get('views', 0) < filters['min_views']:
            return False
        if 'min_likes' in filters and item.get('likes', 0) < filters['min_likes']:
            return False
        if 'channels' in filters and filters['channels'] and item.get('channel') not in filters['channels']:
            return False
        return True
    
    def _passes_reddit_filters(self, item, filters):
        """Check if a Reddit item passes filters"""
        if 'min_upvotes' in filters and item.get('upvotes', 0) < filters['min_upvotes']:
            return False
        if 'subreddits' in filters and filters['subreddits'] and item.get('subreddit') not in filters['subreddits']:
            return False
        if 'post_types' in filters and filters['post_types'] and item.get('type') not in filters['post_types']:
            return False
        return True
    
    def _passes_twitter_filters(self, item, filters):
        """Check if a Twitter item passes filters"""
        if 'min_likes' in filters and item.get('likes', 0) < filters['min_likes']:
            return False
        if 'min_retweets' in filters and item.get('retweets', 0) < filters['min_retweets']:
            return False
        if 'accounts' in filters and filters['accounts'] and item.get('username') not in filters['accounts']:
            return False
        return True
    
    def _item_to_text(self, item):
        """Convert an item to text for keyword filtering"""
        text = ""
        for key, value in item.items():
            if isinstance(value, str):
                text += value + " "
        return text
    
    def _calculate_engagement(self, item):
        """Calculate engagement score for an item"""
        engagement = 0
        
        # Add up various engagement metrics
        engagement += item.get('likes', 0)
        engagement += item.get('views', 0) // 100  # Scale down views
        engagement += item.get('comments', 0) * 5  # Weight comments more
        engagement += item.get('shares', 0) * 10   # Weight shares even more
        engagement += item.get('upvotes', 0)
        engagement += item.get('retweets', 0) * 10
        
        return engagement
    
    def format_for_discord(self, platform, item):
        """
        Format a content item for Discord
        
        Args:
            platform (str): The platform the content is from
            item (dict): Content item
            
        Returns:
            dict: Formatted item with 'content' and 'embed' fields
        """
        # Get the platform-specific template
        template = self.config['formatting'].get(platform, {}).get('template', '{url}')
        
        # Format the content
        content = template
        for key, value in item.items():
            placeholder = f"{{{key}}}"
            if placeholder in content:
                content = content.replace(placeholder, str(value))
        
        # Create an embed for rich content
        embed = self._create_embed(platform, item)
        
        return {
            'platform': platform,
            'original_item': item,
            'content': content,
            'embed': embed
        }
    
    def _create_embed(self, platform, item):
        """Create a Discord embed for a content item"""
        embed = {
            'title': item.get('title', ''),
            'url': item.get('url', ''),
            'color': self._get_platform_color(platform),
            'timestamp': datetime.now().isoformat()
        }
        
        # Add author
        if 'author' in item or 'channel' in item or 'username' in item:
            embed['author'] = {
                'name': item.get('author') or item.get('channel') or item.get('username', 'Unknown')
            }
        
        # Add thumbnail
        if 'thumbnail' in item:
            embed['thumbnail'] = {'url': item['thumbnail']}
        
        # Add image
        if 'image' in item:
            embed['image'] = {'url': item['image']}
        
        # Add description
        if 'description' in item or 'content' in item or 'text' in item:
            description = item.get('description') or item.get('content') or item.get('text', '')
            # Truncate long descriptions
            if len(description) > 300:
                description = description[:297] + '...'
            embed['description'] = description
        
        # Add fields for platform-specific metadata
        fields = []
        
        if platform == 'youtube':
            if 'views' in item:
                fields.append({'name': 'Views', 'value': f"{item['views']:,}", 'inline': True})
            if 'likes' in item:
                fields.append({'name': 'Likes', 'value': f"{item['likes']:,}", 'inline': True})
            if 'duration' in item:
                fields.append({'name': 'Duration', 'value': item['duration'], 'inline': True})
        
        elif platform == 'reddit':
            if 'upvotes' in item:
                fields.append({'name': 'Upvotes', 'value': f"{item['upvotes']:,}", 'inline': True})
            if 'comments' in item:
                fields.append({'name': 'Comments', 'value': f"{item['comments']:,}", 'inline': True})
            if 'subreddit' in item:
                fields.append({'name': 'Subreddit', 'value': f"r/{item['subreddit']}", 'inline': True})
        
        elif platform == 'twitter':
            if 'likes' in item:
                fields.append({'name': 'Likes', 'value': f"{item['likes']:,}", 'inline': True})
            if 'retweets' in item:
                fields.append({'name': 'Retweets', 'value': f"{item['retweets']:,}", 'inline': True})
        
        if fields:
            embed['fields'] = fields
        
        return embed
    
    def _get_platform_color(self, platform):
        """Get color code for a platform"""
        colors = {
            'youtube': 0xFF0000,  # Red
            'reddit': 0xFF4500,   # Orange Red
            'twitter': 0x1DA1F2,  # Twitter Blue
            'instagram': 0xE1306C # Instagram Pink/Purple
        }
        return colors.get(platform, 0x7289DA)  # Default Discord color
    
    def format_content_with_template(self, item, template):
        """
        Format content with a custom template
        
        Args:
            item (dict): Content item
            template (str): Template string with {placeholders}
            
        Returns:
            str: Formatted content
        """
        # Use re.sub with a function to handle placeholders
        def replace_placeholder(match):
            field = match.group(1)
            return str(item.get(field, ''))
        
        # Replace {field} with the corresponding value or empty string if missing
        content = re.sub(r'\{(\w+)\}', replace_placeholder, template)
        return content
    
    def format_content(self, platform, item):
        """
        Format content for a specific platform using the configured template
        
        Args:
            platform (str): The platform the content is from
            item (dict): Content item
            
        Returns:
            str: Formatted content string
        """
        # Get the template for the platform
        template = self.config.get('formatting', {}).get(platform, {}).get('template', '{url}')
        
        # Use the template formatting method
        return self.format_content_with_template(item, template)
