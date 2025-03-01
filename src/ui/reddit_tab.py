"""
Reddit Tab UI Component.

Manages Reddit content search and display.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import logging
import webbrowser
from .base_ui import BaseUI
import threading

logger = logging.getLogger(__name__)


class RedditSearchOptions:
    """Container for Reddit search options."""
    
    # Sort options
    SORT_OPTIONS = [
        {"name": "Hot", "value": "hot"},
        {"name": "New", "value": "new"},
        {"name": "Top", "value": "top"}
    ]
    
    # Time filter options
    TIME_FILTER_OPTIONS = [
        {"name": "Hour", "value": "hour"},
        {"name": "Day", "value": "day"},
        {"name": "Week", "value": "week"},
        {"name": "Month", "value": "month"},
        {"name": "Year", "value": "year"},
        {"name": "All Time", "value": "all"}
    ]
    
    # Result count options
    RESULT_OPTIONS = [5, 10, 15, 25, 50]


class RedditTab(BaseUI):
    """Tab for searching and posting Reddit content."""
    
    def __init__(self, parent, config_manager):
        """
        Initialize the Reddit tab.
        
        Args:
            parent: Parent widget
            config_manager: Configuration manager
        """
        super().__init__(parent, config_manager, "Reddit")
        self.results = []
        self._init_ui()
    
    def _init_ui(self):
        """Initialize the UI components."""
        # Create main frame
        main_frame = ttk.Frame(self.frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create search frame
        search_frame = ttk.LabelFrame(main_frame, text="Search Reddit")
        search_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Create search options frame
        options_frame = ttk.Frame(search_frame)
        options_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Search type (subreddit or keyword)
        self.search_type_var = tk.StringVar(value="subreddit")
        search_type_frame = ttk.Frame(options_frame)
        search_type_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(search_type_frame, text="Search Type:").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(search_type_frame, text="Subreddit", variable=self.search_type_var, 
                         value="subreddit", command=self._toggle_search_type).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(search_type_frame, text="Keyword", variable=self.search_type_var, 
                         value="keyword", command=self._toggle_search_type).pack(side=tk.LEFT, padx=5)
        
        # Subreddit frame
        self.subreddit_frame = ttk.Frame(options_frame)
        self.subreddit_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(self.subreddit_frame, text="Subreddit:").pack(side=tk.LEFT, padx=5)
        self.subreddit_var = tk.StringVar()
        ttk.Entry(self.subreddit_frame, textvariable=self.subreddit_var, width=30).pack(side=tk.LEFT, padx=5)
        
        # Sort options
        sort_frame = ttk.Frame(self.subreddit_frame)
        sort_frame.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(sort_frame, text="Sort:").pack(side=tk.LEFT, padx=5)
        self.sort_var = tk.StringVar(value=RedditSearchOptions.SORT_OPTIONS[0]["value"])
        sort_dropdown = ttk.Combobox(sort_frame, textvariable=self.sort_var, state="readonly", width=10)
        sort_dropdown["values"] = [option["name"] for option in RedditSearchOptions.SORT_OPTIONS]
        sort_dropdown.current(0)
        sort_dropdown.pack(side=tk.LEFT, padx=5)
        
        # Time filter
        self.time_frame = ttk.Frame(self.subreddit_frame)
        self.time_frame.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(self.time_frame, text="Time:").pack(side=tk.LEFT, padx=5)
        self.time_var = tk.StringVar(value=RedditSearchOptions.TIME_FILTER_OPTIONS[1]["value"])
        time_dropdown = ttk.Combobox(self.time_frame, textvariable=self.time_var, state="readonly", width=10)
        time_dropdown["values"] = [option["name"] for option in RedditSearchOptions.TIME_FILTER_OPTIONS]
        time_dropdown.current(1)
        time_dropdown.pack(side=tk.LEFT, padx=5)
        
        # Keyword frame
        self.keyword_frame = ttk.Frame(options_frame)
        
        ttk.Label(self.keyword_frame, text="Keyword:").pack(side=tk.LEFT, padx=5)
        self.keyword_var = tk.StringVar()
        ttk.Entry(self.keyword_frame, textvariable=self.keyword_var, width=40).pack(side=tk.LEFT, padx=5)
        
        # Maximum results
        results_frame = ttk.Frame(options_frame)
        results_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(results_frame, text="Maximum Results:").pack(side=tk.LEFT, padx=5)
        self.max_results_var = tk.IntVar(value=10)
        max_results_dropdown = ttk.Combobox(results_frame, textvariable=self.max_results_var, state="readonly", width=5)
        max_results_dropdown["values"] = RedditSearchOptions.RESULT_OPTIONS
        max_results_dropdown.current(1)
        max_results_dropdown.pack(side=tk.LEFT, padx=5)
        
        # Search button
        ttk.Button(results_frame, text="Search", command=self._search_reddit).pack(side=tk.RIGHT, padx=5)
        
        # Results frame
        results_frame = ttk.LabelFrame(main_frame, text="Results")
        results_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create treeview for results
        columns = [
            ("title", "Title", 300),
            ("subreddit", "Subreddit", 100),
            ("author", "Author", 100),
            ("upvotes", "Upvotes", 80),
            ("comments", "Comments", 80),
            ("type", "Type", 80)
        ]
        
        self.results_tree, _ = self.create_treeview(results_frame, columns)
        self.results_tree.bind("<Double-1>", self._on_result_double_click)
        self.results_tree.bind("<Button-3>", self._on_result_right_click)
        
        # Initial UI state setup
        self._toggle_search_type()
    
    def _toggle_search_type(self):
        """Toggle between subreddit and keyword search."""
        search_type = self.search_type_var.get()
        
        if search_type == "subreddit":
            self.keyword_frame.pack_forget()
            self.subreddit_frame.pack(fill=tk.X, pady=5)
        else:
            self.subreddit_frame.pack_forget()
            self.keyword_frame.pack(fill=tk.X, pady=5)
    
    def _search_reddit(self):
        """Search Reddit based on selected options."""
        search_type = self.search_type_var.get()
        
        # Clear existing results
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        
        # Setup search params
        params = {
            "limit": self.max_results_var.get()
        }
        
        if search_type == "subreddit":
            subreddit = self.subreddit_var.get().strip()
            if not subreddit:
                messagebox.showerror("Error", "Please enter a subreddit name")
                return
            
            params["subreddit"] = subreddit
            params["sort"] = self.sort_var.get()
            
            if self.sort_var.get() == "top":
                params["time_filter"] = self.time_var.get()
            
            # Enable/disable time filter based on sort
            if self.sort_var.get() == "top":
                for child in self.time_frame.winfo_children():
                    child.configure(state="normal")
            else:
                for child in self.time_frame.winfo_children():
                    child.configure(state="disabled")
        else:
            query = self.keyword_var.get().strip()
            if not query:
                messagebox.showerror("Error", "Please enter a search query")
                return
            
            params["query"] = query
        
        # Start search in background
        threading.Thread(target=self._do_search, args=(params,), daemon=True).start()
    
    def _do_search(self, params):
        """
        Perform the search in a background thread.
        
        Args:
            params: Search parameters
        """
        try:
            # Get credentials
            credentials = self.config_manager.credentials.get("reddit", {})
            
            if not credentials.get("client_id") or not credentials.get("client_secret"):
                messagebox.showerror("Error", "Reddit API credentials not configured. Please go to the API Config tab.")
                return
            
            from src.api_connectors.factory import ConnectorFactory
            reddit = ConnectorFactory.create_connector("reddit", credentials)
            
            # Perform search
            results = reddit.fetch(**params)
            self.results = results
            
            # Update UI in main thread
            self.frame.after(0, self._update_results)
            
        except Exception as e:
            logger.error(f"Error searching Reddit: {e}")
            messagebox.showerror("Error", f"Error searching Reddit: {str(e)}")
    
    def _update_results(self):
        """Update the results treeview."""
        # Clear existing results
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        
        # Add results to treeview
        for result in self.results:
            values = (
                result["title"],
                result["subreddit"],
                result["author"],
                result["upvotes"],
                result["comments"],
                result["type"]
            )
            
            # Add display text and source ID for scheduling
            result["display_text"] = f"Reddit - {result['title']} (r/{result['subreddit']})"
            result["source_id"] = result["permalink"]
            
            self.results_tree.insert("", tk.END, values=values)
    
    def _on_result_double_click(self, event):
        """Handle double-click on a result."""
        # Get selected item
        selected = self.results_tree.selection()
        if not selected:
            return
        
        # Get index of selected item
        index = self.results_tree.index(selected[0])
        if index < len(self.results):
            # Open in browser
            webbrowser.open(self.results[index]["permalink"])
    
    def _on_result_right_click(self, event):
        """Show context menu on right-click."""
        # Get selection
        selected = self.results_tree.selection()
        if not selected:
            return
        
        # Create context menu
        context_menu = tk.Menu(self.frame, tearoff=0)
        context_menu.add_command(label="Open in Browser", command=self._open_in_browser)
        context_menu.add_command(label="Send to Discord", command=self._send_to_discord)
        context_menu.add_separator()
        context_menu.add_command(label="Copy URL", command=self._copy_url)
        
        # Show menu
        context_menu.post(event.x_root, event.y_root)
    
    def _open_in_browser(self):
        """Open selected result in browser."""
        selected = self.results_tree.selection()
        if not selected:
            return
        
        index = self.results_tree.index(selected[0])
        if index < len(self.results):
            webbrowser.open(self.results[index]["permalink"])
    
    def _send_to_discord(self):
        """Send selected result to Discord webhook."""
        selected = self.results_tree.selection()
        if not selected:
            return
        
        index = self.results_tree.index(selected[0])
        if index < len(self.results):
            result = self.results[index]
            
            # Get webhooks
            webhooks = self.config_manager.credentials.get("discord", {}).get("webhooks", [])
            if not webhooks:
                # For backward compatibility, check config.json
                webhooks = self.config_manager.config.get("webhooks", [])
                
            if not webhooks:
                messagebox.showerror("Error", "No webhooks configured. Please go to the Discord tab.")
                return
            
            # Create dialog to select webhook
            from .base_ui import DialogHelper
            dialog = tk.Toplevel(self.frame)
            dialog.title("Send to Discord")
            dialog.transient(self.frame)
            dialog.grab_set()
            
            # Webhook selection
            webhook_frame = ttk.Frame(dialog)
            webhook_frame.pack(fill=tk.X, padx=10, pady=10)
            
            ttk.Label(webhook_frame, text="Webhook:").pack(side=tk.LEFT, padx=5)
            webhook_var = tk.StringVar()
            webhook_dropdown = ttk.Combobox(webhook_frame, textvariable=webhook_var, state="readonly", width=30)
            webhook_dropdown["values"] = [w["name"] for w in webhooks]
            webhook_dropdown.current(0)
            webhook_dropdown.pack(side=tk.LEFT, padx=5)
            
            # Message customization
            message_frame = ttk.LabelFrame(dialog, text="Message")
            message_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            content_frame = ttk.Frame(message_frame)
            content_frame.pack(fill=tk.X, padx=5, pady=5)
            
            ttk.Label(content_frame, text="Content:").pack(anchor=tk.W)
            content_var = tk.StringVar(value=f"New post from r/{result['subreddit']}")
            ttk.Entry(content_frame, textvariable=content_var, width=50).pack(fill=tk.X, pady=5)
            
            include_var = tk.BooleanVar(value=True)
            ttk.Checkbutton(message_frame, text="Include post details", variable=include_var).pack(anchor=tk.W, padx=5)
            
            # Buttons
            button_frame = ttk.Frame(dialog)
            button_frame.pack(fill=tk.X, padx=10, pady=10)
            
            ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.RIGHT, padx=5)
            ttk.Button(button_frame, text="Send", command=lambda: self._do_send_to_discord(
                dialog, webhook_var.get(), content_var.get(), include_var.get(), result
            )).pack(side=tk.RIGHT, padx=5)
    
    def _do_send_to_discord(self, dialog, webhook_name, content, include_details, result):
        """
        Send result to Discord webhook.
        
        Args:
            dialog: Dialog to close
            webhook_name: Name of webhook
            content: Message content
            include_details: Whether to include post details
            result: Result to send
        """
        try:
            # Get webhook URL
            webhooks = self.config_manager.credentials.get("discord", {}).get("webhooks", [])
            if not webhooks:
                # For backward compatibility, check config.json
                webhooks = self.config_manager.config.get("webhooks", [])
            
            webhook = next((w for w in webhooks if w["name"] == webhook_name), None)
            
            if not webhook:
                messagebox.showerror("Error", "Selected webhook not found")
                return
            
            # Get Discord connector
            from src.api_connectors.factory import ConnectorFactory
            discord = ConnectorFactory.create_connector("discord", {})
            
            # Prepare message
            message = {
                "content": content,
                "embeds": []
            }
            
            if include_details:
                # Create embed for post
                color = 0xFF4500  # Reddit orange
                
                embed = {
                    "title": result["title"],
                    "url": result["permalink"],
                    "color": color,
                    "author": {
                        "name": f"u/{result['author']} in r/{result['subreddit']}",
                        "url": f"https://www.reddit.com/user/{result['author']}"
                    },
                    "footer": {
                        "text": f"👍 {result['upvotes']} | 💬 {result['comments']}"
                    }
                }
                
                # Add image if present
                if result.get("type") == "image" and result.get("image"):
                    embed["image"] = {"url": result["image"]}
                
                # Add description for text posts
                if result.get("type") == "text" and result.get("text"):
                    embed["description"] = result["text"][:2000]  # Discord max is 2048
                
                message["embeds"].append(embed)
            
            # Send message
            discord.send_webhook_message(webhook["url"], **message)
            
            # Close dialog
            dialog.destroy()
            
            # Show success message
            messagebox.showinfo("Success", "Message sent to Discord")
            
        except Exception as e:
            logger.error(f"Error sending to Discord: {e}")
            messagebox.showerror("Error", f"Error sending to Discord: {str(e)}")
    
    def _copy_url(self):
        """Copy selected result URL to clipboard."""
        selected = self.results_tree.selection()
        if not selected:
            return
        
        index = self.results_tree.index(selected[0])
        if index < len(self.results):
            # Copy to clipboard
            self.frame.clipboard_clear()
            self.frame.clipboard_append(self.results[index]["permalink"])
            
            # Show feedback
            messagebox.showinfo("Copied", "URL copied to clipboard")
