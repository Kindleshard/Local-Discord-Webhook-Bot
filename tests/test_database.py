"""
Tests for the Database module.
"""

import unittest
import os
import sys
import json
import tempfile
import shutil
from datetime import datetime

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database import Database


class TestDatabase(unittest.TestCase):
    """Tests for the Database class."""
    
    def setUp(self):
        """Set up the test case."""
        # Create temporary directory for database file
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test.db")
        self.db = Database(self.db_path)
        
        # Sample content items
        self.youtube_items = [
            {
                "id": "video1",
                "title": "Test Video 1",
                "url": "https://www.youtube.com/watch?v=video1",
                "author": "Test Channel",
                "published_at": "2023-01-01T00:00:00Z"
            },
            {
                "id": "video2",
                "title": "Test Video 2",
                "url": "https://www.youtube.com/watch?v=video2",
                "author": "Test Channel",
                "published_at": "2023-01-02T00:00:00Z"
            }
        ]
        
        self.reddit_items = [
            {
                "id": "post1",
                "title": "Test Post 1",
                "url": "https://www.reddit.com/r/test/comments/post1",
                "author": "test_user1",
                "published_at": "2023-01-01T00:00:00Z",
                "subreddit": "test"
            }
        ]
    
    def tearDown(self):
        """Clean up after the test case."""
        # Close database connection
        if self.db.conn:
            self.db.conn.close()
        
        # Delete temporary directory
        shutil.rmtree(self.temp_dir)
    
    def test_store_and_retrieve_content(self):
        """Test storing and retrieving content."""
        # Store content
        stored_count = self.db.store_content("youtube", self.youtube_items)
        self.assertEqual(stored_count, 2)
        
        # Retrieve content
        items = self.db.get_content(platform="youtube", limit=10)
        self.assertEqual(len(items), 2)
        
        # Find the item with content_id "video1"
        video1_item = next((item for item in items if item["content_id"] == "video1"), None)
        self.assertIsNotNone(video1_item, "Item with content_id 'video1' not found")
        
        # Check retrieved item properties
        self.assertEqual(video1_item["platform"], "youtube")
        self.assertEqual(video1_item["content_id"], "video1")
        self.assertEqual(video1_item["title"], "Test Video 1")
        self.assertEqual(video1_item["url"], "https://www.youtube.com/watch?v=video1")
        self.assertEqual(video1_item["author"], "Test Channel")
        self.assertEqual(video1_item["posted"], False)
    
    def test_mark_as_posted(self):
        """Test marking content as posted."""
        # Store content
        self.db.store_content("youtube", self.youtube_items)
        
        # Get the first item
        items = self.db.get_content(platform="youtube", limit=1)
        item_id = items[0]["id"]
        
        # Mark as posted
        result = self.db.mark_as_posted(item_id)
        self.assertTrue(result)
        
        # Check that item is marked as posted
        items = self.db.get_content(platform="youtube", posted=True, limit=10)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["id"], item_id)
        
        # Check that it doesn't appear in non-posted items
        items = self.db.get_content(platform="youtube", posted=False, limit=10)
        self.assertEqual(len(items), 1)  # Only the second video should remain
    
    def test_store_duplicate_content(self):
        """Test storing duplicate content."""
        # Store content
        stored_count = self.db.store_content("youtube", self.youtube_items)
        self.assertEqual(stored_count, 2)
        
        # Try to store the same content again
        stored_count = self.db.store_content("youtube", self.youtube_items)
        self.assertEqual(stored_count, 0)  # No new items should be stored
    
    def test_store_multiple_platforms(self):
        """Test storing content from multiple platforms."""
        # Store YouTube content
        stored_count = self.db.store_content("youtube", self.youtube_items)
        self.assertEqual(stored_count, 2)
        
        # Store Reddit content
        stored_count = self.db.store_content("reddit", self.reddit_items)
        self.assertEqual(stored_count, 1)
        
        # Check total items
        items = self.db.get_content(limit=10)
        self.assertEqual(len(items), 3)
        
        # Check platform-specific items
        items = self.db.get_content(platform="youtube", limit=10)
        self.assertEqual(len(items), 2)
        
        items = self.db.get_content(platform="reddit", limit=10)
        self.assertEqual(len(items), 1)
    
    def test_settings(self):
        """Test saving and retrieving settings."""
        # Save setting
        result = self.db.save_setting("test_key", "test_value")
        self.assertTrue(result)
        
        # Get setting
        value = self.db.get_setting("test_key")
        self.assertEqual(value, "test_value")
        
        # Get non-existent setting
        value = self.db.get_setting("non_existent_key")
        self.assertIsNone(value)
        
        # Get setting with default
        value = self.db.get_setting("non_existent_key", default="default_value")
        self.assertEqual(value, "default_value")


if __name__ == "__main__":
    unittest.main()
