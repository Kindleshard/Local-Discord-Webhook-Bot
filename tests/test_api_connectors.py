"""
Tests for API connectors.
"""

import unittest
import os
import sys
import json
from unittest.mock import patch, MagicMock

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.api_connectors.factory import ConnectorFactory
from src.api_connectors.youtube import YouTubeConnector
from src.api_connectors.reddit import RedditConnector
from src.api_connectors.discord import DiscordConnector
from src.utils.error_handler import APIError, APIConnectionError, APIAuthenticationError


class TestConnectorFactory(unittest.TestCase):
    """Tests for the ConnectorFactory class."""
    
    def test_create_youtube_connector(self):
        """Test creating a YouTube connector."""
        credentials = {"api_key": "test_key"}
        connector = ConnectorFactory.create_connector("youtube", credentials)
        self.assertIsInstance(connector, YouTubeConnector)
    
    def test_create_reddit_connector(self):
        """Test creating a Reddit connector."""
        credentials = {"client_id": "test_id", "client_secret": "test_secret"}
        connector = ConnectorFactory.create_connector("reddit", credentials)
        self.assertIsInstance(connector, RedditConnector)
    
    def test_create_discord_connector(self):
        """Test creating a Discord connector."""
        credentials = {"webhook_url": "https://discord.com/api/webhooks/test"}
        connector = ConnectorFactory.create_connector("discord", credentials)
        self.assertIsInstance(connector, DiscordConnector)
    
    def test_create_unknown_connector(self):
        """Test creating an unknown connector."""
        credentials = {}
        connector = ConnectorFactory.create_connector("unknown", credentials)
        self.assertIsNone(connector)


class TestYouTubeConnector(unittest.TestCase):
    """Tests for the YouTubeConnector class."""
    
    @patch('googleapiclient.discovery.build')
    def test_search_videos(self, mock_build):
        """Test searching for videos."""
        # Set up mock YouTube API response
        mock_youtube = MagicMock()
        mock_search = MagicMock()
        mock_search_list = MagicMock()
        mock_search_list.list.return_value = mock_search
        mock_search.execute.return_value = {
            'items': [
                {
                    'id': {'videoId': 'test_video_id'},
                    'snippet': {
                        'title': 'Test Video',
                        'channelTitle': 'Test Channel',
                        'publishedAt': '2023-01-01T00:00:00Z',
                        'description': 'Test description',
                        'thumbnails': {
                            'high': {'url': 'http://example.com/thumbnail.jpg'}
                        }
                    }
                }
            ],
            'pageInfo': {
                'totalResults': 1,
                'resultsPerPage': 1
            }
        }
        
        # Set up mock for video details
        mock_videos = MagicMock()
        mock_videos_list = MagicMock()
        mock_videos_list.list.return_value = mock_videos
        mock_videos.execute.return_value = {
            'items': [
                {
                    'id': 'test_video_id',
                    'snippet': {
                        'title': 'Test Video',
                        'channelTitle': 'Test Channel',
                        'publishedAt': '2023-01-01T00:00:00Z',
                        'description': 'Test description',
                    },
                    'statistics': {
                        'viewCount': '1000',
                        'likeCount': '100',
                        'commentCount': '50'
                    },
                    'contentDetails': {
                        'duration': 'PT10M30S'
                    }
                }
            ]
        }
        
        mock_youtube.search.return_value = mock_search_list
        mock_youtube.videos.return_value = mock_videos_list
        mock_build.return_value = mock_youtube
        
        # Create connector and search for videos
        credentials = {"api_key": "test_key"}
        connector = YouTubeConnector(credentials)
        # Bypass initialization for testing
        connector.youtube = mock_youtube
        connector.initialized = True
        
        results = connector.search_videos(query="test", max_results=1)
        
        # Check results
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['title'], 'Test Video')
        self.assertEqual(results[0]['channel'], 'Test Channel')
    
    @patch('googleapiclient.discovery.build')
    def test_search_videos_api_error(self, mock_build):
        """Test error handling when searching for videos."""
        # Set up mock to raise an error
        mock_build.side_effect = Exception("API Error")
        
        # Create connector and attempt to search for videos
        credentials = {"api_key": "test_key"}
        connector = YouTubeConnector(credentials)
        
        # Ensure connector is not initialized for testing
        connector.initialized = False
        
        # Verify that APIError is raised
        with self.assertRaises(APIError):
            connector.search_videos(query="test", max_results=1)


