"""
Fetching Tab UI Component.

Manages content fetching from different platforms.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import logging
from .base_ui import BaseUI
from .youtube_tab import YouTubeTab
from .reddit_tab import RedditTab

logger = logging.getLogger(__name__)


class FetchingTab(BaseUI):
    """Fetching tab for managing content retrieval from different platforms."""
    
    def __init__(self, parent, config_manager):
        """
        Initialize Fetching tab.
        
        Args:
            parent: Parent notebook
            config_manager: Configuration manager instance
        """
        self.current_platform = None
        self.platform_frames = {}
        self.youtube_content = []
        self.reddit_content = []
        
        super().__init__(parent, config_manager, "Fetching")
    
    def _init_ui(self):
        """Initialize the UI components."""
        # Main frame
        main_frame = ttk.Frame(self.frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Platform selection frame
        platform_frame = ttk.LabelFrame(main_frame, text="Select Platform")
        platform_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Platform dropdown
        ttk.Label(platform_frame, text="Platform:").pack(side=tk.LEFT, padx=5, pady=5)
        self.platform_var = tk.StringVar(value="YouTube")
        self.platform_combo = ttk.Combobox(platform_frame, textvariable=self.platform_var, 
                                           values=["YouTube", "Reddit"], state="readonly", width=20)
        self.platform_combo.pack(side=tk.LEFT, padx=5, pady=5)
        self.platform_combo.bind("<<ComboboxSelected>>", self._on_platform_changed)
        
        # Content frame - will contain the platform-specific frames
        self.content_frame = ttk.Frame(main_frame)
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create platform-specific frames
        self._create_platform_frames()
        
        # Initially show YouTube frame
        self._show_platform_frame("YouTube")
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        self.status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=2)
    
    def _create_platform_frames(self):
        """Create frames for each platform."""
        # YouTube frame - embedding YouTube tab functionality
        youtube_frame = ttk.Frame(self.content_frame)
        youtube_ui = YouTubeTab(youtube_frame, self.config_manager)
        youtube_ui.frame.pack(fill=tk.BOTH, expand=True)
        
        # Store reference to YouTube UI and its original display_results method
        self.platform_frames["YouTube"] = {
            "frame": youtube_frame, 
            "ui": youtube_ui
        }
        
        # Replace the display_results method
        original_yt_display = youtube_ui._display_results
        def youtube_display_wrapper(videos):
            self.youtube_content = videos
            return original_yt_display(videos)
        youtube_ui._display_results = youtube_display_wrapper
        
        # Reddit frame - embedding Reddit tab functionality
        reddit_frame = ttk.Frame(self.content_frame)
        reddit_ui = RedditTab(reddit_frame, self.config_manager)
        reddit_ui.frame.pack(fill=tk.BOTH, expand=True)
        
        # Store reference to Reddit UI and its original display_results method
        self.platform_frames["Reddit"] = {
            "frame": reddit_frame, 
            "ui": reddit_ui
        }
        
        # Replace the display_results method
        original_reddit_display = reddit_ui._update_results
        def reddit_display_wrapper():
            self.reddit_content = reddit_ui.results
            return original_reddit_display()
        reddit_ui._update_results = reddit_display_wrapper
    
    def _show_platform_frame(self, platform):
        """
        Show the frame for the selected platform.
        
        Args:
            platform: Platform name
        """
        # Hide all frames
        for p, frame_data in self.platform_frames.items():
            frame_data["frame"].pack_forget()
        
        # Show the selected platform's frame
        if platform in self.platform_frames:
            self.platform_frames[platform]["frame"].pack(fill=tk.BOTH, expand=True)
            self.current_platform = platform
    
    def _on_platform_changed(self, event):
        """
        Handle platform selection change.
        
        Args:
            event: ComboboxSelected event
        """
        platform = self.platform_var.get()
        self._show_platform_frame(platform)
    
    def get_fetched_content(self, platform=None):
        """
        Get content fetched from the specified platform.
        
        Args:
            platform: Platform to get content from. If None, returns content from the current platform.
            
        Returns:
            List of content items
        """
        if platform is None:
            platform = self.current_platform
        
        if platform == "YouTube":
            # Get selected videos from the YouTube UI
            youtube_ui = self.platform_frames.get("YouTube", {}).get("ui")
            if youtube_ui:
                # First check for selected videos
                if hasattr(youtube_ui, "selected_videos") and youtube_ui.selected_videos:
                    logger.info(f"Returning {len(youtube_ui.selected_videos)} selected videos from YouTube tab")
                    return youtube_ui.selected_videos
                # If no selected videos, return all videos
                if hasattr(youtube_ui, "videos") and youtube_ui.videos:
                    logger.info(f"No selected videos, returning {len(youtube_ui.videos)} videos from YouTube tab")
                    return youtube_ui.videos
            
            # Last resort: return cached content
            logger.info(f"Using cached YouTube content: {len(self.youtube_content)}")
            return self.youtube_content
        elif platform == "Reddit":
            return self.reddit_content
        
        return []
