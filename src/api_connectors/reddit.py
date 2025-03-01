"""
Reddit API Connector
Handles interactions with the Reddit API using PRAW
"""
import logging
from datetime import datetime
import praw
from .base_connector import PlatformConnector
from ..utils.error_handler import (
    APIError, 
    APIConnectionError, 
    APIAuthenticationError,
    APIRateLimitError,
    APIDataError,
    handle_api_error,
    validate_api_response,
    safe_api_call
)

logger = logging.getLogger('content_curator.api_connectors.reddit')

class RedditConnector(PlatformConnector):
    def __init__(self, credentials):
        """
        Initialize the Reddit API connector
        
        Args:
            credentials (dict): Reddit API credentials
        """
        self.client_id = credentials.get('client_id', '')
        self.client_secret = credentials.get('client_secret', '')
        self.user_agent = credentials.get('user_agent', 'Discord Content Curator Bot')
        self.reddit = None
        super().__init__(credentials)
    
    def _initialize(self):
        """
        Initialize the Reddit API client
        
        Returns:
            bool: True if initialization was successful, False otherwise
        """
        if not self.client_id or not self.client_secret:
            self.log_error("Reddit API credentials not provided")
            return False
        
        try:
            # Create Reddit API client
            self.reddit = praw.Reddit(
                client_id=self.client_id,
                client_secret=self.client_secret,
                user_agent=self.user_agent
            )
            self.log_info("Reddit API client initialized")
            return True
        except Exception as e:
            self.log_error(f"Failed to initialize Reddit API client", e)
            return False
    
    def validate_credentials(self):
        """
        Validate the Reddit API credentials
        
        Returns:
            bool: True if credentials are valid, False otherwise
        """
        if not self.client_id or not self.client_secret:
            self.log_error("Client ID and Client Secret are required")
            return False
            
        try:
            # Try to make a simple API call
            self.log_api_call("user.me")
            self.reddit.user.me()
            self.log_info("Reddit API credentials validated successfully")
            return True
        except Exception as e:
            self.log_error(f"Error validating Reddit credentials", e)
            return False
    
    @handle_api_error
    def fetch(self, subreddit=None, query=None, sort='hot', time_filter='day', limit=10):
        """
        Fetch posts from Reddit
        
        Args:
            subreddit (str, optional): Subreddit to fetch from (without 'r/')
            query (str, optional): Search query
            sort (str, optional): Sort method ('hot', 'new', 'top')
            time_filter (str, optional): Time filter for 'top' sort ('hour', 'day', 'week', 'month', 'year', 'all')
            limit (int, optional): Maximum number of results to return
            
        Returns:
            list: List of post items
            
        Raises:
            APIError: If the API request fails
        """
        if not self.reddit:
            raise APIConnectionError("Reddit API client not initialized")
        
        if subreddit:
            return self.fetch_subreddit_posts(subreddit, sort, time_filter, limit)
        elif query:
            return self.search_posts(query, limit)
        else:
            raise APIDataError("Either subreddit or query must be provided")
    
    @handle_api_error
    def fetch_subreddit_posts(self, subreddit_name, sort='hot', time_filter='day', limit=10):
        """
        Fetch posts from a specific subreddit
        
        Args:
            subreddit_name (str): Subreddit name (without 'r/')
            sort (str, optional): Sort method ('hot', 'new', 'top')
            time_filter (str, optional): Time filter for 'top' sort
            limit (int, optional): Maximum number of results to return
            
        Returns:
            list: List of post items
            
        Raises:
            APIError: If the API request fails
        """
        self.log_info(f"Fetching posts from r/{subreddit_name}")
        
        try:
            # Get subreddit
            self.log_api_call("subreddit", name=subreddit_name)
            subreddit = self.reddit.subreddit(subreddit_name)
            
            # Get posts based on sort method
            if sort == 'hot':
                self.log_api_call("subreddit.hot", limit=limit)
                posts = subreddit.hot(limit=limit)
            elif sort == 'new':
                self.log_api_call("subreddit.new", limit=limit)
                posts = subreddit.new(limit=limit)
            elif sort == 'top':
                self.log_api_call("subreddit.top", time_filter=time_filter, limit=limit)
                posts = subreddit.top(time_filter=time_filter, limit=limit)
            else:
                raise APIDataError(f"Invalid sort method: {sort}")
            
            # Process posts
            return self._process_posts(posts)
        
        except praw.exceptions.PRAWException as e:
            if "401" in str(e):
                raise APIAuthenticationError(f"Reddit authentication error: {str(e)}")
            elif "403" in str(e):
                raise APIAuthenticationError(f"Reddit permission error: {str(e)}")
            elif "429" in str(e):
                raise APIRateLimitError(f"Reddit rate limit exceeded: {str(e)}")
            elif "404" in str(e) or "Subreddit not found" in str(e):
                raise APIDataError(f"Subreddit '{subreddit_name}' not found")
            else:
                raise APIError(f"Reddit API error: {str(e)}")
        except APIError:
            # Re-raise specific API errors
            raise
        except Exception as e:
            raise APIError(f"Error fetching subreddit posts: {str(e)}")
    
    @handle_api_error
    def search_posts(self, query, limit=10):
        """
        Search for posts on Reddit
        
        Args:
            query (str): Search query
            limit (int, optional): Maximum number of results to return
            
        Returns:
            list: List of post items
            
        Raises:
            APIError: If the API request fails
        """
        self.log_info(f"Searching for posts with query: {query}")
        
        try:
            # Search for posts
            self.log_api_call("subreddit.search", query=query, limit=limit)
            posts = self.reddit.subreddit('all').search(query, limit=limit)
            
            # Process posts
            return self._process_posts(posts)
        
        except praw.exceptions.PRAWException as e:
            if "401" in str(e):
                raise APIAuthenticationError(f"Reddit authentication error: {str(e)}")
            elif "403" in str(e):
                raise APIAuthenticationError(f"Reddit permission error: {str(e)}")
            elif "429" in str(e):
                raise APIRateLimitError(f"Reddit rate limit exceeded: {str(e)}")
            else:
                raise APIError(f"Reddit API error: {str(e)}")
        except APIError:
            # Re-raise specific API errors
            raise
        except Exception as e:
            raise APIError(f"Error searching posts: {str(e)}")
    
    @handle_api_error
    def _process_posts(self, posts):
        """
        Process Reddit posts into a standardized format
        
        Args:
            posts (Iterator): Iterator of Reddit posts
            
        Returns:
            list: List of processed post items
            
        Raises:
            APIError: If processing fails
        """
        processed_posts = []
        
        try:
            for post in posts:
                try:
                    # Skip stickied posts
                    if post.stickied:
                        continue
                    
                    # Determine post type
                    post_type = self._get_post_type(post)
                    
                    # Process post
                    processed_post = {
                        "id": post.id,
                        "title": post.title,
                        "url": post.url,
                        "permalink": f"https://www.reddit.com{post.permalink}",
                        "author": post.author.name if post.author else "[deleted]",
                        "subreddit": post.subreddit.display_name,
                        "upvotes": post.score,
                        "upvote_ratio": post.upvote_ratio,
                        "comments": post.num_comments,
                        "created_at": datetime.fromtimestamp(post.created_utc).isoformat(),
                        "type": post_type,
                        "nsfw": post.over_18
                    }
                    
                    # Add post-type specific fields
                    if post_type == 'text':
                        processed_post["text"] = post.selftext[:2000] if post.selftext else ""
                    elif post_type == 'image':
                        processed_post["image"] = post.url
                    elif post_type == 'video':
                        if hasattr(post, 'media') and post.media:
                            if 'reddit_video' in post.media:
                                processed_post["video"] = post.media['reddit_video']['fallback_url']
                    
                    processed_posts.append(processed_post)
                    self.log_debug(f"Processed post: {post.id} - {post.title}")
                except Exception as e:
                    self.log_error(f"Error processing post {post.id if hasattr(post, 'id') else 'unknown'}", e)
                    # Continue with next post instead of failing completely
                    continue
            
            return processed_posts
        except Exception as e:
            raise APIError(f"Error processing posts: {str(e)}")
    
    @safe_api_call(fallback_value='link')
    def _get_post_type(self, post):
        """
        Determine the type of a Reddit post
        
        Args:
            post: Reddit post object
            
        Returns:
            str: Post type ('text', 'image', 'video', 'link', 'gallery')
        """
        # Text post
        if post.is_self:
            return 'text'
        
        # Image post
        if post.url.endswith(('.jpg', '.jpeg', '.png', '.gif')):
            return 'image'
        
        # Video post
        if hasattr(post, 'is_video') and post.is_video:
            return 'video'
        
        # Gallery post
        if hasattr(post, 'is_gallery') and post.is_gallery:
            return 'gallery'
        
        # Link post (default)
        return 'link'