class TestDiscordConnector(unittest.TestCase):
    """Tests for the DiscordConnector class."""
    
    @patch('requests.post')
    def test_send_message(self, mock_post):
        """Test sending a message to Discord."""
        # Set up mock response
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_post.return_value = mock_response
        
        # Create connector and send message
        webhook_url = "https://discord.com/api/webhooks/test"
        connector = DiscordConnector({"webhook_url": webhook_url})
        connector.webhook_url = webhook_url  # Set directly for testing
        connector.initialized = True
        result = connector.send_message("Test message")
        
        # Check result
        self.assertTrue(result)
        mock_post.assert_called_once()
        
        # Check JSON payload
        args, kwargs = mock_post.call_args
        self.assertEqual(kwargs['json']['content'], "Test message")
    
    @patch('requests.post')
    def test_send_message_error(self, mock_post):
        """Test error handling when sending a message."""
        # Set up mock to return error status
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_post.return_value = mock_response
        
        # Create connector and attempt to send message
        webhook_url = "https://discord.com/api/webhooks/test"
        connector = DiscordConnector({"webhook_url": webhook_url})
        connector.webhook_url = webhook_url  # Set directly for testing
        connector.initialized = True
        
        # Verify that APIError is raised
        with self.assertRaises(APIAuthenticationError):
            connector.send_message("Test message")


class TestRedditConnector(unittest.TestCase):
    """Tests for the RedditConnector class."""
    
    @patch('praw.Reddit')
    def test_search_posts(self, mock_reddit_class):
        """Test searching posts."""
        # Set up mock PRAW response
        mock_reddit = MagicMock()
        mock_reddit_class.return_value = mock_reddit
        
        # Create mock submission
        mock_submission = MagicMock()
        mock_submission.id = "test_id"
        mock_submission.title = "Test Post"
        mock_submission.url = "https://www.reddit.com/r/test/comments/123/test_post"
        mock_submission.permalink = "/r/test/comments/123/test_post"
        mock_submission.author = MagicMock()
        mock_submission.author.name = "test_user"
        mock_submission.subreddit = MagicMock()
        mock_submission.subreddit.display_name = "test"
        mock_submission.score = 1000
        mock_submission.upvote_ratio = 0.95
        mock_submission.num_comments = 50
        mock_submission.created_utc = 1609459200  # 2021-01-01 00:00:00 UTC
        mock_submission.over_18 = False
        mock_submission.is_self = True
        mock_submission.selftext = "Test content"
        mock_submission.stickied = False
        
        # Set up mock search
        mock_subreddit = MagicMock()
        mock_subreddit.search.return_value = [mock_submission]
        mock_reddit.subreddit.return_value = mock_subreddit
        
        # Create connector and search posts
        credentials = {"client_id": "test_id", "client_secret": "test_secret", "user_agent": "test"}
        connector = RedditConnector(credentials)
        connector.reddit = mock_reddit  # Set directly for testing
        connector.initialized = True
        
        results = connector.search_posts(query="test", limit=1)
        
        # Check results
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['title'], "Test Post")
        self.assertEqual(results[0]['author'], "test_user")
        self.assertEqual(results[0]['upvotes'], 1000)
        self.assertEqual(results[0]['comments'], 50)
    
    @patch('praw.Reddit')
    def test_search_posts_api_error(self, mock_reddit_class):
        """Test error handling when searching posts."""
        # Set up mock to raise an error
        mock_reddit = MagicMock()
        mock_reddit_class.return_value = mock_reddit
        mock_reddit.subreddit.side_effect = Exception("API Error")
        
        # Create connector and attempt to search posts
        credentials = {"client_id": "test_id", "client_secret": "test_secret", "user_agent": "test"}
        connector = RedditConnector(credentials)
        connector.reddit = mock_reddit  # Set directly for testing
        connector.initialized = True
        
        # Verify that APIError is raised
        with self.assertRaises(APIError):
            connector.search_posts(query="test", limit=1)


if __name__ == "__main__":
    unittest.main()
