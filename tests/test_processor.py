"""
Tests for the Processor module.
"""

import unittest
import os
import sys
import json
from unittest.mock import patch, MagicMock

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.processor import ContentProcessor


class TestContentProcessor(unittest.TestCase):
    """Tests for the ContentProcessor class."""
    
    def setUp(self):
        """Set up the test case."""
        # Sample config
        self.config = {
            "filters": {
                "global": {
                    "min_engagement": 100,
                    "keywords_include": ["test", "example"],
                    "keywords_exclude": ["ignore", "skip"]
                },
                "youtube": {
                    "min_views": 1000,
                    "min_likes": 100,
                    "channels": ["Test Channel"]
                },
                "reddit": {
                    "min_upvotes": 500,
                    "subreddits": ["test"],
                    "post_types": ["image", "link", "text"]
                }
            },
            "formatting": {
                "youtube": {
                    "template": "**New Video from {channel}**\n\n{title}\n\n{views} views | {likes} likes\n\n{url}"
                },
                "reddit": {
                    "template": "**From r/{subreddit}**\n\n{title}\n\n{upvotes} upvotes | {comments} comments\n\n{url}"
                }
            }
        }
        
        # Create processor
        self.processor = ContentProcessor(self.config)
        
        # Sample content items
        self.youtube_items = [
            {
                "id": "video1",
                "title": "Test Video that should pass",
                "url": "https://www.youtube.com/watch?v=video1",
                "channel": "Test Channel",
                "views": 5000,
                "likes": 200,
                "description": "This is a test video"
            },
            {
                "id": "video2",
                "title": "Video with ignore keyword",
                "url": "https://www.youtube.com/watch?v=video2",
                "channel": "Test Channel",
                "views": 5000,
                "likes": 200,
                "description": "This video should be ignored"
            },
            {
                "id": "video3",
                "title": "Low engagement video",
                "url": "https://www.youtube.com/watch?v=video3",
                "channel": "Test Channel",
                "views": 500,
                "likes": 50,
                "description": "This video has low engagement"
            },
            {
                "id": "video4",
                "title": "Video from wrong channel",
                "url": "https://www.youtube.com/watch?v=video4",
                "channel": "Another Channel",
                "views": 5000,
                "likes": 200,
                "description": "This video is from another channel"
            }
        ]
        
        self.reddit_items = [
            {
                "id": "post1",
                "title": "Test Post that should pass",
                "url": "https://www.reddit.com/r/test/comments/post1",
                "author": "test_user1",
                "subreddit": "test",
                "upvotes": 1000,
                "comments": 50,
                "type": "image"
            },
            {
                "id": "post2",
                "title": "Post with skip keyword",
                "url": "https://www.reddit.com/r/test/comments/post2",
                "author": "test_user2",
                "subreddit": "test",
                "upvotes": 1000,
                "comments": 50,
                "type": "image"
            },
            {
                "id": "post3",
                "title": "Low engagement post",
                "url": "https://www.reddit.com/r/test/comments/post3",
                "author": "test_user3",
                "subreddit": "test",
                "upvotes": 300,
                "comments": 20,
                "type": "image"
            },
            {
                "id": "post4",
                "title": "Post from wrong subreddit",
                "url": "https://www.reddit.com/r/other/comments/post4",
                "author": "test_user4",
                "subreddit": "other",
                "upvotes": 1000,
                "comments": 50,
                "type": "image"
            }
        ]
    
    def test_filter_youtube_content(self):
        """Test filtering YouTube content."""
        filtered_items = self.processor.filter_content("youtube", self.youtube_items)
        self.assertEqual(len(filtered_items), 1)
        self.assertEqual(filtered_items[0]["id"], "video1")
    
    def test_filter_reddit_content(self):
        """Test filtering Reddit content."""
        filtered_items = self.processor.filter_content("reddit", self.reddit_items)
        self.assertEqual(len(filtered_items), 1)
        self.assertEqual(filtered_items[0]["id"], "post1")
    
    def test_format_youtube_content(self):
        """Test formatting YouTube content."""
        item = self.youtube_items[0]
        formatted = self.processor.format_content("youtube", item)
        expected = "**New Video from Test Channel**\n\nTest Video that should pass\n\n5000 views | 200 likes\n\nhttps://www.youtube.com/watch?v=video1"
        self.assertEqual(formatted, expected)
    
    def test_format_reddit_content(self):
        """Test formatting Reddit content."""
        item = self.reddit_items[0]
        formatted = self.processor.format_content("reddit", item)
        expected = "**From r/test**\n\nTest Post that should pass\n\n1000 upvotes | 50 comments\n\nhttps://www.reddit.com/r/test/comments/post1"
        self.assertEqual(formatted, expected)
    
    def test_global_keyword_filter(self):
        """Test global keyword filtering."""
        # Create processor with specific test config
        test_config = {
            "filters": {
                "global": {
                    "keywords_include": ["test", "example"],
                    "keywords_exclude": ["ignore", "skip"],
                    "min_engagement": 0  # Set to 0 to not filter on engagement
                }
            }
        }
        processor = ContentProcessor(test_config)
        
        # Create test items
        items = [
            {"id": "1", "title": "Test content", "description": "This should pass"},
            {"id": "2", "title": "No keywords", "description": "This should not pass"},
            {"id": "3", "title": "Example content", "description": "This should pass"},
            {"id": "4", "title": "Content to ignore", "description": "This should not pass"},
            {"id": "5", "title": "Content to skip", "description": "This should not pass"}
        ]
        
        # Apply global filters manually
        filtered = [item for item in items if processor.passes_global_filters(item)]
        self.assertEqual(len(filtered), 2)
        self.assertEqual(filtered[0]["id"], "1")
        self.assertEqual(filtered[1]["id"], "3")
    
    def test_custom_formatting(self):
        """Test custom content formatting."""
        # Create custom template
        custom_template = "CUSTOM: {title} by {channel} ({views} views)"
        
        # Format with custom template
        item = self.youtube_items[0]
        formatted = self.processor.format_content_with_template(item, custom_template)
        expected = "CUSTOM: Test Video that should pass by Test Channel (5000 views)"
        self.assertEqual(formatted, expected)
    
    def test_missing_format_field(self):
        """Test formatting with missing fields."""
        # Create template with missing field
        template = "{title} by {channel} with {missing_field}"
        
        # Format with missing field
        item = self.youtube_items[0]
        formatted = self.processor.format_content_with_template(item, template)
        expected = "Test Video that should pass by Test Channel with "
        self.assertEqual(formatted, expected)


if __name__ == "__main__":
    unittest.main()
