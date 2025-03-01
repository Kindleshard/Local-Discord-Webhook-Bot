"""
Discord Webhook Bot - Main entry point (refactored version).

This script initializes and runs the Discord Webhook Bot application.
"""

import os
import tkinter as tk
from tkinter import ttk, messagebox
import logging
import sys
import json
from src.ui.base_ui import StyleManager, ConfigManager
from src.ui.discord_tab import DiscordTab
from src.ui.youtube_tab import YouTubeTab
from src.ui.reddit_tab import RedditTab
from src.ui.api_config_tab import ApiConfigTab
from src.ui.schedule_tab import ScheduleTab
from src.ui.fetching_tab import FetchingTab
import threading

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


class DiscordBotApp:
    """Main application class for the Discord Webhook Bot."""
    
    def __init__(self, root):
        """
        Initialize the application.
        
        Args:
            root: Tkinter root window
        """
        self.root = root
        self.root.title("Discord Webhook Bot")
        self.root.geometry("800x600")
        
        # Set style
        self.style = ttk.Style()
        StyleManager.configure(self.style)
        
        # Create config manager
        script_dir = os.path.dirname(os.path.abspath(__file__))
        config_dir = os.path.join(script_dir, "config")
        logger.info(f"Script directory: {script_dir}")
        logger.info(f"Config directory path: {config_dir}")
        
        # Test config file access directly
        config_file = os.path.join(config_dir, "config.json")
        logger.info(f"Config file path: {config_file}")
        logger.info(f"Config file exists: {os.path.exists(config_file)}")
        
        # Try to read the config file directly
        try:
            with open(config_file, 'r') as f:
                direct_config = json.load(f)
                logger.info(f"Successfully read config file directly with {len(direct_config.keys())} keys")
        except Exception as e:
            logger.error(f"Error reading config file directly: {e}")
        
        self.config_manager = ConfigManager(config_dir)
        
        # Check if credentials file exists
        credentials_file = os.path.join(config_dir, "credentials.json")
        if not os.path.exists(credentials_file):
            logger.warning("Credentials file not found. Using example file as template.")
            example_file = os.path.join(config_dir, "credentials.example.json")
            if os.path.exists(example_file):
                with open(example_file, 'r') as src:
                    with open(credentials_file, 'w') as dest:
                        dest.write(src.read())
                messagebox.showwarning(
                    "Credentials Required",
                    "Please update the credentials.json file with your API keys before using the application."
                )
            else:
                messagebox.showerror(
                    "Missing Files",
                    "credentials.example.json not found. Please check your installation."
                )
        
        # Create main frame
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create tabs - Rearranged according to specified order
        self.discord_tab = DiscordTab(self.notebook, self.config_manager)
        self.api_config_tab = ApiConfigTab(self.notebook, self.config_manager)
        self.fetching_tab = FetchingTab(self.notebook, self.config_manager)
        self.schedule_tab = ScheduleTab(self.notebook, self.config_manager, self.fetching_tab)
        
        # Add tabs to notebook - in the requested order
        self.notebook.add(self.discord_tab.frame, text="Discord Config")
        self.notebook.add(self.api_config_tab.frame, text="API Config")
        self.notebook.add(self.fetching_tab.frame, text="Fetching")
        self.notebook.add(self.schedule_tab.frame, text="Tasks")
        
        # Select the first tab by default
        self.notebook.select(0)
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        self.status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Set window close handler
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Start scheduler thread
        self.scheduler_running = True
        self.scheduler_thread = threading.Thread(target=self._scheduler_worker, daemon=True)
        self.scheduler_thread.start()
        
        # Check for webhook URLs in config and issue warning if present
        self._check_webhook_security()
        
        logger.info("Application initialized")
    
    def _check_webhook_security(self):
        """Check for webhook URLs in config and issue warning if present."""
        webhooks = self.config_manager.config.get("webhooks", [])
        for webhook in webhooks:
            if webhook.get("url") and webhook.get("url").startswith("https://discord.com/api/webhooks/"):
                messagebox.showwarning(
                    "Security Warning",
                    "Discord webhook URLs are stored in config.json, which may be committed to version control.\n\n"
                    "Consider moving webhook URLs to credentials.json for better security."
                )
                break
    
    def _scheduler_worker(self):
        """Background thread that checks for scheduled tasks to run."""
        import time
        from datetime import datetime
        
        logger.info("Scheduler thread started")
        
        while self.scheduler_running:
            try:
                # Get tasks from config
                config = self.config_manager.config
                tasks = config.get("scheduled_tasks", [])
                
                # Current time
                now = datetime.now()
                
                # Check each task
                for task in tasks:
                    # Skip disabled tasks
                    if not task.get("enabled", True):
                        continue
                    
                    # Check if it's time to run
                    next_run = task.get("next_run", "")
                    if next_run:
                        try:
                            next_run_dt = datetime.fromisoformat(next_run)
                            if now >= next_run_dt:
                                logger.info(f"Running scheduled task: {task.get('source')}")
                                self.status_var.set(f"Running scheduled task: {task.get('source')}")
                                
                                # Run the task using the schedule tab's execute method
                                threading.Thread(
                                    target=self.schedule_tab._execute_task,
                                    args=(task,)
                                ).start()
                        except (ValueError, TypeError) as e:
                            logger.error(f"Error parsing next run time: {e}")
                
                # Sleep for a bit
                time.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Error in scheduler thread: {e}", exc_info=True)
                time.sleep(60)  # Wait before retrying
    
    def run(self):
        """Run the application."""
        logger.info("Starting application")
        self.root.mainloop()
    
    def on_close(self):
        """Handle window close event."""
        logger.info("Closing application")
        self.scheduler_running = False
        self.root.destroy()


def main():
    """Main entry point."""
    root = tk.Tk()
    app = DiscordBotApp(root)
    app.run()


if __name__ == "__main__":
    main()
