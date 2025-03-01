"""
Discord Bot UI Main Window.

This module contains the main application UI that integrates all tabs.
"""

import tkinter as tk
from tkinter import ttk
import logging
import os
import json

from .discord_tab import DiscordTab
from .youtube_tab import YouTubeTab
from .fetching_tab import FetchingTab
from .api_config_tab import ApiConfigTab
from .schedule_tab import ScheduleTab
from .base_ui import StyleManager, ConfigManager

logger = logging.getLogger(__name__)


class DiscordBotUI:
    """Main UI for the Discord Webhook Bot."""
    
    def __init__(self, root):
        """
        Initialize the Discord Bot UI.
        
        Args:
            root: Root Tkinter window
        """
        self.root = root
        self.root.title("Discord Content Curator")
        self.root.geometry("1200x800")
        
        # Apply style
        style = ttk.Style()
        StyleManager.configure(style)
        
        # Initialize config manager
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        config_dir = os.path.join(base_dir, "config")
        self.config_manager = ConfigManager(config_dir)
        
        # Create main notebook
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Initialize tabs
        self.tabs = {}
        self._create_tabs()
        
        # Set up event handlers
        self._setup_events()
        
        # Create status bar
        self._create_status_bar()
        
        logger.info("Discord Bot UI initialized")
    
    def _create_tabs(self):
        """Create and initialize all tabs."""
        # Discord tab
        discord_frame = ttk.Frame(self.notebook)
        self.tabs["DiscordTab"] = DiscordTab(discord_frame, self.config_manager)
        self.notebook.add(discord_frame, text="Discord")
        
        # YouTube tab
        youtube_frame = ttk.Frame(self.notebook)
        self.tabs["YouTubeTab"] = YouTubeTab(youtube_frame, self.config_manager)
        self.notebook.add(youtube_frame, text="YouTube")
        
        # Fetching tab
        fetching_frame = ttk.Frame(self.notebook)
        fetching_tab = FetchingTab(fetching_frame, self.config_manager)
        self.tabs["FetchingTab"] = fetching_tab
        self.notebook.add(fetching_frame, text="Fetch Content")
        
        # API Config tab
        api_config_frame = ttk.Frame(self.notebook)
        self.tabs["ApiConfigTab"] = ApiConfigTab(api_config_frame, self.config_manager)
        self.notebook.add(api_config_frame, text="API Config")
        
        # Schedule tab
        schedule_frame = ttk.Frame(self.notebook)
        self.tabs["ScheduleTab"] = ScheduleTab(schedule_frame, self.config_manager, fetching_tab)
        self.notebook.add(schedule_frame, text="Schedule")
        
        # Select the first tab by default
        self.notebook.select(0)
    
    def _setup_events(self):
        """Set up event handlers."""
        # Tab change event
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)
        
        # Window close event
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
    
    def _on_tab_changed(self, event):
        """Handle tab change event."""
        try:
            selected = self.notebook.select()
            if selected:
                current_tab = self.notebook.tab(selected, "text")
                logger.info(f"Switched to tab: {current_tab}")
                
                # Update status bar
                self.status_var.set(f"Current tab: {current_tab}")
            else:
                logger.warning("No tab selected")
                self.status_var.set("Ready")
        except Exception as e:
            logger.error(f"Error in tab change handler: {e}")
            self.status_var.set("Ready")
    
    def _on_close(self):
        """Handle window close event."""
        logger.info("Closing application")
        self.root.destroy()
    
    def _create_status_bar(self):
        """Create status bar at the bottom of the window."""
        status_frame = ttk.Frame(self.root)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=10, pady=5)
        
        self.status_var = tk.StringVar()
        status_label = ttk.Label(status_frame, textvariable=self.status_var)
        status_label.pack(side=tk.LEFT)
        
        self.status_var.set("Ready")
