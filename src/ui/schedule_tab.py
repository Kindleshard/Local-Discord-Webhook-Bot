"""
Task management tab for the Discord Webhook Bot.

This module provides UI components for managing tasks.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import logging
import time as time_module  # Rename to avoid conflict
import threading
import json
from datetime import datetime, timedelta, time
from .base_ui import BaseUI
import os

logger = logging.getLogger(__name__)


class TasksTab(BaseUI):
    """Task management tab UI component."""
    
    def __init__(self, parent, config_manager, fetching_tab=None):
        """
        Initialize the task management tab.
        
        Args:
            parent: Parent widget
            config_manager: Configuration manager
            fetching_tab: Reference to the fetching tab for content selection
        """
        self.fetching_tab = fetching_tab
        super().__init__(parent, config_manager, "Tasks")
        self._tasks = self.config.get("scheduled_tasks", [])
        
        # Create a status variable for this tab
        self.status_var = tk.StringVar(value="Ready")
        
        self._setup_ui()
        self._load_tasks()
    
    @property
    def config(self):
        """Get the current configuration."""
        return self.config_manager.config
    
    @property
    def tasks(self):
        """Get the current tasks."""
        return self._tasks
    
    @tasks.setter
    def tasks(self, value):
        """Set the tasks."""
        self._tasks = value
    
    def _init_ui(self):
        """Initialize the UI components. Required by BaseUI."""
        # This is called by the parent class, but we're setting up UI in _setup_ui
        pass
    
    def _setup_ui(self):
        """Set up the UI components."""
        # Create a main frame
        main_frame = ttk.Frame(self.frame, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Top frame for buttons
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.grid(row=0, column=0, sticky="w", pady=(0, 5))
        
        # Add buttons
        add_button = ttk.Button(buttons_frame, text="Add Task", command=self._add_task_dialog)
        add_button.pack(side=tk.LEFT, padx=5)
        
        edit_button = ttk.Button(buttons_frame, text="Edit Task", command=self._edit_task_dialog)
        edit_button.pack(side=tk.LEFT, padx=5)
        
        remove_button = ttk.Button(buttons_frame, text="Remove Task", command=self._remove_task_dialog)
        remove_button.pack(side=tk.LEFT, padx=5)
        
        run_button = ttk.Button(buttons_frame, text="Run Now", command=self._run_task_now)
        run_button.pack(side=tk.LEFT, padx=5)
        
        # Add treeview for tasks
        self.tasks_tree = ttk.Treeview(
            main_frame,
            columns=("id", "platform", "source", "webhook", "schedule", "enabled", "next_run"),
            show="headings",
            selectmode="browse"
        )
        
        # Configure columns
        self.tasks_tree.heading("id", text="ID")
        self.tasks_tree.heading("platform", text="Platform")
        self.tasks_tree.heading("source", text="Source")
        self.tasks_tree.heading("webhook", text="Webhook")
        self.tasks_tree.heading("schedule", text="Task Schedule")
        self.tasks_tree.heading("enabled", text="Enabled")
        self.tasks_tree.heading("next_run", text="Next Run")
        
        # Configure column widths
        self.tasks_tree.column("id", width=50)
        self.tasks_tree.column("platform", width=80)
        self.tasks_tree.column("source", width=150)
        self.tasks_tree.column("webhook", width=100)
        self.tasks_tree.column("schedule", width=150)
        self.tasks_tree.column("enabled", width=60)
        self.tasks_tree.column("next_run", width=150)
        
        # Add scrollbars
        vsb = ttk.Scrollbar(main_frame, orient="vertical", command=self.tasks_tree.yview)
        hsb = ttk.Scrollbar(main_frame, orient="horizontal", command=self.tasks_tree.xview)
        
        # Grid layout
        self.tasks_tree.grid(row=3, column=0, sticky="nsew")
        vsb.grid(row=3, column=1, sticky="ns")
        hsb.grid(row=4, column=0, sticky="ew")
        
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(3, weight=1)
        
        self.tasks_tree.configure(yscroll=vsb.set, xscroll=hsb.set)
        
        # Add status bar for this tab
        self.status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.grid(row=5, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
    
    def _load_tasks(self):
        """Load tasks from configuration."""
        # Clear existing tasks
        for item in self.tasks_tree.get_children():
            self.tasks_tree.delete(item)
        
        # Add tasks from config
        for task in self._tasks:
            status = "Enabled" if task.get("enabled", True) else "Disabled"
            
            # Format next run time
            next_run = task.get("next_run", "")
            if next_run:
                try:
                    next_run_dt = datetime.fromisoformat(next_run)
                    next_run = next_run_dt.strftime("%Y-%m-%d %H:%M")
                except ValueError:
                    pass
            
            self.tasks_tree.insert("", tk.END, values=(
                task.get("id", ""),
                task.get("platform", ""),
                task.get("source", ""),
                task.get("webhook", ""),
                task.get("schedule", ""),
                status,
                next_run
            ), tags=(task.get("id", "")))
    
    def _refresh_tasks(self):
        """Refresh the tasks list from configuration."""
        logger.info("Refreshing task list")
        # Get fresh tasks from config
        self._tasks = self.config_manager.config.get("scheduled_tasks", [])
        # Reload the tasks into the UI
        self._load_tasks()
    
    def _add_scheduled_task(self, is_edit=False):
        """
        Show the add scheduled task dialog.
        
        Args:
            is_edit: Whether this is editing an existing task
        """
        # Get task to edit (if applicable)
        task = {} if not is_edit else self.task_being_edited
        
        # Create the dialog window
        add_window = tk.Toplevel(self.frame.winfo_toplevel())
        add_window.title(f"{'Edit' if is_edit else 'Add'} Scheduled Task")
        add_window.geometry("600x750")
        add_window.grab_set()  # Make window modal
        
        # Main frame with scrollbar
        main_canvas = tk.Canvas(add_window)
        scrollbar = ttk.Scrollbar(add_window, orient="vertical", command=main_canvas.yview)
        scrollable_frame = ttk.Frame(main_canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all"))
        )
        
        main_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        main_canvas.configure(yscrollcommand=scrollbar.set)
        
        main_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Content frame
        content_frame = ttk.Frame(scrollable_frame)
        content_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Platform selection
        platform_frame = ttk.LabelFrame(content_frame, text="Platform")
        platform_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(platform_frame, text="Platform:").pack(side="left", padx=5, pady=5)
        platform_var = tk.StringVar(value=task.get("platform", "YouTube"))
        platform_combo = ttk.Combobox(platform_frame, textvariable=platform_var, 
                                     values=["YouTube", "Reddit"], state="readonly", width=20)
        platform_combo.pack(side="left", padx=5, pady=5)
        
        # Source section
        source_frame = ttk.LabelFrame(content_frame, text="Content Source")
        source_frame.pack(fill="x", padx=5, pady=5)
        
        # Source option
        source_option_var = tk.StringVar(value="fetched" if not task.get("source") else "manual")
        
        ttk.Radiobutton(source_frame, text="Use fetched videos", variable=source_option_var, 
                        value="fetched").pack(anchor="w", padx=5, pady=5)
        ttk.Radiobutton(source_frame, text="Enter manual source", variable=source_option_var, 
                        value="manual").pack(anchor="w", padx=5, pady=5)
        
        # Manual source entry
        manual_source_frame = ttk.Frame(source_frame)
        manual_source_frame.pack(fill="x", padx=20, pady=5)
        
        ttk.Label(manual_source_frame, text="Source:").pack(side="left", padx=5, pady=5)
        source_var = tk.StringVar(value=task.get("source", ""))
        source_entry = ttk.Entry(manual_source_frame, textvariable=source_var, width=40)
        source_entry.pack(side="left", padx=5, pady=5)
        
        # Source help text
        source_help = tk.StringVar()
        source_help_label = ttk.Label(manual_source_frame, textvariable=source_help)
        source_help_label.pack(side="left", padx=5, pady=5)
        
        def update_source_help(event=None):
            platform = platform_var.get()
            if platform == "YouTube":
                source_help.set("Enter channel ID or search term")
            elif platform == "Reddit":
                source_help.set("Enter subreddit or search term")
        
        platform_combo.bind("<<ComboboxSelected>>", update_source_help)
        update_source_help()  # Initialize with default
        
        # Videos frame (only shown when source_option is "fetched")
        videos_selection_frame = ttk.LabelFrame(content_frame, text="Select Videos to Post")
        videos_selection_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        videos_frame = ttk.Frame(videos_selection_frame)
        videos_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Status var for video loading
        video_status_var = tk.StringVar(value="Loading videos...")
        
        # Create header with refresh button
        videos_header_frame = ttk.Frame(videos_selection_frame)
        videos_header_frame.pack(fill="x", padx=5, pady=5)
        
        # Add refresh button
        def refresh_videos():
            # Get the current platform
            current_platform = platform_var.get()
            
            # Store the video status and tell user we're refreshing
            video_status_var.set("Refreshing videos...")
            add_window.update()
            
            # Clear existing videos
            for widget in videos_frame.winfo_children():
                widget.destroy()
            
            # Clear video vars and frames
            video_vars.clear()
            video_frames.clear()
            
            # Populate with fresh videos
            self._populate_fetched_videos(current_platform, videos_frame, video_status_var, video_vars, video_frames, task)
        
        # Create video checkboxes for selection
        video_vars = []
        video_frames = []
        
        # Add refresh button to header
        ttk.Button(videos_header_frame, text="Refresh Videos", command=refresh_videos).pack(side="right", padx=5)
        ttk.Label(videos_header_frame, textvariable=video_status_var).pack(side="left", padx=5)
        
        # Show/hide manual source based on selection
        def toggle_source_visibility():
            if source_option_var.get() == "manual":
                manual_source_frame.pack(fill="x", padx=20, pady=5)
                videos_selection_frame.pack_forget()
            else:
                manual_source_frame.pack_forget()
                videos_selection_frame.pack(fill="both", expand=True, padx=5, pady=5)
                # Populate videos
                refresh_videos()
        
        # Set up toggle handlers
        source_option_var.trace_add("write", lambda *args: toggle_source_visibility())
        
        # Initialize visibility
        toggle_source_visibility()
        
        # Add webhook selection
        webhook_frame = ttk.LabelFrame(content_frame, text="Webhook")
        webhook_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(webhook_frame, text="Select webhook:").pack(side="left", padx=5, pady=5)
        webhook_var = tk.StringVar(value=task.get("webhook", ""))
        
        # Get webhooks from config
        webhooks = []
        if hasattr(self, "config_manager"):
            webhooks = self.config_manager.config.get("webhooks", [])
        webhook_names = [w.get("name", "") for w in webhooks]
        
        webhook_combo = ttk.Combobox(webhook_frame, textvariable=webhook_var, values=webhook_names, state="readonly")
        webhook_combo.pack(side="left", padx=5, pady=5)
        
        # Add scheduling options
        schedule_frame = ttk.LabelFrame(content_frame, text="Schedule")
        schedule_frame.pack(fill="x", padx=5, pady=5)
        
        # Schedule checkbox
        enabled_var = tk.BooleanVar(value=task.get("enabled", True))
        ttk.Checkbutton(schedule_frame, text="Enable scheduling", variable=enabled_var).pack(anchor="w", padx=5, pady=5)
        
        # Frequency settings
        frequency_frame = ttk.Frame(schedule_frame)
        frequency_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(frequency_frame, text="Run every:").pack(side="left", padx=5)
        interval_value_var = tk.StringVar(value=str(task.get("interval_value", 1)))
        ttk.Spinbox(frequency_frame, from_=1, to=60, textvariable=interval_value_var, width=5).pack(side="left", padx=5)
        
        interval_type_var = tk.StringVar(value=task.get("interval_type", "days"))
        ttk.Combobox(frequency_frame, textvariable=interval_type_var, values=["minutes", "hours", "days", "weeks"], state="readonly", width=10).pack(side="left", padx=5)
        
        # First run settings
        first_run_frame = ttk.Frame(schedule_frame)
        first_run_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(first_run_frame, text="First run:").pack(side="left", padx=5)
        
        # Default to current time if no start time set
        now = datetime.now()
        
        # Parse start time if it exists in the task
        try:
            if task and "start_time" in task:
                start_dt = datetime.fromisoformat(task["start_time"])
            else:
                start_dt = now
        except (ValueError, TypeError):
            start_dt = now
        
        # Date entry
        date_var = tk.StringVar(value=start_dt.strftime("%Y-%m-%d"))
        ttk.Entry(first_run_frame, textvariable=date_var, width=10).pack(side="left", padx=5)
        
        # Time entry
        time_frame = ttk.Frame(first_run_frame)
        time_frame.pack(side="left", padx=5)
        
        hour_var = tk.StringVar(value=start_dt.strftime("%H"))
        ttk.Spinbox(time_frame, from_=0, to=23, textvariable=hour_var, width=2).pack(side="left")
        
        ttk.Label(time_frame, text=":").pack(side="left")
        
        minute_var = tk.StringVar(value=start_dt.strftime("%M"))
        ttk.Spinbox(time_frame, from_=0, to=59, textvariable=minute_var, width=2).pack(side="left")
        
        # Options
        options_frame = ttk.LabelFrame(content_frame, text="Options")
        options_frame.pack(fill="x", padx=5, pady=5)
        
        max_items_frame = ttk.Frame(options_frame)
        max_items_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(max_items_frame, text="Max items to post:").pack(side="left", padx=5)
        max_items_var = tk.StringVar(value=str(task.get("max_items", 1)))
        ttk.Spinbox(max_items_frame, from_=1, to=10, textvariable=max_items_var, width=5).pack(side="left", padx=5)
        
        # Status and buttons
        status_var = tk.StringVar()
        ttk.Label(content_frame, textvariable=status_var, foreground="red").pack(pady=5)
        
        button_frame = ttk.Frame(content_frame)
        button_frame.pack(fill="x", padx=5, pady=10)
        
        # Save function
        def save_task():
            try:
                # Validate inputs
                if source_option_var.get() == "manual" and not source_var.get().strip():
                    status_var.set("Please enter a source")
                    return
                
                if not webhook_var.get():
                    status_var.set("Please select a webhook")
                    return
                
                # Create base task dict
                new_task = {
                    "id": task.get("id", f"task_{int(datetime.now().timestamp())}"),
                    "platform": platform_var.get(),
                    "webhook": webhook_var.get(),
                    "updated": datetime.now().isoformat()
                }
                
                # Add created timestamp if it's a new task
                if not is_edit:
                    new_task["created"] = datetime.now().isoformat()
                elif "created" in task:
                    new_task["created"] = task["created"]
                
                # Add manual source or selected videos
                if source_option_var.get() == "manual":
                    new_task["source"] = source_var.get().strip()
                else:
                    # Get selected videos from video_vars
                    selected_videos = []
                    for i, var in enumerate(video_vars):
                        if var.get() and i < len(video_frames):
                            selected_videos.append(video_frames[i].video)
                    
                    # Only store essential info for each video
                    new_task["selected_videos"] = [
                        {
                            "id": video.get("id", ""),
                            "title": video.get("title", ""),
                            "url": video.get("url", ""),
                            "thumbnail": video.get("thumbnail", ""),
                            "published": video.get("published", "")
                        }
                        for video in selected_videos
                    ]
                
                # Add scheduling info if enabled
                if enabled_var.get():
                    try:
                        # Parse date and time
                        date_str = date_var.get()
                        hour_str = hour_var.get().zfill(2)
                        minute_str = minute_var.get().zfill(2)
                        
                        # Validate date format
                        start_time = datetime.fromisoformat(f"{date_str}T{hour_str}:{minute_str}:00")
                        
                        # Add to task
                        new_task["start_time"] = start_time.isoformat()
                        new_task["interval_value"] = int(interval_value_var.get())
                        new_task["interval_type"] = interval_type_var.get()
                        new_task["enabled"] = True
                        
                        # Create a human-readable schedule string
                        interval_value = int(interval_value_var.get())
                        interval_type = interval_type_var.get()
                        if interval_value == 1:
                            schedule_str = f"Every {interval_type[:-1]}"  # Remove 's' for singular
                        else:
                            schedule_str = f"Every {interval_value} {interval_type}"
                        
                        new_task["schedule"] = schedule_str
                        
                    except ValueError as e:
                        status_var.set(f"Invalid date or time: {e}")
                        return
                else:
                    new_task["enabled"] = False
                    new_task["schedule"] = "Manual"
                
                # Add max items
                try:
                    new_task["max_items"] = int(max_items_var.get())
                except ValueError:
                    new_task["max_items"] = 1
                
                # Save to config
                if hasattr(self, "config_manager"):
                    # Get current tasks
                    tasks = self.config_manager.config.get("scheduled_tasks", [])
                    
                    # Remove old task if editing
                    if is_edit:
                        tasks = [t for t in tasks if t.get("id") != new_task["id"]]
                    
                    # Add the new task
                    tasks.append(new_task)
                    
                    # Update config
                    self.config_manager.config["scheduled_tasks"] = tasks
                    self.config_manager.save_config()
                    
                    # Update UI
                    self._refresh_tasks()
                    
                    # Close window
                    add_window.destroy()
                else:
                    status_var.set("Error: Config manager not available")
            
            except Exception as e:
                logger.error(f"Error saving task: {e}", exc_info=True)
                status_var.set(f"Error: {str(e)}")
        
        # Add buttons
        ttk.Button(button_frame, text="Cancel", command=add_window.destroy).pack(side="right", padx=5)
        ttk.Button(button_frame, text="Save", command=save_task).pack(side="right", padx=5)
    
    def _add_task_dialog(self):
        """Show the add task dialog."""
        # Reuse the existing _add_scheduled_task method
        self._add_scheduled_task()
    
    def _edit_task_dialog(self):
        """Show the edit task dialog."""
        selected = self.tasks_tree.selection()
        if not selected:
            messagebox.showinfo("Info", "Please select a task to edit")
            return
        
        # Get the selected task
        task_id = self.tasks_tree.item(selected[0], "tags")[0]
        task = next((t for t in self.tasks if t.get("id") == task_id), None)
        if not task:
            messagebox.showerror("Error", "Task not found")
            return
        
        # Store the task being edited for reference in the add window
        self.task_being_edited = task
        
        # Open the edit window (we'll modify the add window to handle edits)
        self._add_scheduled_task(is_edit=True)
    
    def _remove_task_dialog(self):
        """Show the remove task confirmation dialog."""
        selected = self.tasks_tree.selection()
        if not selected:
            messagebox.showinfo("Info", "Please select a task to remove")
            return
        
        # Get the selected task
        task_id = self.tasks_tree.item(selected[0], "tags")[0]
        
        # Confirm deletion
        if messagebox.askyesno("Confirm", "Are you sure you want to remove this task?"):
            # Remove the task from the list
            self.tasks = [t for t in self.tasks if t.get("id") != task_id]
            
            # Save to config
            self.save_tasks()
            
            # Refresh the display
            self._load_tasks()
    
    def _toggle_task(self):
        """Enable or disable a scheduled task."""
        selected = self.tasks_tree.selection()
        if not selected:
            messagebox.showinfo("Info", "Please select a task to toggle")
            return
        
        # Get the selected task
        task_id = self.tasks_tree.item(selected[0], "tags")[0]
        
        # Find the task and toggle its state
        for task in self.tasks:
            if task.get("id") == task_id:
                task["enabled"] = not task.get("enabled", True)
                break
        
        # Save to config
        self.save_tasks()
        
        # Refresh the display
        self._load_tasks()
    
    def _run_task_now(self):
        """Run the selected task immediately."""
        selection = self.tasks_tree.selection()
        if not selection:
            messagebox.showwarning("No Task Selected", "Please select a task to run.")
            return
        
        # Get the task ID from the selected item
        task_id = self.tasks_tree.item(selection[0])['values'][0]
        logger.info(f"Running task with ID: {task_id}")
        
        # Find the task in the list
        task = next((t for t in self._tasks if str(t.get('id')) == str(task_id)), None)
        if not task:
            messagebox.showerror("Task Error", f"Task with ID {task_id} not found.")
            return
        
        # Update the status
        self.status_var.set(f"Running task: {task.get('source')}")
        
        # Run the task in a separate thread
        threading.Thread(target=self._execute_task, args=(task,), daemon=True).start()
    
    def _execute_task(self, task):
        """
        Execute a scheduled task.
        
        Args:
            task: Task to execute
        """
        platform = task.get("platform", "").lower()
        webhook_name = task.get("webhook", "")
        source = task.get("source", "")
        max_items = task.get("max_items", 5)
        
        # Check if we have selected videos saved
        has_selected_videos = "selected_videos" in task and task["selected_videos"]
        selected_video_ids = [video.get("id") for video in task.get("selected_videos", [])]
        
        logger.info(f"Executing task: ID={task.get('id')}, Platform={platform}, Webhook={webhook_name}")
        logger.info(f"Has selected videos: {has_selected_videos}, Count: {len(selected_video_ids) if selected_video_ids else 0}")
        
        try:
            # Get connectors
            source_connector = None
            discord_connector = None
            
            try:
                # Try to import connectors using factory
                from src.api_connectors.factory import get_connector
                
                # Get API credentials for the platform
                platform_credentials = {}
                if hasattr(self, 'config_manager'):
                    platform_credentials = self.config_manager.credentials.get(platform, {})
                else:
                    logger.warning("No config_manager available, using empty credentials")
                
                # Create the connectors with the appropriate credentials
                source_connector = get_connector(platform, platform_credentials)
                logger.info(f"Created {platform} connector with credentials")
                
                discord_credentials = {}
                if hasattr(self, 'config_manager'):
                    discord_credentials = self.config_manager.credentials.get("discord", {})
                
                discord_connector = get_connector("discord", discord_credentials)
                logger.info(f"Created Discord connector with credentials")
            except ImportError as e:
                logger.error(f"Error importing connector factory: {e}", exc_info=True)
                # Try direct imports if the factory isn't available
                try:
                    if platform == "youtube":
                        from src.api_connectors.youtube import YouTubeConnector
                        platform_credentials = {}
                        if hasattr(self, 'config_manager'):
                            platform_credentials = self.config_manager.credentials.get(platform, {})
                        source_connector = YouTubeConnector(platform_credentials)
                    
                    from src.api_connectors.discord import DiscordConnector
                    discord_credentials = {}
                    if hasattr(self, 'config_manager'):
                        discord_credentials = self.config_manager.credentials.get("discord", {})
                    discord_connector = DiscordConnector(discord_credentials)
                except ImportError as e2:
                    error_msg = f"Error importing connectors: {e2}"
                    logger.error(error_msg)
                    self.status_var.set(f"Error: {error_msg}")
                    messagebox.showerror("Import Error", error_msg)
                    return
            
            # Get the webhook URL
            webhook = None
            if hasattr(self, 'config_manager'):
                webhooks = self.config_manager.config.get("webhooks", [])
                for wh in webhooks:
                    if wh.get("name") == webhook_name:
                        webhook = wh
                        break
            
            if not webhook:
                error_msg = f"Webhook '{webhook_name}' not found"
                logger.error(error_msg)
                self.status_var.set(f"Error: {error_msg}")
                messagebox.showerror("Webhook Error", error_msg)
                return
            
            # Fetch content
            self.status_var.set(f"Fetching content from {platform}...")
            
            # Always prioritize using the selected videos if they exist
            items = []
            
            if has_selected_videos:
                logger.info("Using task's selected videos")
                items = task["selected_videos"]
                
                # Make sure each item has the necessary fields for posting
                for item in items:
                    # Ensure URL is present
                    if "id" in item and not item.get("url"):
                        # Construct URL if missing but ID is present
                        item["url"] = f"https://www.youtube.com/watch?v={item['id']}"
                    
                    # Ensure thumbnail URL is present
                    if not item.get("thumbnail") and "id" in item:
                        # Use YouTube thumbnail format if missing
                        item["thumbnail"] = f"https://img.youtube.com/vi/{item['id']}/hqdefault.jpg"
                
                logger.info(f"Found {len(items)} selected videos to post")
            else:
                # Only fetch from API if no selected videos
                logger.info(f"No selected videos found, fetching from API with max_items={max_items}")
                
                if platform == "youtube":
                    # Check if source is a channel ID or a search term
                    if source and source.startswith("UC"):  # YouTube channel IDs start with UC
                        logger.info(f"Fetching from YouTube channel: {source}")
                        items = source_connector.fetch(channel_id=source, max_results=max_items)
                    elif source:
                        logger.info(f"Searching YouTube for: {source}")
                        items = source_connector.fetch(query=source, max_results=max_items)
                    else:
                        logger.warning("No source specified for YouTube")
            
            logger.info(f"Final list contains {len(items) if items else 0} items to post")
            
            # Send to Discord
            if items:
                self.status_var.set(f"Sending {len(items)} items to Discord...")
                
                for item in items:
                    # Create an embed for the item
                    embed = {
                        "title": item.get("title", ""),
                        "description": item.get("description", "")[:200] + "..." if item.get("description", "") else "",
                        "url": item.get("url", ""),
                        "color": 0x00ff00,  # Green
                        "thumbnail": {"url": item.get("thumbnail", "")},
                        "fields": [
                            {"name": "Source", "value": platform.capitalize(), "inline": True},
                            {"name": "Published", "value": item.get("published", ""), "inline": True}
                        ]
                    }
                    
                    # Log the message being sent
                    logger.info(f"Sending embed: {embed['title']}")
                    
                    # Send the message
                    discord_connector.send_webhook_message(
                        webhook["url"],
                        content=f"New content from {platform.capitalize()}",
                        embeds=[embed]
                    )
                
                self.status_var.set(f"Task completed: Sent {len(items)} items to Discord")
                logger.info(f"Task completed successfully")
                
                # Update next run time
                self._update_task_next_run(task)
            else:
                no_items_msg = f"No items found from {platform}"
                self.status_var.set(no_items_msg)
                logger.warning(no_items_msg)
                messagebox.showinfo("No Content", no_items_msg)
            
        except Exception as e:
            error_msg = f"Error executing task: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.status_var.set(error_msg)
            messagebox.showerror("Task Error", error_msg)
    
    def _update_task_next_run(self, task):
        """
        Update the next run time for a task.
        
        Args:
            task: Task to update
        """
        # Parse interval string if it exists
        if "interval" in task and isinstance(task["interval"], str):
            parts = task["interval"].split()
            if len(parts) >= 2:
                task["interval_value"] = int(parts[0])
                task["interval_type"] = parts[1]
        
        interval_value = task.get("interval_value", 1)
        interval_type = task.get("interval_type", "hours")
        
        # Calculate the next run time
        now = datetime.now()
        
        if interval_type == "minutes":
            next_run = now + timedelta(minutes=interval_value)
        elif interval_type == "hours":
            next_run = now + timedelta(hours=interval_value)
        elif interval_type == "days":
            next_run = now + timedelta(days=interval_value)
        elif interval_type == "weeks":
            next_run = now + timedelta(weeks=interval_value)
        else:
            next_run = now + timedelta(hours=1)  # Default to 1 hour
        
        # Update the task
        task["next_run"] = next_run.isoformat()
        
        # Save the changes
        self.save_tasks()
        
        # Refresh the display
        self._load_tasks()
    
    def save_tasks(self):
        """Save tasks to configuration."""
        try:
            logger.info(f"save_tasks called with {len(self._tasks)} tasks")
            for i, task in enumerate(self._tasks):
                logger.info(f"Task {i}: ID={task.get('id')}, Platform={task.get('platform')}")
            
            # Try direct file approach first
            config_file = os.path.join(self.config_manager.config_dir, "config.json")
            logger.info(f"Direct save to config file: {config_file}")
            logger.info(f"Config manager dir: {self.config_manager.config_dir}")
            
            # Check if config file exists
            if not os.path.exists(config_file):
                logger.error(f"Config file not found: {config_file}")
                logger.info("Falling back to config_manager.update_config")
            else:
                # Read current config
                try:
                    with open(config_file, 'r') as f:
                        config = json.load(f)
                    logger.info(f"Successfully read config with {len(config.keys())} keys")
                    
                    # Update scheduled_tasks
                    config['scheduled_tasks'] = self._tasks
                    logger.info(f"Updated config scheduled_tasks with {len(self._tasks)} tasks")
                    
                    # Write back to file
                    with open(config_file, 'w') as f:
                        json.dump(config, f, indent=4)
                    logger.info(f"Successfully wrote updated config back to file")
                    
                    # Update config manager's cache
                    if hasattr(self, 'config_manager'):
                        self.config_manager.config = config
                    logger.info("Updated config manager's in-memory config")
                    
                    # Notify observers manually
                    if hasattr(self, 'config_manager'):
                        self.config_manager._notify_observers()
                    logger.info("Manually notified observers")
                    
                    return
                except Exception as e:
                    logger.error(f"Error with direct file approach: {e}", exc_info=True)
                    logger.info("Falling back to config_manager.update_config")
            
            # Fallback to original approach
            before_tasks = []
            if hasattr(self, 'config_manager'):
                before_tasks = self.config_manager.config.get("scheduled_tasks", [])
            logger.info(f"Before update: Config has {len(before_tasks)} tasks")
            
            if hasattr(self, 'config_manager'):
                self.config_manager.update_config("scheduled_tasks", self._tasks)
            
            after_tasks = []
            if hasattr(self, 'config_manager'):
                after_tasks = self.config_manager.config.get("scheduled_tasks", [])
            logger.info(f"After update: Config has {len(after_tasks)} tasks")
            logger.info("Tasks saved successfully")
        except Exception as e:
            logger.error(f"Error in save_tasks: {e}", exc_info=True)
            raise
    
    def on_config_changed(self):
        """Called when configuration changes."""
        try:
            logger.info("on_config_changed called")
            old_tasks_count = len(self._tasks)
            
            # Get updated tasks from config
            self._tasks = []
            if hasattr(self, 'config_manager'):
                self._tasks = self.config_manager.config.get("scheduled_tasks", [])
            new_tasks_count = len(self._tasks)
            
            logger.info(f"Tasks updated: {old_tasks_count} -> {new_tasks_count}")
            
            # Reload task list
            self._load_tasks()
            logger.info("Task list reloaded")
        except Exception as e:
            logger.error(f"Error in on_config_changed: {e}", exc_info=True)
    
    def _populate_content_listbox(self, listbox, platform):
        """Populate the content listbox with fetched content."""
        # Clear existing content
        listbox.delete(0, tk.END)
        
        # Get fetched content from the fetching tab
        if self.fetching_tab:
            content = self.fetching_tab.get_fetched_content(platform)
            if content:
                for item in content:
                    # Get the display text to show in listbox
                    display_text = item.get("display_text", "Unknown content")
                    
                    # Save the item's source ID as well
                    source_id = item.get("source_id", "")
                    
                    # Add to listbox
                    listbox.insert(tk.END, display_text)
    
    def _toggle_content_source(self, use_fetched, listbox, entry):
        """Toggle between using fetched content and manual entry."""
        if use_fetched:
            listbox.config(state="normal")
            entry.config(state="disabled")
        else:
            listbox.config(state="disabled")
            entry.config(state="normal")

    def _populate_fetched_videos(self, platform, videos_frame, status_var, video_vars, video_frames, task=None):
        """
        Populate the videos frame with fetched videos from the specified platform.
        
        Args:
            platform: Platform to get videos from
            videos_frame: Frame to populate with videos
            status_var: StringVar for status updates
            video_vars: List to store video checkbox variables
            video_frames: List to store video frames
            task: Task data if this is an edit operation
        """
        # Clear any existing videos
        for widget in videos_frame.winfo_children():
            widget.destroy()
        
        # Clear our tracking lists
        video_vars.clear()
        video_frames.clear()
        
        # Update status
        status_var.set(f"Fetching videos from {platform}...")
        
        try:
            # Get videos from the fetching tab
            fetching_tab = self.fetching_tab
            if not fetching_tab:
                status_var.set("Error: Fetching tab not available")
                return
            
            # Get videos from the platform
            videos = fetching_tab.get_fetched_content(platform)
            
            if not videos:
                status_var.set(f"No videos found for {platform}. Please fetch videos first.")
                return
            
            # Create a canvas for scrolling
            canvas = tk.Canvas(videos_frame)
            scrollbar = ttk.Scrollbar(videos_frame, orient="vertical", command=canvas.yview)
            scrollable_frame = ttk.Frame(canvas)
            
            scrollable_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )
            
            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)
            
            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
            
            # Track videos that are already selected from the task
            selected_video_ids = []
            if task and "selected_videos" in task:
                selected_video_ids = [v.get("id") for v in task.get("selected_videos", [])]
            
            # Create video selection checkboxes
            for i, video in enumerate(videos):
                # Create a frame for this video
                video_frame = ttk.Frame(scrollable_frame)
                video_frame.pack(fill="x", padx=5, pady=5, anchor="w")
                
                # Determine if this video should be pre-selected
                is_selected = video.get("id") in selected_video_ids
                var = tk.BooleanVar(value=is_selected)
                video_vars.append(var)
                
                # Add checkbox with video title
                title = video.get("title", "Untitled Video")
                checkbox = ttk.Checkbutton(
                    video_frame, 
                    text=title, 
                    variable=var,
                    width=60
                )
                checkbox.pack(side="left", fill="x", expand=True, anchor="w")
                
                # Add video details
                if "published" in video:
                    published = video.get("published", "")
                    if isinstance(published, str):
                        # Try to parse the date if it's a string
                        try:
                            dt = datetime.fromisoformat(published.replace('Z', '+00:00'))
                            published = dt.strftime("%Y-%m-%d")
                        except (ValueError, AttributeError):
                            # Keep as is if parsing fails
                            pass
                    
                    # Add published date
                    ttk.Label(
                        video_frame, 
                        text=f"Published: {published}"
                    ).pack(side="right", padx=5)
                
                # Store the video for retrieval
                video_frame.video = video
                video_frames.append(video_frame)
            
            # Store the items on the frame for reference
            videos_frame.items = videos
            
            # Add "Select All" and "Deselect All" buttons
            buttons_frame = ttk.Frame(scrollable_frame)
            buttons_frame.pack(fill="x", padx=5, pady=5, anchor="w")
            
            def select_all():
                for var in video_vars:
                    var.set(True)
            
            def deselect_all():
                for var in video_vars:
                    var.set(False)
            
            ttk.Button(buttons_frame, text="Select All", command=select_all).pack(side="left", padx=5)
            ttk.Button(buttons_frame, text="Deselect All", command=deselect_all).pack(side="left", padx=5)
            
            # Update status
            status_var.set(f"Found {len(videos)} videos from {platform}")
        
        except Exception as e:
            logger.error(f"Error populating videos: {e}", exc_info=True)
            status_var.set(f"Error: {str(e)}")
    
    def _populate_task_selected_videos(self, task, videos_frame, status_var, video_vars, video_frames):
        """
        Populate the videos frame with a task's selected videos.
        
        Args:
            task: Task with selected videos
            videos_frame: Frame to populate
            status_var: Status variable to update
            video_vars: List to store video checkbox variables
            video_frames: List to store video frames
        """
        # Clear existing video frames
        for frame in video_frames:
            frame.destroy()
        video_frames.clear()
        video_vars.clear()
        
        # Remove all existing widgets
        for widget in videos_frame.winfo_children():
            widget.destroy()
        
        # Add loading indicator
        loading_label = ttk.Label(
            videos_frame, 
            text="Loading selected videos... Please wait",
            wraplength=400,
            justify="center"
        )
        loading_label.pack(expand=True, fill="both", padx=20, pady=40)
        videos_frame.update()
        
        try:
            # Get the task's selected videos
            selected_videos = task.get("selected_videos", [])
            
            # Remove loading indicator
            loading_label.destroy()
            
            if not selected_videos:
                status_var.set("No selected videos found")
                no_videos_label = ttk.Label(
                    videos_frame, 
                    text="No videos were selected for this task.",
                    wraplength=400,
                    justify="center",
                    foreground="red"
                )
                no_videos_label.pack(expand=True, fill="both", padx=20, pady=40)
                return
            
            # Display selected videos with checkboxes
            status_var.set(f"Found {len(selected_videos)} selected videos")
            
            # Create header
            header_frame = ttk.Frame(videos_frame)
            header_frame.pack(fill="x", padx=5, pady=10, anchor="w")
            
            select_all_var = tk.BooleanVar(value=True)
            
            def toggle_all():
                new_state = select_all_var.get()
                for var in video_vars:
                    var.set(new_state)
            
            select_all_cb = ttk.Checkbutton(
                header_frame, 
                text="Select/Deselect All", 
                variable=select_all_var,
                command=toggle_all
            )
            select_all_cb.pack(side="left", padx=(5, 20))
            
            ttk.Label(header_frame, text=f"Total videos: {len(selected_videos)}").pack(side="left")
            
            # Create a scrollable frame for videos
            canvas_frame = ttk.Frame(videos_frame)
            canvas_frame.pack(fill="both", expand=True, padx=5, pady=5)
            
            canvas = tk.Canvas(canvas_frame)
            scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
            scrollable_frame = ttk.Frame(canvas)
            
            scrollable_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )
            
            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)
            
            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
            
            # Create a checkbox for each video
            for i, item in enumerate(selected_videos):
                var = tk.BooleanVar(value=True)  # Default to selected
                video_vars.append(var)
                
                # Create a frame for this video
                frame = ttk.Frame(scrollable_frame)
                frame.pack(fill="x", padx=5, pady=5, anchor="w")
                video_frames.append(frame)
                
                # Get title from the video item
                if isinstance(item, dict):
                    if "title" in item:
                        title = item["title"]
                    elif "snippet" in item and "title" in item["snippet"]:
                        title = item["snippet"]["title"]
                    else:
                        title = f"Video {i+1}"
                else:
                    title = f"Video {i+1}"
                
                # Add checkbox
                cb = ttk.Checkbutton(
                    frame, 
                    text=title,
                    variable=var
                )
                cb.pack(side="left", anchor="w")
                
                # Add tooltip for full title
                if len(title) > 50:
                    # Simple tooltip using a label that appears on hover
                    tooltip = None
                    tooltip_text = title
                    
                    def enter(event, tooltip_text=tooltip_text):
                        nonlocal tooltip
                        x = event.widget.winfo_rootx() + 25
                        y = event.widget.winfo_rooty() + 20
                        
                        # Create a toplevel window
                        tooltip = tk.Toplevel(event.widget)
                        tooltip.wm_overrideredirect(True)
                        tooltip.wm_geometry(f"+{x}+{y}")
                        
                        label = tk.Label(tooltip, text=tooltip_text, wraplength=400,
                                      background="#ffffe0", relief="solid", borderwidth=1)
                        label.pack(padx=2, pady=2)
                    
                    def leave(event):
                        nonlocal tooltip
                        if tooltip:
                            tooltip.destroy()
                            tooltip = None
                    
                    cb.bind("<Enter>", enter)
                    cb.bind("<Leave>", leave)
                    
                    # Also enable tooltip for the video details line
                    def create_tooltip(widget, tooltip_text):
                        tooltip = None
                        
                        def enter(event):
                            nonlocal tooltip
                            x = event.widget.winfo_rootx() + 25
                            y = event.widget.winfo_rooty() + 20
                            
                            # Create a toplevel window
                            tooltip = tk.Toplevel(widget)
                            tooltip.wm_overrideredirect(True)
                            tooltip.wm_geometry(f"+{x}+{y}")
                            
                            label = tk.Label(tooltip, text=tooltip_text, wraplength=400,
                                          background="#ffffe0", relief="solid", borderwidth=1)
                            label.pack(padx=2, pady=2)
                        
                        def leave(event):
                            nonlocal tooltip
                            if tooltip:
                                tooltip.destroy()
                                tooltip = None
                        
                        widget.bind("<Enter>", enter)
                        widget.bind("<Leave>", leave)
                    
                    create_tooltip(cb, title)
                
                # Add publish date if available
                if "published" in item:
                    date_label = ttk.Label(frame, text=f"({item.get('published', '')})")
                    date_label.pack(side="left", padx=5)
                
                # Add a thumbnail indicator if available
                if "thumbnail" in item and item["thumbnail"]:
                    # Just show a placeholder text for the thumbnail
                    thumb_label = ttk.Label(frame, text="[Thumbnail]", foreground="blue")
                    thumb_label.pack(side="right", padx=5)
            
            # Store items for later use when saving
            videos_frame.items = selected_videos
            
            # Update canvas
            videos_frame.update_idletasks()
            if hasattr(videos_frame.master, "config") and hasattr(videos_frame.master, "bbox"):
                videos_frame.master.config(scrollregion=videos_frame.master.bbox("all"))

            # Clear any source-related prompt messages at the bottom of the dialog
            # Only if we have a dialog instance
            if hasattr(self, 'dialog') and self.dialog is not None:
                try:
                    # Find the status message at the bottom of the dialog
                    for widget in self.dialog.winfo_children():
                        if isinstance(widget, ttk.Label) and hasattr(widget, 'cget'):
                            try:
                                if widget.cget('text') == "Please enter a source":
                                    widget.config(text="")
                            except:
                                pass
                except Exception as e:
                    # Just log and continue if there's any issue clearing messages
                    logger.debug(f"Error clearing source message: {e}")
            
        except Exception as e:
            logger.error(f"Error loading selected videos: {e}", exc_info=True)
            status_var.set(f"Error: {str(e)}")
            
            # Show error in the videos frame
            for widget in videos_frame.winfo_children():
                widget.destroy()
            
            error_label = ttk.Label(
                videos_frame, 
                text=f"Error loading selected videos:\n{str(e)}",
                wraplength=400,
                justify="center",
                foreground="red"
            )
            error_label.pack(expand=True, fill="both", padx=20, pady=40)

# For backward compatibility
ScheduleTab = TasksTab
