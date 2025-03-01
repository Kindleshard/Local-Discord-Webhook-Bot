"""
Base UI component for Discord Webhook Bot.

Contains common UI utilities, styles, and dialog creation functions.
"""

import os
import json
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import logging
from abc import ABC, abstractmethod

# Configure logger
logger = logging.getLogger(__name__)

class StyleManager:
    """Manages UI style and themes for the application."""
    
    THEMES = {
        'default': {
            'button': {'background': '#4a6ea9', 'foreground': 'white'},
            'frame': {'background': '#f5f5f5'},
            'label': {'background': '#f5f5f5', 'foreground': '#333333'},
            'entry': {'background': 'white', 'foreground': '#333333'},
            'treeview': {'background': 'white', 'foreground': '#333333'},
            'tab': {'background': '#e1e1e1'}
        },
        'dark': {
            'button': {'background': '#2c3e50', 'foreground': 'white'},
            'frame': {'background': '#34495e'},
            'label': {'background': '#34495e', 'foreground': '#ecf0f1'},
            'entry': {'background': '#2c3e50', 'foreground': '#ecf0f1'},
            'treeview': {'background': '#2c3e50', 'foreground': '#ecf0f1'},
            'tab': {'background': '#2c3e50'}
        }
    }
    
    @classmethod
    def configure(cls, style, theme_name='default'):
        """Configure the style for the application."""
        style.theme_use('clam')
        
        # Apply theme to ttk elements
        theme = cls.THEMES.get(theme_name, cls.THEMES['default'])
        style.configure('TButton', **theme['button'])
        style.configure('TFrame', **theme['frame'])
        style.configure('TLabel', **theme['label'])
        style.configure('TEntry', **theme['entry'])
        style.configure('Treeview', **theme['treeview'])
        style.configure('TNotebook.Tab', **theme['tab'])
        
        return style


