"""
YouTube API Connector Module.

This module provides functionality to interact with the YouTube API.
"""

import googleapiclient.discovery
import googleapiclient.errors
import logging
import re
import json
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

logger = logging.getLogger(__name__)


class YouTubeConnector(PlatformConnector):
    """
    YouTube API connector class.
    
    Handles interactions with the YouTube API.
    """
    
    def __init__(self, credentials):
        """
        Initialize YouTube connector.
        
        Args:
            credentials (dict): Dictionary containing 'api_key' for YouTube API authentication
        """
        self.youtube = None
        super().__init__(credentials)
    
    def _initialize(self):
        """
        Initialize YouTube API client.
        
        Returns:
            bool: True if initialization was successful, False otherwise
        """
        api_key = self.credentials.get("api_key")
        if not api_key:
            self.log_error("YouTube API key not provided")
            return False
        
        try:
            self.youtube = googleapiclient.discovery.build(
                "youtube", "v3", developerKey=api_key
            )
            self.log_info("YouTube API client initialized successfully")
            return True
        except Exception as e:
            self.log_error("Failed to initialize YouTube API client", e)
            return False
    
    def validate_credentials(self):
        """
        Validate the credentials.
        
        Returns:
            bool: True if credentials are valid, False otherwise
        """
        if not self.credentials or not self.credentials.get("api_key"):
            self.log_error("YouTube API key not provided")
            return False
        
        try:
            # Try a simple search to validate API key
            self.log_api_call("search.list", part="id", q="test", maxResults=1)
            search_response = self.youtube.search().list(
                part="id",
                q="test",
                maxResults=1
            ).execute()
            
            self.log_info("YouTube API credentials validated successfully")
            return True
        except googleapiclient.errors.HttpError as e:
            error_details = {}
            status_code = None
            
            if hasattr(e, 'resp') and hasattr(e.resp, 'status'):
                status_code = e.resp.status
                
                if status_code == 400:
                    self.log_error("YouTube API request error (invalid request)", e)
                    raise APIDataError("Invalid request to YouTube API", status_code=status_code)
                elif status_code == 401:
                    self.log_error("YouTube API authentication error (invalid API key)", e)
                    raise APIAuthenticationError("Invalid YouTube API key", status_code=status_code)
                elif status_code == 403:
                    self.log_error("YouTube API permission error (quota exceeded or API key restrictions)", e)
                    raise APIAuthenticationError("YouTube API permission error", status_code=status_code)
                elif status_code == 429:
                    self.log_error("YouTube API rate limit exceeded", e)
                    raise APIRateLimitError("YouTube API rate limit exceeded", status_code=status_code)
                else:
                    self.log_error(f"YouTube API HTTP error (status {status_code})", e)
            
            self.log_error("YouTube API credentials validation failed", e)
            return False
        except Exception as e:
            self.log_error("YouTube API credentials validation failed", e)
            return False
    
    @handle_api_error
    def fetch(self, channel_id=None, query=None, max_results=10, order="relevance", language=None, exclude_languages=None):
        """
        Fetch videos from YouTube
        
        Args:
            channel_id (str, optional): YouTube channel ID to fetch from
            query (str, optional): Search query
            max_results (int, optional): Maximum number of results to return
            order (str, optional): Order of results (relevance, date, rating, viewCount, title)
            language (str, optional): Language code to filter results
            exclude_languages (list, optional): List of language codes to exclude from results
            
        Returns:
            list: List of video items
            
        Raises:
            APIError: If the API request fails
        """
        self.log_info(f"Fetching videos from YouTube with channel_id: {channel_id}, query: {query}, exclude_languages: {exclude_languages}")
        
        if channel_id:
            return self.fetch_channel_videos(channel_id, max_results, order, exclude_languages)
        elif query:
            return self.search_videos(query, max_results, order, language, exclude_languages)
        else:
            raise APIError("Either channel_id or query must be provided")
    
    @handle_api_error
    def fetch_channel_videos(self, channel_id, max_results=10, order="date", exclude_languages=None):
        """
        Fetch videos from a specific channel
        
        Args:
            channel_id (str): YouTube channel ID
            max_results (int, optional): Maximum number of results to return
            order (str, optional): Order of results (date, rating, title, videoCount)
            exclude_languages (list, optional): List of language codes to exclude from results
            
        Returns:
            list: List of video items
            
        Raises:
            APIError: If the API request fails
        """
        self.log_info(f"Fetching videos from channel {channel_id}, max_results: {max_results}, order: {order}, exclude_languages: {exclude_languages}")
        
        if not self.youtube:
            raise APIConnectionError("YouTube API client not initialized")
        
        try:
            # First approach: Try searching for videos from the channel directly
            self.log_info(f"Searching for videos from channel: {channel_id}")
            self.log_api_call("search.list", part="snippet", channelId=channel_id, 
                              type="video", maxResults=max_results, order=order)
            
            search_response = self.youtube.search().list(
                part="snippet",
                channelId=channel_id,
                type="video",
                maxResults=max_results,
                order=order
            ).execute()
            
            # Validate response
            validate_api_response(search_response, ['items', 'pageInfo'], 
                                 "Invalid YouTube channel search response")
            
            # Extract video information
            videos = []
            for item in search_response.get("items", []):
                try:
                    video_id = item["id"]["videoId"]
                    title = item["snippet"]["title"]
                    channel_title = item["snippet"]["channelTitle"]
                    publish_time = item["snippet"]["publishedAt"]
                    thumbnail = item["snippet"]["thumbnails"]["high"]["url"]
                    
                    # Create video URL
                    url = f"https://www.youtube.com/watch?v={video_id}"
                    
                    # Add video to list
                    videos.append({
                        "id": video_id,
                        "title": title,
                        "channel": channel_title,
                        "published": publish_time,
                        "thumbnail": thumbnail,
                        "url": url
                    })
                    self.log_info(f"Added channel video to results: {title} ({video_id})")
                except KeyError as e:
                    self.log_error(f"Error extracting channel video data: {e}, item: {item}")
                    # Continue with next video instead of failing completely
                    continue
            
            # Get additional information for each video
            if videos:
                video_ids = [video["id"] for video in videos]
                self.log_info(f"Getting details for {len(video_ids)} channel videos")
                details = self._get_videos_details(video_ids)
                
                # Add additional information to videos
                for i, video in enumerate(videos):
                    if i < len(details):
                        video.update(details[i])
            
            # Filter out excluded languages
            if exclude_languages:
                videos = self._filter_excluded_languages(videos, exclude_languages)
            
            self.log_info(f"Returning {len(videos)} channel video results")
            return videos
        
        except googleapiclient.errors.HttpError as e:
            status_code = None
            if hasattr(e, 'resp') and hasattr(e.resp, 'status'):
                status_code = e.resp.status
                
            if status_code == 401:
                raise APIAuthenticationError("YouTube API authentication error", status_code=status_code)
            elif status_code == 403:
                raise APIAuthenticationError("YouTube API permission error", status_code=status_code)
            elif status_code == 429:
                raise APIRateLimitError("YouTube API rate limit exceeded", status_code=status_code)
            else:
                raise APIError(f"YouTube API error when fetching channel videos: {str(e)}", status_code=status_code)
        except APIError:
            # Re-raise specific API errors
            raise
        except Exception as e:
            raise APIError(f"Error fetching channel videos: {str(e)}")
    
    @handle_api_error
    def search_videos(self, query, max_results=10, order="relevance", language=None, exclude_languages=None):
        """
        Search for videos on YouTube
        
        Args:
            query (str): Search query
            max_results (int, optional): Maximum number of results to return
            order (str, optional): Order of results (relevance, date, rating, viewCount, title)
            language (str, optional): Language code to filter results (e.g., "en", "es", "fr")
            exclude_languages (list, optional): List of language codes to exclude from results
            
        Returns:
            list: List of video items
            
        Raises:
            APIError: If the API request fails
        """
        self.log_info(f"Searching for videos with query: {query}, order: {order}, max_results: {max_results}, language: {language}, exclude_languages: {exclude_languages}")
        
        if not self.youtube:
            raise APIConnectionError("YouTube API client not initialized")
        
        try:
            # Search for videos
            self.log_info(f"Making YouTube API search request with query: {query}")
            
            # Base parameters
            params = {
                "part": "snippet",
                "q": query,
                "type": "video",
                "maxResults": max_results,
                "order": order
            }
            
            # Add language filter if specified
            if language:
                params["relevanceLanguage"] = language
                self.log_info(f"Filtering results by language: {language}")
            
            # Add exclude languages filter if specified
            if exclude_languages:
                params["videoCaption"] = "none"
                self.log_info(f"Excluding languages: {exclude_languages}")
            
            self.log_api_call("search.list", **params)
            
            search_response = self.youtube.search().list(**params).execute()
            
            # Validate response
            validate_api_response(search_response, ['items', 'pageInfo'], 
                                 "Invalid YouTube search response")
            
            # Log search response
            item_count = len(search_response.get("items", []))
            self.log_info(f"Received {item_count} search results from YouTube API")
            
            # Extract video information
            videos = []
            for item in search_response.get("items", []):
                try:
                    video_id = item["id"]["videoId"]
                    title = item["snippet"]["title"]
                    channel_title = item["snippet"]["channelTitle"]
                    publish_time = item["snippet"]["publishedAt"]
                    thumbnail = item["snippet"]["thumbnails"]["high"]["url"]
                    
                    # Create video URL
                    url = f"https://www.youtube.com/watch?v={video_id}"
                    
                    # Add video to list
                    videos.append({
                        "id": video_id,
                        "title": title,
                        "channel": channel_title,
                        "published": publish_time,
                        "thumbnail": thumbnail,
                        "url": url
                    })
                    self.log_debug(f"Added video to results: {title} ({video_id})")
                except KeyError as e:
                    self.log_error(f"Error extracting video data: {e}, item: {item}")
                    # Continue with next video instead of failing completely
                    continue
            
            # Get additional information for each video
            if videos:
                video_ids = [video["id"] for video in videos]
                self.log_info(f"Getting details for {len(video_ids)} videos")
                details = self._get_videos_details(video_ids)
                
                # Add additional information to videos
                for i, video in enumerate(videos):
                    if i < len(details):
                        video.update(details[i])
            
            # Filter out excluded languages
            if exclude_languages:
                videos = self._filter_excluded_languages(videos, exclude_languages)
            
            self.log_info(f"Returning {len(videos)} video results")
            return videos
        
        except googleapiclient.errors.HttpError as e:
            status_code = None
            if hasattr(e, 'resp') and hasattr(e.resp, 'status'):
                status_code = e.resp.status
                
            if status_code == 401:
                raise APIAuthenticationError("YouTube API authentication error", status_code=status_code)
            elif status_code == 403:
                raise APIAuthenticationError("YouTube API permission error", status_code=status_code)
            elif status_code == 429:
                raise APIRateLimitError("YouTube API rate limit exceeded", status_code=status_code)
            else:
                raise APIError(f"YouTube API error: {str(e)}", status_code=status_code)
        except APIError:
            # Re-raise specific API errors
            raise
        except Exception as e:
            raise APIError(f"Error searching videos: {str(e)}")
    
    @handle_api_error
    def search_by_topic(self, topic_id, max_results=10, order="relevance", language=None, exclude_languages=None):
        """
        Search videos by topic ID
        
        Args:
            topic_id (str): Topic ID to search for
            max_results (int, optional): Maximum number of results to return
            order (str, optional): Order of results (relevance, date, rating, viewCount, title)
            language (str, optional): Language code to filter results
            exclude_languages (list, optional): List of language codes to exclude from results
            
        Returns:
            list: List of video items
            
        Raises:
            APIError: If the API request fails
        """
        self.log_info(f"Searching videos by topic ID: {topic_id}, exclude_languages: {exclude_languages}")
        
        if not self.youtube:
            raise APIConnectionError("YouTube API client not initialized")
        
        try:
            # Search videos by topic ID
            params = {
                "part": "snippet",
                "topicId": topic_id,
                "type": "video",
                "maxResults": max_results,
                "order": order
            }
            
            # Add language filter if specified
            if language:
                params["relevanceLanguage"] = language
                self.log_info(f"Filtering results by language: {language}")
                
            self.log_api_call("search.list", **params)
            
            search_response = self.youtube.search().list(**params).execute()
            
            # Validate response
            validate_api_response(search_response, ['items', 'pageInfo'], 
                                 "Invalid YouTube topic search response")
            
            # Extract video information
            videos = []
            for item in search_response.get("items", []):
                try:
                    video_id = item["id"]["videoId"]
                    title = item["snippet"]["title"]
                    channel_title = item["snippet"]["channelTitle"]
                    publish_time = item["snippet"]["publishedAt"]
                    thumbnail = item["snippet"]["thumbnails"]["high"]["url"]
                    
                    # Create video URL
                    url = f"https://www.youtube.com/watch?v={video_id}"
                    
                    # Add video to list
                    videos.append({
                        "id": video_id,
                        "title": title,
                        "channel": channel_title,
                        "published": publish_time,
                        "thumbnail": thumbnail,
                        "url": url
                    })
                except KeyError as e:
                    self.log_error(f"Error extracting topic video data: {e}")
                    continue
            
            # Get additional information for each video
            if videos:
                video_ids = [video["id"] for video in videos]
                details = self._get_videos_details(video_ids)
                
                # Add additional information to videos
                for i, video in enumerate(videos):
                    if i < len(details):
                        video.update(details[i])
            
            # Filter out excluded languages
            if exclude_languages:
                videos = self._filter_excluded_languages(videos, exclude_languages)
            
            return videos
            
        except googleapiclient.errors.HttpError as e:
            status_code = None
            if hasattr(e, 'resp') and hasattr(e.resp, 'status'):
                status_code = e.resp.status
                
            if status_code == 401:
                raise APIAuthenticationError("YouTube API authentication error", status_code=status_code)
            elif status_code == 403:
                raise APIAuthenticationError("YouTube API permission error", status_code=status_code)
            elif status_code == 429:
                raise APIRateLimitError("YouTube API rate limit exceeded", status_code=status_code)
            else:
                raise APIError(f"YouTube API error: {str(e)}", status_code=status_code)
        except APIError:
            # Re-raise specific API errors
            raise
        except Exception as e:
            raise APIError(f"Error searching videos by topic: {str(e)}")
    
    @handle_api_error
    def _get_videos_details(self, video_ids):
        """
        Get detailed information for a list of video IDs
        
        Args:
            video_ids (list): List of video IDs
            
        Returns:
            list: List of video items with detailed information
            
        Raises:
            APIError: If the API request fails
        """
        if not video_ids:
            return []
        
        try:
            # Get video details
            self.log_api_call("videos.list", part="snippet,contentDetails,statistics", 
                              id=",".join(video_ids))
            
            videos_response = self.youtube.videos().list(
                part="snippet,contentDetails,statistics",
                id=",".join(video_ids)
            ).execute()
            
            # Validate response
            validate_api_response(videos_response, ['items'], 
                                 "Invalid YouTube videos details response")
            
            videos = []
            for item in videos_response.get("items", []):
                try:
                    video = {
                        "id": item["id"],
                        "title": item["snippet"]["title"],
                        "description": item["snippet"]["description"],
                        "url": f"https://www.youtube.com/watch?v={item['id']}",
                        "thumbnail": item["snippet"]["thumbnails"]["high"]["url"],
                        "channel": item["snippet"]["channelTitle"],
                        "channel_id": item["snippet"]["channelId"],
                        "published_at": item["snippet"]["publishedAt"],
                        "views": int(item["statistics"].get("viewCount", 0)),
                        "likes": int(item["statistics"].get("likeCount", 0)),
                        "comments": int(item["statistics"].get("commentCount", 0)),
                        "duration": self._parse_duration(item["contentDetails"]["duration"])
                    }
                    videos.append(video)
                except KeyError as e:
                    self.log_error(f"Error extracting video details: {e}, item: {item}")
                    continue
            
            return videos
        
        except googleapiclient.errors.HttpError as e:
            status_code = None
            if hasattr(e, 'resp') and hasattr(e.resp, 'status'):
                status_code = e.resp.status
                
            raise APIError(f"YouTube API error: {str(e)}", status_code=status_code)
        except Exception as e:
            raise APIError(f"Error getting video details: {str(e)}")
    
    def _filter_excluded_languages(self, videos, exclude_languages):
        """
        Filter out videos in excluded languages.
        
        Args:
            videos (list): List of video items
            exclude_languages (list): List of language codes to exclude
        
        Returns:
            list: Filtered list of video items
        """
        if not exclude_languages or not videos:
            return videos
        
        # Clean up and prepare exclude_languages list
        exclude_languages = [lang.strip().lower() for lang in exclude_languages if lang.strip()]
        if not exclude_languages:
            return videos
            
        self.log_info(f"Filtering out videos in languages: {exclude_languages}")
        
        filtered_videos = []
        for video in videos:
            # Extract text content to analyze
            title = video.get('title', '').lower()
            description = video.get('description', '').lower()
            channel = video.get('channel', '').lower()
            
            # Check if video matches any excluded language
            should_exclude = False
            
            # Import detection code mappings from YouTubeSearchOptions class
            try:
                from src.ui.youtube_tab import YouTubeSearchOptions
                language_detection_codes = YouTubeSearchOptions.LANGUAGE_DETECTION_CODES
                
                for lang_code in exclude_languages:
                    # Look for exact language code matches
                    if lang_code in language_detection_codes:
                        # Check for language patterns in title and description
                        patterns = language_detection_codes[lang_code]
                        for pattern in patterns:
                            if (pattern in title or 
                                pattern in description or 
                                (len(pattern) > 2 and pattern in channel)):  # Only check channel for longer patterns
                                should_exclude = True
                                self.log_debug(f"Excluded video '{video.get('title')}' due to language pattern '{pattern}'")
                                break
                    
                    if should_exclude:
                        break
            except (ImportError, AttributeError) as e:
                self.log_warning(f"Could not import language detection codes: {e}")
                # Fallback to simple exclusion if we can't import the detection codes
                should_exclude = any(lang in title or lang in description for lang in exclude_languages)
            
            if not should_exclude:
                filtered_videos.append(video)
                
        self.log_info(f"Filtered videos from {len(videos)} to {len(filtered_videos)} after language exclusion")
        return filtered_videos
    
    @safe_api_call(fallback_value="0:00")
    def _parse_duration(self, duration_str):
        """
        Parse YouTube duration string (ISO 8601) to a human-readable format
        
        Args:
            duration_str (str): YouTube duration string (e.g., "PT1H2M3S")
            
        Returns:
            str: Human-readable duration (e.g., "1:02:03")
        """
        duration = duration_str[2:]  # Remove "PT" prefix
        
        hours = 0
        minutes = 0
        seconds = 0
        
        # Extract hours, minutes, seconds
        if "H" in duration:
            hours_str, duration = duration.split("H")
            hours = int(hours_str)
        
        if "M" in duration:
            minutes_str, duration = duration.split("M")
            minutes = int(minutes_str)
        
        if "S" in duration:
            seconds_str = duration.split("S")[0]
            seconds = int(seconds_str)
        
        if hours > 0:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes}:{seconds:02d}"
