"""
Twitter API Connector
Handles interactions with the Twitter API using Tweepy
"""
import logging
from datetime import datetime
import tweepy
from .base_connector import BaseConnector

logger = logging.getLogger('content_curator.api_connectors.twitter')

class TwitterConnector(BaseConnector):
    def __init__(self, credentials):
        """
        Initialize the Twitter API connector
        
        Args:
            credentials (dict): Twitter API credentials
        """
        super().__init__(credentials)
        self.consumer_key = credentials.get('consumer_key', '')
        self.consumer_secret = credentials.get('consumer_secret', '')
        self.access_token = credentials.get('access_token', '')
        self.access_token_secret = credentials.get('access_token_secret', '')
        self.api = None
        self._init_api()
    
    def _init_api(self):
        """Initialize the Twitter API client"""
        if not all([self.consumer_key, self.consumer_secret, self.access_token, self.access_token_secret]):
            logger.error("Twitter API credentials not provided")
            return
        
        try:
            # Create Twitter API client
            auth = tweepy.OAuth1UserHandler(
                self.consumer_key, 
                self.consumer_secret,
                self.access_token,
                self.access_token_secret
            )
            self.api = tweepy.API(auth)
            logger.info("Twitter API client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Twitter API client: {e}")
    
    def fetch(self, username=None, query=None, count=10):
        """
        Fetch tweets from Twitter
        
        Args:
            username (str, optional): Twitter username to fetch from (without '@')
            query (str, optional): Search query
            count (int, optional): Maximum number of results to return
            
        Returns:
            list: List of tweet items
        """
        if not self.api:
            logger.error("Twitter API client not initialized")
            return []
        
        if username:
            return self.fetch_user_tweets(username, count)
        elif query:
            return self.search_tweets(query, count)
        else:
            logger.error("Either username or query must be provided")
            return []
    
    def fetch_user_tweets(self, username, count=10):
        """
        Fetch tweets from a specific user
        
        Args:
            username (str): Twitter username (without '@')
            count (int, optional): Maximum number of results to return
            
        Returns:
            list: List of tweet items
        """
        logger.info(f"Fetching tweets from @{username}")
        
        try:
            # Get user timeline
            tweets = self.api.user_timeline(
                screen_name=username,
                count=count,
                tweet_mode='extended',
                include_rts=False,
                exclude_replies=True
            )
            
            # Process tweets
            return self._process_tweets(tweets)
        
        except tweepy.TweepyException as e:
            logger.error(f"Twitter API error: {e}")
            return []
        except Exception as e:
            logger.error(f"Error fetching user tweets: {e}")
            return []
    
    def search_tweets(self, query, count=10):
        """
        Search for tweets on Twitter
        
        Args:
            query (str): Search query
            count (int, optional): Maximum number of results to return
            
        Returns:
            list: List of tweet items
        """
        logger.info(f"Searching for tweets with query: {query}")
        
        try:
            # Search for tweets
            tweets = self.api.search_tweets(
                q=query,
                count=count,
                tweet_mode='extended',
                result_type='recent'
            )
            
            # Process tweets
            return self._process_tweets(tweets)
        
        except tweepy.TweepyException as e:
            logger.error(f"Twitter API error: {e}")
            return []
        except Exception as e:
            logger.error(f"Error searching tweets: {e}")
            return []
    
    def _process_tweets(self, tweets):
        """
        Process Twitter tweets into a standardized format
        
        Args:
            tweets (list): List of Twitter tweets
            
        Returns:
            list: List of processed tweet items
        """
        processed_tweets = []
        
        for tweet in tweets:
            # Extract media
            media = self._extract_media(tweet)
            
            # Process tweet
            processed_tweet = {
                "id": tweet.id_str,
                "content": tweet.full_text,
                "url": f"https://twitter.com/{tweet.user.screen_name}/status/{tweet.id_str}",
                "username": tweet.user.screen_name,
                "name": tweet.user.name,
                "created_at": tweet.created_at.isoformat(),
                "likes": tweet.favorite_count,
                "retweets": tweet.retweet_count,
                "profile_image": tweet.user.profile_image_url_https,
                "verified": tweet.user.verified
            }
            
            # Add media if available
            if media:
                processed_tweet.update(media)
            
            processed_tweets.append(processed_tweet)
        
        return processed_tweets
    
    def _extract_media(self, tweet):
        """
        Extract media from a tweet
        
        Args:
            tweet: Twitter tweet object
            
        Returns:
            dict: Media information
        """
        media = {}
        
        # Check if tweet has media
        if hasattr(tweet, 'extended_entities') and 'media' in tweet.extended_entities:
            media_entities = tweet.extended_entities['media']
            
            if media_entities:
                media_type = media_entities[0]['type']
                
                if media_type == 'photo':
                    media['image'] = media_entities[0]['media_url_https']
                elif media_type == 'video':
                    # Get the highest bitrate video
                    videos = media_entities[0]['video_info']['variants']
                    videos = [v for v in videos if 'bitrate' in v]
                    if videos:
                        videos.sort(key=lambda x: x['bitrate'], reverse=True)
                        media['video'] = videos[0]['url']
                elif media_type == 'animated_gif':
                    media['gif'] = media_entities[0]['video_info']['variants'][0]['url']
        
        return media
    
    def validate_credentials(self):
        """
        Validate the Twitter API credentials
        
        Returns:
            dict: Validation result with keys 'valid' and 'error'
        """
        if not all([self.consumer_key, self.consumer_secret, self.access_token, self.access_token_secret]):
            return {
                "valid": False,
                "error": "All Twitter credentials are required (consumer key, consumer secret, access token, access token secret)"
            }
            
        try:
            # Try to verify credentials
            if self.api:
                self.api.verify_credentials()
                return {"valid": True}
            else:
                return {
                    "valid": False,
                    "error": "API not initialized"
                }
        except Exception as e:
            logger.error(f"Error validating Twitter credentials: {e}")
            return {
                "valid": False,
                "error": str(e)
            }
