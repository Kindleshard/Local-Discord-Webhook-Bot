"""
API Configuration Tab.

Manages API keys and credentials for various services.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import logging
from .base_ui import BaseUI

logger = logging.getLogger(__name__)


class ApiConfigTab(BaseUI):
    """API configuration tab."""
    
    # API platforms
    API_PLATFORMS = [
        {
            "name": "YouTube",
            "id": "youtube",
            "fields": [
                {
                    "name": "API Key",
                    "id": "api_key",
                    "type": "password",
                    "description": ("YouTube API Key from Google Cloud Console. "
                                  "Required for YouTube search functionality.")
                }
            ],
            "help_text": (
                "To get a YouTube API Key:\n"
                "1. Go to Google Cloud Console (https://console.cloud.google.com/)\n"
                "2. Create a new project or select an existing one\n"
                "3. Enable the YouTube Data API v3\n"
                "4. Create an API key from the Credentials section\n"
                "5. Paste the API key here"
            )
        },
        {
            "name": "Reddit",
            "id": "reddit",
            "fields": [
                {
                    "name": "Client ID",
                    "id": "client_id",
                    "type": "text",
                    "description": "Client ID from Reddit Developer Application"
                },
                {
                    "name": "Client Secret",
                    "id": "client_secret",
                    "type": "password",
                    "description": "Client Secret from Reddit Developer Application"
                },
                {
                    "name": "Username",
                    "id": "username",
                    "type": "text",
                    "description": "Reddit username"
                },
                {
                    "name": "Password",
                    "id": "password",
                    "type": "password",
                    "description": "Reddit password"
                }
            ],
            "help_text": (
                "To get Reddit API credentials:\n"
                "1. Go to https://www.reddit.com/prefs/apps\n"
                "2. Click 'create app' at the bottom\n"
                "3. Fill in the details (name, description, etc.)\n"
                "4. Select 'script' as the app type\n"
                "5. Add a redirect URI (http://localhost:8000)\n"
                "6. Click 'create app'\n"
                "7. The Client ID is under the app name\n"
                "8. The Client Secret is labeled 'secret'"
            )
        },
        {
            "name": "Twitter",
            "id": "twitter",
            "fields": [
                {
                    "name": "API Key",
                    "id": "api_key",
                    "type": "text",
                    "description": "Twitter API Key (Consumer Key)"
                },
                {
                    "name": "API Secret",
                    "id": "api_secret",
                    "type": "password",
                    "description": "Twitter API Secret (Consumer Secret)"
                },
                {
                    "name": "Access Token",
                    "id": "access_token",
                    "type": "text",
                    "description": "Twitter Access Token"
                },
                {
                    "name": "Access Token Secret",
                    "id": "access_token_secret",
                    "type": "password",
                    "description": "Twitter Access Token Secret"
                }
            ],
            "help_text": (
                "To get Twitter API credentials:\n"
                "1. Go to https://developer.twitter.com/\n"
                "2. Create a new application\n"
                "3. Navigate to 'Keys and Tokens'\n"
                "4. Generate Consumer Keys and Access Tokens"
            )
        }
    ]
    
    def __init__(self, parent, config_manager):
        """
        Initialize API configuration tab.
        
        Args:
            parent: Parent notebook
            config_manager: Configuration manager instance
        """
        self.api_entries = {}
        super().__init__(parent, config_manager, "API Configuration")
        # Select first platform by default
        if self.API_PLATFORMS:
            platform_name = self.API_PLATFORMS[0]["name"]
            self.platform_var.set(platform_name)
            self._on_platform_selected(None)
    
    def _init_ui(self):
        """Initialize the UI components."""
        # Main frame
        main_frame = ttk.Frame(self.frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create API platform selector
        platform_frame = ttk.Frame(main_frame)
        platform_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(platform_frame, text="Platform:").pack(side=tk.LEFT, padx=5)
        
        platform_names = [platform["name"] for platform in self.API_PLATFORMS]
        self.platform_var = tk.StringVar()
        
        platform_combo = ttk.Combobox(platform_frame, textvariable=self.platform_var, values=platform_names, state="readonly")
        platform_combo.pack(side=tk.LEFT, padx=5)
        platform_combo.bind("<<ComboboxSelected>>", self._on_platform_selected)
        
        # Create content frame (will hold platform-specific settings)
        self.content_frame = ttk.Frame(main_frame)
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(button_frame, text="Save", command=self._save_credentials).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Test Connection", command=self._test_connection).pack(side=tk.RIGHT, padx=5)
        
        # Create status label
        self.status_var = tk.StringVar(value="Select a platform to configure")
        status_label = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_label.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=2)
        
    def _on_platform_selected(self, event):
        """
        Handle platform selection.
        
        Args:
            event: ComboboxSelected event
        """
        # Clear content frame
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        # Get selected platform
        platform_name = self.platform_var.get()
        platform = next((p for p in self.API_PLATFORMS if p["name"] == platform_name), None)
        
        if not platform:
            return
        
        # Get existing API keys
        platform_id = platform["id"]
        creds = self.config_manager.config.get("api_keys", {}).get(platform_id, {})
        
        # Create settings frame
        settings_frame = ttk.LabelFrame(self.content_frame, text=f"{platform_name} API Configuration")
        settings_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create entries for each field
        self.api_entries[platform_id] = {}
        
        for i, field in enumerate(platform["fields"]):
            # Create field frame
            field_frame = ttk.Frame(settings_frame)
            field_frame.pack(fill=tk.X, padx=5, pady=5)
            
            # Add label
            ttk.Label(field_frame, text=f"{field['name']}:").grid(row=i, column=0, sticky="w", padx=5, pady=2)
            
            # Add entry
            field_id = field["id"]
            field_var = tk.StringVar(value=creds.get(field_id, ""))
            
            if field["type"] == "password":
                entry = ttk.Entry(field_frame, textvariable=field_var, show="*", width=40)
            else:
                entry = ttk.Entry(field_frame, textvariable=field_var, width=40)
            
            entry.grid(row=i, column=1, sticky="we", padx=5, pady=2)
            
            # Add description
            ttk.Label(field_frame, text=field["description"], foreground="gray").grid(row=i, column=2, sticky="w", padx=5, pady=2)
            
            # Store entry variable
            self.api_entries[platform_id][field_id] = field_var
        
        # Add help text
        if platform.get("help_text"):
            help_frame = ttk.LabelFrame(settings_frame, text="Help")
            help_frame.pack(fill=tk.X, padx=5, pady=5)
            
            help_text = tk.Text(help_frame, height=10, wrap=tk.WORD)
            help_text.pack(fill=tk.X, padx=5, pady=5)
            
            help_text.insert(tk.END, platform["help_text"])
            help_text.config(state=tk.DISABLED)
        
        # Update status
        self.status_var.set(f"Configuring {platform_name} API")
    
    def _save_credentials(self):
        """Save API credentials."""
        # Get selected platform
        platform_name = self.platform_var.get()
        platform = next((p for p in self.API_PLATFORMS if p["name"] == platform_name), None)
        
        if not platform:
            return
        
        # Get platform ID
        platform_id = platform["id"]
        
        # Get current API keys
        api_keys = self.config_manager.config.get("api_keys", {})
        if platform_id not in api_keys:
            api_keys[platform_id] = {}
        
        # Update with new values
        for field in platform["fields"]:
            field_id = field["id"]
            if platform_id in self.api_entries and field_id in self.api_entries[platform_id]:
                field_var = self.api_entries[platform_id][field_id]
                value = field_var.get()
                
                # Only update if not empty
                if value:
                    api_keys[platform_id][field_id] = value
        
        # Save API keys
        self.config_manager.update_config("api_keys", api_keys)
        
        # Update status
        self.status_var.set(f"{platform_name} API credentials saved")
        messagebox.showinfo("Credentials Saved", f"{platform_name} API credentials saved successfully")
    
    def _test_connection(self):
        """Test API connection."""
        # Get selected platform
        platform_name = self.platform_var.get()
        platform = next((p for p in self.API_PLATFORMS if p["name"] == platform_name), None)
        
        if not platform:
            return
        
        # Get platform credentials
        platform_id = platform["id"]
        credentials = self.config_manager.config.get("api_keys", {}).get(platform_id, {})
        
        # Check if credentials are empty
        if not credentials:
            messagebox.showerror("Connection Test", f"No {platform_name} API credentials found. Please enter and save them first.")
            return
        
        # Validate credentials are present
        for field in platform["fields"]:
            field_id = field["id"]
            if field_id not in credentials or not credentials[field_id]:
                messagebox.showwarning("Missing Credentials", 
                                    f"{field['name']} is required. Please save your credentials first.")
                return
        
        # Update status
        self.status_var.set(f"Testing {platform_name} API connection...")
        
        # Test connection based on platform
        if platform_id == "youtube":
            self._test_youtube_connection(credentials)
        elif platform_id == "reddit":
            self._test_reddit_connection(credentials)
        elif platform_id == "twitter":
            self._test_twitter_connection(credentials)
    
    def _test_youtube_connection(self, credentials):
        """
        Test YouTube API connection.
        
        Args:
            credentials: YouTube API credentials
        """
        def test_task():
            try:
                # Import the connector factory
                from src.api_connectors import get_connector
                
                # Create YouTube connector
                connector = get_connector("youtube", credentials)
                
                # Validate credentials
                if not connector.validate_credentials():
                    return False, "YouTube API credentials are invalid"
                
                # Test a simple search
                videos = connector.search_videos("test", max_results=1)
                
                return len(videos) > 0, "Connection successful. YouTube API is working."
            except Exception as e:
                logger.error(f"YouTube API connection test failed: {e}")
                return False, f"Connection failed: {str(e)}"
        
        def handle_result(result):
            success, message = result
            
            if success:
                messagebox.showinfo("Connection Test", message)
                self.status_var.set("YouTube API connection successful")
            else:
                messagebox.showerror("Connection Test", message)
                self.status_var.set("YouTube API connection failed")
        
        # Run test in background thread
        self.run_async(test_task, handle_result)
    
    def _test_reddit_connection(self, credentials):
        """
        Test Reddit API connection.
        
        Args:
            credentials: Reddit API credentials
        """
        # Update status (placeholder for now)
        self.status_var.set("Reddit API connection testing not implemented")
        messagebox.showinfo("Not Implemented", "Reddit API connection testing is not implemented yet")
    
    def _test_twitter_connection(self, credentials):
        """
        Test Twitter API connection.
        
        Args:
            credentials: Twitter API credentials
        """
        # Update status (placeholder for now)
        self.status_var.set("Twitter API connection testing not implemented")
        messagebox.showinfo("Not Implemented", "Twitter API connection testing is not implemented yet")
    
    def on_config_changed(self):
        """Handle configuration changes."""
        # Refresh the current view
        self._on_platform_selected(None)