class ConfigManager:
    """Manages application configuration with observer pattern."""
    
    def __init__(self, config_dir):
        self.config_dir = config_dir
        self.config_file = os.path.join(config_dir, "config.json")
        self.credentials_file = os.path.join(config_dir, "credentials.json")
        self.config = self._load_config()
        self.credentials = self._load_credentials()
        self.observers = []
    
    def add_observer(self, callback):
        """Add an observer that will be notified of config changes."""
        self.observers.append(callback)
    
    def update_config(self, section, values):
        """Update a section of the config and notify observers."""
        try:
            logger.info(f"update_config called for section: {section} with {len(values) if isinstance(values, list) else 'non-list'} values")
            old_values = self.config.get(section, None)
            logger.info(f"Previous values in section {section}: {type(old_values).__name__}, {len(old_values) if isinstance(old_values, list) else 'N/A'}")
            
            self.config[section] = values
            logger.info(f"Updated config[{section}] = {type(values).__name__} with {len(values) if isinstance(values, list) else 'N/A'} items")
            
            self._save_config()
            logger.info(f"Config saved to {self.config_file}")
            
            self._notify_observers()
            logger.info(f"Notified {len(self.observers)} observers")
        except Exception as e:
            logger.error(f"Error in update_config: {e}", exc_info=True)
            raise
    
    def update_credentials(self, section, values):
        """Update credentials and notify observers."""
        self.credentials[section] = values
        self._save_credentials()
        self._notify_observers()
    
    def _notify_observers(self):
        """Notify all observers of a change."""
        logger.info(f"Notifying {len(self.observers)} observers of config change...")
        for i, callback in enumerate(self.observers):
            try:
                logger.info(f"Calling observer {i+1}...")
                callback()
                logger.info(f"Observer {i+1} notified successfully")
            except Exception as e:
                logger.error(f"Error notifying observer {i+1}: {e}", exc_info=True)
    
    def _load_config(self):
        """Load configuration from file."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, "r") as f:
                    return json.load(f)
            return {"webhooks": [], "scheduled_tasks": []}
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return {"webhooks": [], "scheduled_tasks": []}
    
    def _load_credentials(self):
        """Load credentials from file."""
        try:
            if os.path.exists(self.credentials_file):
                with open(self.credentials_file, "r") as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Error loading credentials: {e}")
            return {}
    
    def _save_config(self):
        """Save configuration to file."""
        try:
            logger.info(f"Saving config to {self.config_file}")
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            
            # Count scheduled tasks before save
            tasks_before = len(self.config.get("scheduled_tasks", []))
            logger.info(f"Config has {tasks_before} scheduled tasks before save")
            
            with open(self.config_file, "w") as f:
                json.dump(self.config, f, indent=4)
            
            # Verify the save by reading back the file
            if os.path.exists(self.config_file):
                with open(self.config_file, "r") as f:
                    saved_config = json.load(f)
                    tasks_after = len(saved_config.get("scheduled_tasks", []))
                    logger.info(f"Saved config has {tasks_after} scheduled tasks")
            
            logger.info(f"Config saved successfully to {self.config_file}")
        except Exception as e:
            logger.error(f"Error saving config: {e}", exc_info=True)
    
    def _save_credentials(self):
        """Save credentials to file."""
        try:
            os.makedirs(os.path.dirname(self.credentials_file), exist_ok=True)
            with open(self.credentials_file, "w") as f:
                json.dump(self.credentials, f, indent=4)
        except Exception as e:
            logger.error(f"Error saving credentials: {e}")
    
    def save_config(self):
        """Public method to save configuration to file."""
        logger.info("save_config called")
        self._save_config()


class DialogHelper:
    """Helper class for creating dialogs."""
    
    @staticmethod
    def create_dialog(parent, title, fields, width=300, height=None):
        """
        Create a dialog with specified fields.
        
        Args:
            parent: Parent window
            title: Dialog title
            fields: List of tuples (label, default_value)
            width: Dialog width (default 300)
            height: Dialog height (optional)
            
        Returns:
            tuple: (dialog, entries)
        """
        dialog = tk.Toplevel(parent)
        dialog.title(title)
        dialog.transient(parent)
        dialog.grab_set()
        
        # Set default size
        if height:
            dialog.geometry(f"{width}x{height}")
        else:
            dialog.geometry(f"{width}x{100 + 40*len(fields)}")
        
        # Create a main frame with padding
        main_frame = ttk.Frame(dialog, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        entries = []
        for i, (label, default) in enumerate(fields):
            # Create label frame for each field for better organization
            field_frame = ttk.Frame(main_frame)
            field_frame.pack(fill=tk.X, pady=5)
            
            label_widget = ttk.Label(field_frame, text=label)
            label_widget.pack(anchor='w', pady=(0, 2))
            
            entry = ttk.Entry(field_frame, width=40)
            if default:
                entry.insert(0, default)
            entry.pack(fill=tk.X)
            entries.append(entry)
        
        return dialog, entries
    
    @staticmethod
    def create_webhook_dialog(parent, title, webhook=None):
        """
        Create a comprehensive webhook dialog.
        
        Args:
            parent: Parent window
            title: Dialog title
            webhook: Existing webhook data (optional)
            
        Returns:
            tuple: (dialog, form_data)
        """
        dialog = tk.Toplevel(parent)
        dialog.title(title)
        dialog.transient(parent)
        dialog.grab_set()
        dialog.geometry("450x300")
        
        # Create a main frame with padding
        main_frame = ttk.Frame(dialog, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Webhook details section
        details_frame = ttk.LabelFrame(main_frame, text="Webhook Details")
        details_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Name field
        name_frame = ttk.Frame(details_frame)
        name_frame.pack(fill=tk.X, pady=5, padx=10)
        
        ttk.Label(name_frame, text="Name:").pack(anchor='w', pady=(5, 2))
        name_var = tk.StringVar(value=webhook.get("name", "") if webhook else "")
        name_entry = ttk.Entry(name_frame, width=40, textvariable=name_var)
        name_entry.pack(fill=tk.X)
        
        # URL field
        url_frame = ttk.Frame(details_frame)
        url_frame.pack(fill=tk.X, pady=5, padx=10)
        
        ttk.Label(url_frame, text="URL:").pack(anchor='w', pady=(5, 2))
        url_var = tk.StringVar(value=webhook.get("url", "") if webhook else "")
        url_entry = ttk.Entry(url_frame, width=40, textvariable=url_var)
        url_entry.pack(fill=tk.X)
        
        # Help text
        help_frame = ttk.Frame(details_frame)
        help_frame.pack(fill=tk.X, pady=5, padx=10)
        
        help_text = """
        Webhook URL format: https://discord.com/api/webhooks/{webhook.id}/{webhook.token}
        You can get this URL from Discord server settings > Integrations > Webhooks
        """
        ttk.Label(help_frame, text=help_text, wraplength=400, justify=tk.LEFT, foreground="#555555").pack(anchor='w')
        
        form_data = {
            "name_var": name_var,
            "url_var": url_var,
            "name_entry": name_entry,
            "url_entry": url_entry
        }
        
        return dialog, form_data
    
    @staticmethod
    def add_button_frame(dialog, save_callback, cancel_callback):
        """
        Add buttons to dialog.
        
        Args:
            dialog: Dialog window
            save_callback: Function to call when Save is clicked
            cancel_callback: Function to call when Cancel is clicked
            
        Returns:
            frame: Button frame
        """
        button_frame = ttk.Frame(dialog)
        
        # Check if we're adding to a grid or pack layout
        if any(child.grid_info() for child in dialog.winfo_children()):
            button_frame.grid(row=len(dialog.winfo_children()) - 1, column=0, columnspan=2, pady=10)
        else:
            button_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10)
            
        ttk.Button(button_frame, text="Save", command=save_callback, width=10).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=cancel_callback, width=10).pack(side=tk.LEFT, padx=5)
        
        return button_frame


class BaseUI(ABC):
    """Base UI class for tab components."""
    
    def __init__(self, parent, config_manager, tab_name):
        """
        Initialize base UI component.
        
        Args:
            parent: Parent frame
            config_manager: Configuration manager instance
            tab_name: Name of this tab
        """
        self.parent = parent
        self.config_manager = config_manager
        self.tab_name = tab_name
        
        # Create the frame but DO NOT pack it
        # It will be added to the notebook via notebook.add() later
        self.frame = ttk.Frame(parent)
        
        # Initialize UI
        self._init_ui()
        
        # Subscribe to config changes
        self.config_manager.add_observer(self.on_config_changed)
    
    @abstractmethod
    def _init_ui(self):
        """Initialize the UI components."""
        pass
    
    def on_config_changed(self):
        """Called when configuration changes."""
        pass
    
    def run_async(self, task, callback):
        """
        Run a task asynchronously.
        
        Args:
            task: Function to run
            callback: Function to call with result
        """
        import threading
        
        def _run():
            try:
                result = task()
                self.parent.after(0, lambda: callback(result))
            except Exception as e:
                logger.error(f"Error in async task: {e}")
                self.parent.after(0, lambda: messagebox.showerror("Error", str(e)))
        
        threading.Thread(target=_run).start()
    
    def create_scrollable_frame(self, parent):
        """
        Create a scrollable frame.
        
        Args:
            parent: Parent widget
            
        Returns:
            tuple: (container_frame, scrollable_frame)
        """
        # Create a frame to hold the canvas and scrollbar
        container = ttk.Frame(parent)
        
        # Create canvas
        canvas = tk.Canvas(container, borderwidth=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        # Configure scrolling
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        # Add the scrollable frame to the canvas
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack everything
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        return container, scrollable_frame
    
    def create_treeview(self, parent, columns, show="headings"):
        """
        Create a treeview with specified columns.
        
        Args:
            parent: Parent widget
            columns: List of tuples (column_id, column_name, width)
            show: What to show (headings, tree, both)
            
        Returns:
            tuple: (treeview, scrollbar)
        """
        # Create a frame to hold the treeview and scrollbar
        tree_frame = ttk.Frame(parent)
        
        # Create scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient="vertical")
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal")
        
        # Create the treeview
        column_ids = [col[0] for col in columns]
        tree = ttk.Treeview(tree_frame, columns=column_ids, show=show,
                           yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        # Configure scrollbars
        vsb.config(command=tree.yview)
        hsb.config(command=tree.xview)
        
        # Configure columns
        for col_id, col_name, col_width in columns:
            tree.heading(col_id, text=col_name)
            tree.column(col_id, width=col_width, minwidth=50)
        
        # Grid layout
        tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        
        # Configure grid weights
        tree_frame.rowconfigure(0, weight=1)
        tree_frame.columnconfigure(0, weight=1)
        
        return tree_frame, tree
