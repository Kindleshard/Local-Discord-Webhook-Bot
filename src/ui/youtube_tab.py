"""
YouTube Tab UI Component.

Manages YouTube content search and display.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import logging
import webbrowser
from .base_ui import BaseUI
import threading
from datetime import datetime

logger = logging.getLogger(__name__)


class YouTubeSearchOptions:
    """Container for YouTube search options."""
    
    # Search methods
    SEARCH_METHODS = [
        {"name": "Keyword", "value": 0},
        {"name": "Topic", "value": 1},
        {"name": "Channel", "value": 2}
    ]
    
    # Order options
    ORDER_OPTIONS = [
        {"name": "Relevance", "value": "relevance"},
        {"name": "Date", "value": "date"},
        {"name": "Rating", "value": "rating"},
        {"name": "Title", "value": "title"},
        {"name": "View Count", "value": "viewCount"}
    ]
    
    # Result count options
    RESULT_OPTIONS = [5, 10, 15, 25, 50]
    
    # Language options
    LANGUAGE_OPTIONS = [
        {"name": "All Languages", "value": ""},
        {"name": "English", "value": "en"},
        {"name": "Spanish", "value": "es"},
        {"name": "French", "value": "fr"},
        {"name": "German", "value": "de"},
        {"name": "Japanese", "value": "ja"},
        {"name": "Korean", "value": "ko"},
        {"name": "Arabic", "value": "ar"},
        {"name": "Hindi", "value": "hi"},
        {"name": "Indonesian", "value": "id"},
        {"name": "Italian", "value": "it"},
        {"name": "Malay", "value": "ms"},
        {"name": "Portuguese", "value": "pt"},
        {"name": "Russian", "value": "ru"},
        {"name": "Thai", "value": "th"},
        {"name": "Chinese", "value": "zh"},
    ]
    
    # Language detection code mapping
    LANGUAGE_DETECTION_CODES = {
        "en": ["en", "english"],
        "es": ["es", "spanish", "español"],
        "fr": ["fr", "french", "français"],
        "de": ["de", "german", "deutsch"],
        "ja": ["ja", "japanese", "日本語"],
        "ko": ["ko", "korean", "한국어"],
        "ar": ["ar", "arabic", "العربية"],
        "hi": ["hi", "hindi", "हिन्दी"],
        "id": ["id", "indonesian", "bahasa indonesia"],
        "it": ["it", "italian", "italiano"],
        "ms": ["ms", "malay", "bahasa melayu"],
        "pt": ["pt", "portuguese", "português"],
        "ru": ["ru", "russian", "русский"],
        "th": ["th", "thai", "ไทย"],
        "zh": ["zh", "chinese", "中文"],
    }
    
    @staticmethod
    def get_topics():
        """Get topic options."""
        try:
            from src.topic_ids import TOPIC_IDS
            topics = [{"name": name, "id": topic_id} for name, topic_id in TOPIC_IDS.items()]
            return sorted(topics, key=lambda x: x["name"])
        except ImportError:
            logger.error("Could not import topic IDs")
            return []


class YouTubeTab(BaseUI):
    """YouTube content search tab."""
    
    def __init__(self, parent, config_manager):
        """
        Initialize YouTube tab.
        
        Args:
            parent: Parent notebook
            config_manager: Configuration manager instance
        """
        self.videos = []
        self.selected_videos = []
        self.video_checkboxes = []
        super().__init__(parent, config_manager, "YouTube")
    
    def _init_ui(self):
        """Initialize the UI components."""
        # Main frame
        main_frame = ttk.Frame(self.frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create search frame
        search_frame = ttk.LabelFrame(main_frame, text="Search & Filter")
        search_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Platform selector (for future expansion)
        platform_frame = ttk.Frame(search_frame)
        platform_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(platform_frame, text="Platform:").pack(side=tk.LEFT, padx=5)
        self.platform_var = tk.StringVar(value="YouTube")
        platform_combo = ttk.Combobox(platform_frame, textvariable=self.platform_var, state="readonly")
        platform_combo["values"] = ["YouTube"]
        platform_combo.pack(side=tk.LEFT, padx=5)
        
        # Search method tabs
        self.search_tabs = ttk.Notebook(search_frame)
        self.search_tabs.pack(fill=tk.X, padx=5, pady=5)
        
        # Keyword search tab
        keyword_tab = ttk.Frame(self.search_tabs)
        self.search_tabs.add(keyword_tab, text="Keyword")
        
        # Keyword search query
        keyword_query_frame = ttk.Frame(keyword_tab)
        keyword_query_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(keyword_query_frame, text="Search Query:").pack(side=tk.LEFT, padx=5)
        self.youtube_query_var = tk.StringVar()
        ttk.Entry(keyword_query_frame, textvariable=self.youtube_query_var, width=40).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # Topic search tab
        topic_tab = ttk.Frame(self.search_tabs)
        self.search_tabs.add(topic_tab, text="Topic")
        
        # Topic category dropdown
        topic_category_frame = ttk.Frame(topic_tab)
        topic_category_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Get available topics
        topics = YouTubeSearchOptions.get_topics()
        topic_names = [topic["name"] for topic in topics]
        
        ttk.Label(topic_category_frame, text="Topic:").pack(side=tk.LEFT, padx=5)
        self.topic_var = tk.StringVar()
        self.topic_dropdown = ttk.Combobox(topic_category_frame, textvariable=self.topic_var, values=topic_names, state="readonly")
        self.topic_dropdown.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # Custom topic ID
        topic_id_frame = ttk.Frame(topic_tab)
        topic_id_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(topic_id_frame, text="Custom Topic ID:").pack(side=tk.LEFT, padx=5)
        self.custom_topic_var = tk.StringVar()
        ttk.Entry(topic_id_frame, textvariable=self.custom_topic_var, width=40).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # Channel search tab
        channel_tab = ttk.Frame(self.search_tabs)
        self.search_tabs.add(channel_tab, text="Channel")
        
        # Channel ID
        channel_id_frame = ttk.Frame(channel_tab)
        channel_id_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(channel_id_frame, text="Channel ID:").pack(side=tk.LEFT, padx=5)
        self.youtube_channel_var = tk.StringVar()
        ttk.Entry(channel_id_frame, textvariable=self.youtube_channel_var, width=40).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # Search options frame
        options_frame = ttk.LabelFrame(search_frame, text="Search Options")
        options_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Order by
        order_frame = ttk.Frame(options_frame)
        order_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(order_frame, text="Sort By:").pack(side=tk.LEFT, padx=5)
        
        order_names = [option["name"] for option in YouTubeSearchOptions.ORDER_OPTIONS]
        self.order_var = tk.StringVar(value="Relevance")
        order_combo = ttk.Combobox(order_frame, textvariable=self.order_var, values=order_names, state="readonly")
        order_combo.pack(side=tk.LEFT, padx=5)
        
        # Max results
        results_frame = ttk.Frame(options_frame)
        results_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(results_frame, text="Max Results:").pack(side=tk.LEFT, padx=5)
        self.max_results_var = tk.StringVar(value="10")
        max_results_combo = ttk.Combobox(results_frame, textvariable=self.max_results_var, values=YouTubeSearchOptions.RESULT_OPTIONS, state="readonly", width=5)
        max_results_combo.pack(side=tk.LEFT, padx=5)
        
        # Language
        language_frame = ttk.Frame(options_frame)
        language_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(language_frame, text="Language:").pack(side=tk.LEFT, padx=5)
        self.language_var = tk.StringVar(value="All Languages")
        language_combo = ttk.Combobox(language_frame, textvariable=self.language_var, values=[option["name"] for option in YouTubeSearchOptions.LANGUAGE_OPTIONS], state="readonly")
        language_combo.pack(side=tk.LEFT, padx=5)
        
        # Exclude languages
        exclude_languages_frame = ttk.Frame(options_frame)
        exclude_languages_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(exclude_languages_frame, text="Exclude Languages:").pack(side=tk.LEFT, padx=5)
        self.exclude_languages_var = tk.StringVar(value="")
        exclude_languages_entry = ttk.Entry(exclude_languages_frame, textvariable=self.exclude_languages_var, width=40)
        exclude_languages_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # Help button for exclude languages
        help_button = ttk.Button(exclude_languages_frame, text="?", width=2, 
                                command=lambda: messagebox.showinfo("Exclude Languages Help", 
                                "Enter comma-separated language codes to exclude from results.\n\n"
                                "Example: 'ja,ko,ru' will exclude Japanese, Korean, and Russian videos.\n\n"
                                "Available codes:\n"
                                "en - English\n"
                                "es - Spanish\n"
                                "fr - French\n"
                                "de - German\n"
                                "ja - Japanese\n"
                                "ko - Korean\n"
                                "ar - Arabic\n"
                                "hi - Hindi\n"
                                "id - Indonesian\n"
                                "it - Italian\n"
                                "ms - Malay\n"
                                "pt - Portuguese\n"
                                "ru - Russian\n"
                                "th - Thai\n"
                                "zh - Chinese"))
        help_button.pack(side=tk.LEFT, padx=5)
        
        # Search button
        button_frame = ttk.Frame(options_frame)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(button_frame, text="Search Videos", command=self._search_videos).pack(side=tk.RIGHT, padx=5)
        
        # Results frame
        self.results_frame = ttk.LabelFrame(main_frame, text="Search Results")
        self.results_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=2)
    
    def _create_context_menu(self):
        """Create context menu for results."""
        self.context_menu = tk.Menu(self.frame, tearoff=0)
        self.context_menu.add_command(label="Copy URL", command=self._copy_video_url)
        self.context_menu.add_command(label="Open in Browser", command=self._open_video_in_browser)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="View Details", command=self._view_video_details)
        
        # Bind right-click to show context menu
        # self.results_tree.bind("<Button-3>", self._show_context_menu)
    
    def _show_context_menu(self, event):
        """Show context menu."""
        # Select the item under the cursor
        # item = self.results_tree.identify_row(event.y)
        # if item:
        #     self.results_tree.selection_set(item)
        #     self.context_menu.post(event.x_root, event.y_root)
    
    def _search_videos(self):
        """Search for YouTube videos."""
        # Get API key
        api_key = self.config_manager.credentials.get("youtube", {}).get("api_key")
        if not api_key:
            messagebox.showwarning("API Key Required", "Please configure a YouTube API key in the API Configuration tab")
            return
        
        # Create credentials dictionary
        credentials = {
            "api_key": api_key
        }
        
        # Get active tab (search method)
        search_method = self.search_tabs.index(self.search_tabs.select())
        
        # Get max results
        try:
            max_results = int(self.max_results_var.get())
        except ValueError:
            max_results = 10
        
        # Get order value
        order_name = self.order_var.get()
        order_value = next((o["value"] for o in YouTubeSearchOptions.ORDER_OPTIONS if o["name"] == order_name), "relevance")
        
        # Get language value
        language_name = self.language_var.get()
        language_value = next((o["value"] for o in YouTubeSearchOptions.LANGUAGE_OPTIONS if o["name"] == language_name), "")
        
        # Get exclude languages
        exclude_languages = self.exclude_languages_var.get().split(",")
        
        # Update status
        self.status_var.set("Searching YouTube...")
        
        # Define search task
        def search_task():
            try:
                # Import the connector factory
                from src.api_connectors import get_connector
                connector = get_connector("youtube", credentials)
                
                if search_method == 0:  # Keyword search
                    query = self.youtube_query_var.get().strip()
                    if not query:
                        return None, "Please enter a search query"
                    
                    return connector.fetch(query=query, max_results=max_results, order=order_value, language=language_value, exclude_languages=exclude_languages), None
                
                elif search_method == 1:  # Topic search
                    # Check if custom topic ID is provided
                    custom_topic_id = self.custom_topic_var.get().strip()
                    if custom_topic_id:
                        topic_id = custom_topic_id
                    else:
                        # Get topic ID from dropdown
                        topic_name = self.topic_var.get()
                        if not topic_name:
                            return None, "Please select a topic or enter a custom topic ID"
                        
                        # Find topic ID by name
                        topics = YouTubeSearchOptions.get_topics()
                        topic = next((t for t in topics if t["name"] == topic_name), None)
                        if not topic:
                            return None, "Topic not found"
                        
                        topic_id = topic["id"]
                    
                    return connector.search_by_topic(topic_id=topic_id, max_results=max_results, order=order_value, language=language_value, exclude_languages=exclude_languages), None
                
                elif search_method == 2:  # Channel search
                    channel_id = self.youtube_channel_var.get().strip()
                    if not channel_id:
                        return None, "Please enter a channel ID"
                    
                    return connector.fetch(channel_id=channel_id, max_results=max_results, order=order_value, language=language_value, exclude_languages=exclude_languages), None
                
                return None, "Invalid search method"
            
            except Exception as e:
                logger.error(f"Error searching videos: {e}")
                return None, f"Error: {str(e)}"
        
        # Define callback function to process results
        def process_results(result):
            videos, error = result
            
            if error:
                self.status_var.set("Error: " + error)
                messagebox.showerror("Search Error", error)
                return
            
            # Store videos
            self.videos = videos
            
            # Display results
            self._display_results(videos)
        
        # Run search in background thread
        self.run_async(search_task, process_results)
    
    def _display_results(self, videos):
        """
        Display search results.
        
        Args:
            videos: List of video items
        """
        # Clear previous results
        for widget in self.results_frame.winfo_children():
            widget.destroy()
        
        if not videos:
            self.status_var.set("No videos found")
            return
        
        # Update status
        self.status_var.set(f"Found {len(videos)} videos")
        
        # Clear previous checkboxes and selections
        self.video_checkboxes = []
        self.selected_videos = []
        
        # Create a frame for videos with checkboxes
        self.video_checkboxes_frame = ttk.Frame(self.results_frame)
        self.video_checkboxes_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create a canvas for scrolling
        canvas = tk.Canvas(self.video_checkboxes_frame)
        scrollbar = ttk.Scrollbar(self.video_checkboxes_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Display each video with a checkbox
        for i, video in enumerate(videos):
            # Direct access to fields if available, otherwise check nested structure
            if "title" in video:
                # Direct access to flat structure
                title = video.get("title", "Unknown Title")
                channel = video.get("channel", "Unknown Channel")
                published = video.get("published_at", video.get("published", "Unknown Date"))
                views = video.get("views", 0)
                likes = video.get("likes", 0)
                video_id = video.get("id", "")
            else:
                # Nested structure from API
                snippet = video.get("snippet", {})
                
                # Get title and channel
                title = snippet.get("title", "Unknown Title")
                channel = snippet.get("channelTitle", "Unknown Channel")
                
                # Get published date
                published_at = snippet.get("publishedAt", "")
                published = "Unknown Date"
                if published_at:
                    try:
                        date_obj = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
                        published = date_obj.strftime("%Y-%m-%d")
                    except (ValueError, AttributeError):
                        pass
                
                # Get view count and likes
                statistics = video.get("statistics", {})
                views = statistics.get("viewCount", statistics.get("views", 0))
                likes = statistics.get("likeCount", statistics.get("likes", 0))
                
                # Get video ID
                video_id = video.get("id", "")
                if isinstance(video_id, dict):
                    video_id = video_id.get("videoId", "")
            
            # Format numbers
            try:
                views = f"{int(views):,}"
            except (ValueError, TypeError):
                views = "0"
                
            try:
                likes = f"{int(likes):,}"
            except (ValueError, TypeError):
                likes = "0"
            
            # Create a string representation for scheduling
            video["display_text"] = f"YouTube - {title} (by {channel})"
            video["source_id"] = video_id if isinstance(video_id, str) else str(video_id)
            
            # Create a frame for the video
            video_frame = ttk.Frame(scrollable_frame)
            video_frame.pack(fill=tk.X, padx=5, pady=2)
            
            # Create a checkbox
            var = tk.BooleanVar(value=False)
            self.video_checkboxes.append(var)
            
            checkbox = ttk.Checkbutton(video_frame, variable=var, text="")
            checkbox.pack(side=tk.LEFT, padx=2)
            
            # Create labels for the video details
            title_label = ttk.Label(video_frame, text=title, font=("TkDefaultFont", 10, "bold"), wraplength=400)
            title_label.pack(side=tk.TOP, anchor=tk.W, padx=5)
            
            channel_label = ttk.Label(video_frame, text=f"Channel: {channel}")
            channel_label.pack(side=tk.TOP, anchor=tk.W, padx=5)
            
            details_label = ttk.Label(video_frame, text=f"Published: {published} • Views: {views} • Likes: {likes}")
            details_label.pack(side=tk.TOP, anchor=tk.W, padx=5)
            
            # Add a separator
            ttk.Separator(scrollable_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=5, pady=5)
            
            # Bind click event to show details
            title_label.bind("<Button-1>", lambda event, idx=i: self._view_video_details_by_index(idx))
            
        # Add a button frame at the bottom
        button_frame = ttk.Frame(self.video_checkboxes_frame)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Add buttons to select/deselect all
        ttk.Button(button_frame, text="Select All", command=self._select_all_videos).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Deselect All", command=self._deselect_all_videos).pack(side=tk.LEFT, padx=5)
        
        # Add save button
        ttk.Button(button_frame, text="Save Selected Videos", command=self._save_selected_videos).pack(side=tk.RIGHT, padx=5)
    
    def _view_video_details_by_index(self, index):
        """View details of a video by index."""
        if 0 <= index < len(self.videos):
            video = self.videos[index]
            self._show_video_details(video)
    
    def _show_video_details(self, video):
        """Show video details in a popup."""
        # Create a new top-level window
        details_window = tk.Toplevel(self.frame)
        details_window.title("Video Details")
        details_window.geometry("600x400")
        details_window.minsize(400, 300)
        
        # Get video details
        if "title" in video:
            title = video.get("title", "Unknown Title")
            channel = video.get("channel", "Unknown Channel")
            published = video.get("published_at", video.get("published", "Unknown Date"))
            description = video.get("description", "No description available")
            url = f"https://www.youtube.com/watch?v={video.get('id', '')}"
        else:
            snippet = video.get("snippet", {})
            title = snippet.get("title", "Unknown Title")
            channel = snippet.get("channelTitle", "Unknown Channel")
            published = snippet.get("publishedAt", "Unknown Date")
            description = snippet.get("description", "No description available")
            video_id = video.get("id", "")
            if isinstance(video_id, dict):
                video_id = video_id.get("videoId", "")
            url = f"https://www.youtube.com/watch?v={video_id}"
        
        # Create a frame for details
        details_frame = ttk.Frame(details_window, padding=10)
        details_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create labels for the video details
        ttk.Label(details_frame, text=title, font=("TkDefaultFont", 12, "bold"), wraplength=550).pack(fill=tk.X, pady=(0, 10))
        ttk.Label(details_frame, text=f"Channel: {channel}", wraplength=550).pack(fill=tk.X, pady=2)
        ttk.Label(details_frame, text=f"Published: {published}", wraplength=550).pack(fill=tk.X, pady=2)
        
        # Add a separator
        ttk.Separator(details_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        
        # Create scrollable description
        desc_frame = ttk.LabelFrame(details_frame, text="Description")
        desc_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Add scrollbar for description
        desc_scroll = ttk.Scrollbar(desc_frame)
        desc_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Add text widget for description
        desc_text = tk.Text(desc_frame, wrap=tk.WORD, yscrollcommand=desc_scroll.set, height=10)
        desc_text.insert(tk.END, description)
        desc_text.config(state=tk.DISABLED)
        desc_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        desc_scroll.config(command=desc_text.yview)
        
        # Add button to open in browser
        button_frame = ttk.Frame(details_window)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(button_frame, text="Open in Browser", command=lambda: webbrowser.open(url)).pack(side=tk.RIGHT)
        ttk.Button(button_frame, text="Close", command=details_window.destroy).pack(side=tk.RIGHT, padx=5)
    
    def _select_all_videos(self):
        """Select all videos."""
        for var in self.video_checkboxes:
            var.set(True)
    
    def _deselect_all_videos(self):
        """Deselect all videos."""
        for var in self.video_checkboxes:
            var.set(False)
    
    def _save_selected_videos(self):
        """Save selected videos."""
        self.selected_videos = []
        
        for i, var in enumerate(self.video_checkboxes):
            if var.get() and i < len(self.videos):
                self.selected_videos.append(self.videos[i])
        
        if not self.selected_videos:
            messagebox.showinfo("No Videos Selected", "Please select at least one video to save.")
            return
        
        self.status_var.set(f"Saved {len(self.selected_videos)} videos")
        messagebox.showinfo("Videos Saved", f"{len(self.selected_videos)} videos have been saved and are now available in the Schedule tab.")
    
    def on_config_changed(self):
        """Handle configuration changes."""
        # Refresh UI if needed
        pass
