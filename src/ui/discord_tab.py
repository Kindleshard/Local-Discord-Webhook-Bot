"""
Discord Tab UI Component.

Manages the Discord webhook configuration and management UI.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import logging
import re
from .base_ui import BaseUI, DialogHelper

logger = logging.getLogger(__name__)


class WebhookValidator:
    """Validates Discord webhook data."""
    
    @staticmethod
    def validate_webhook(webhook):
        """
        Validate webhook data.
        
        Args:
            webhook: Dictionary with webhook data
            
        Returns:
            bool: True if valid, False otherwise
        """
        if not webhook.get('name'):
            messagebox.showerror("Validation Error", "Webhook name is required")
            return False
        
        if not webhook.get('url'):
            messagebox.showerror("Validation Error", "Webhook URL is required")
            return False
        
        # Check if URL matches Discord webhook pattern
        if not re.match(r'^https://discord\.com/api/webhooks/\d+/', webhook['url']):
            messagebox.showerror("Validation Error", 
                               "Invalid webhook URL. It should be in the format: https://discord.com/api/webhooks/...")
            return False
        
        return True


class DiscordTab(BaseUI):
    """Discord tab UI component."""
    
    def __init__(self, parent, config_manager):
        """
        Initialize Discord tab.
        
        Args:
            parent: Parent notebook
            config_manager: Configuration manager instance
        """
        super().__init__(parent, config_manager, "Discord")
    
    def _init_ui(self):
        """Initialize the UI components."""
        # Main frame
        main_frame = ttk.Frame(self.frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Webhook management frame
        webhook_frame = ttk.LabelFrame(main_frame, text="Webhook Management")
        webhook_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Webhook button frame
        button_frame = ttk.Frame(webhook_frame)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(button_frame, text="Add Webhook", command=self.add_webhook).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="Edit Webhook", command=self.edit_webhook).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="Remove Webhook", command=self.remove_webhook).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="Test Webhook", command=self.test_webhook).pack(side=tk.LEFT, padx=2)
        
        # Webhook treeview
        columns = [
            ("name", "Name", 150),
            ("url", "URL", 300)
        ]
        self.webhook_tree_frame, self.webhook_tree = self.create_treeview(webhook_frame, columns)
        self.webhook_tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Status bar
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(status_frame, text="Status:").pack(side=tk.LEFT, padx=5)
        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(status_frame, textvariable=self.status_var).pack(side=tk.LEFT, padx=5)
        
        # Load webhooks
        self.load_webhooks()
    
    def load_webhooks(self):
        """Load webhooks from config."""
        # Clear existing items
        for item in self.webhook_tree.get_children():
            self.webhook_tree.delete(item)
        
        # Get webhooks from config
        webhooks = self.config_manager.config.get("webhooks", [])
        
        # If no webhooks found, show a message
        if not webhooks:
            self.webhook_tree.insert("", "end", values=("No webhooks configured", "", ""))
            return
        
        # Add webhooks to tree
        for webhook in webhooks:
            name = webhook.get("name", "Unnamed Webhook")
            url = webhook.get("url", "")
            channel = webhook.get("channel", "")
            self.webhook_tree.insert("", "end", values=(name, channel, url))
    
    def add_webhook(self):
        """Add a new webhook."""
        dialog, form_data = DialogHelper.create_webhook_dialog(self.parent, "Add Webhook")
        
        def save():
            name = form_data["name_var"].get().strip()
            url = form_data["url_var"].get().strip()
            
            webhook = {"name": name, "url": url}
            if WebhookValidator.validate_webhook(webhook):
                # Get current webhooks from config
                webhooks = self.config_manager.config.get("webhooks", [])
                
                # Add new webhook
                webhooks.append(webhook)
                
                # Update config
                self.config_manager.update_config("webhooks", webhooks)
                
                # Reload webhooks
                self.load_webhooks()
                dialog.destroy()
        
        DialogHelper.add_button_frame(dialog, save, dialog.destroy)
    
    def edit_webhook(self):
        """Edit selected webhook."""
        selection = self.webhook_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a webhook to edit")
            return
        
        # Get selected webhook
        item = selection[0]
        values = self.webhook_tree.item(item, "values")
        
        # Get webhook data from config
        webhooks = self.config_manager.config.get("webhooks", [])
        webhook_index = next((i for i, w in enumerate(webhooks) if w["name"] == values[0]), None)
        
        if webhook_index is None:
            messagebox.showerror("Error", "Webhook not found in configuration")
            return
        
        webhook = webhooks[webhook_index]
        
        # Create comprehensive dialog
        dialog, form_data = DialogHelper.create_webhook_dialog(
            self.parent,
            "Edit Webhook",
            webhook
        )
        
        def save():
            name = form_data["name_var"].get().strip()
            url = form_data["url_var"].get().strip()
            
            updated_webhook = {"name": name, "url": url}
            if WebhookValidator.validate_webhook(updated_webhook):
                webhooks[webhook_index] = updated_webhook
                self.config_manager.update_config("webhooks", webhooks)
                self.load_webhooks()
                dialog.destroy()
        
        DialogHelper.add_button_frame(dialog, save, dialog.destroy)
    
    def remove_webhook(self):
        """Remove selected webhook."""
        selection = self.webhook_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a webhook to remove")
            return
        
        # Confirm deletion
        if not messagebox.askyesno("Confirm Deletion", "Are you sure you want to remove this webhook?"):
            return
        
        # Get selected webhook
        item = selection[0]
        values = self.webhook_tree.item(item, "values")
        
        # Remove webhook from config
        webhooks = self.config_manager.config.get("webhooks", [])
        webhooks = [w for w in webhooks if w["name"] != values[0]]
        self.config_manager.update_config("webhooks", webhooks)
        
        # Reload webhooks
        self.load_webhooks()
    
    def test_webhook(self):
        """Test selected webhook."""
        selection = self.webhook_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a webhook to test")
            return
        
        # Get selected webhook
        item = selection[0]
        values = self.webhook_tree.item(item, "values")
        
        # Get webhook data from config
        webhooks = self.config_manager.config.get("webhooks", [])
        webhook = next((w for w in webhooks if w["name"] == values[0]), None)
        
        if webhook is None:
            messagebox.showerror("Error", "Webhook not found in configuration")
            return
        
        self._test_webhook(webhook["url"], webhook["name"])
    
    def _test_webhook(self, url, name):
        """
        Test a webhook.
        
        Args:
            url: Webhook URL
            name: Webhook name
        """
        # Create connector
        from src.api_connectors.factory import ConnectorFactory
        connector = ConnectorFactory.create_connector("discord", {})
        
        # Update status
        self.status_var.set(f"Testing webhook: {name}")
        
        # Define test task
        def test_task():
            try:
                result = connector.test_webhook(url)
                
                if result.get("success"):
                    return True, "Webhook test successful"
                else:
                    error = result.get("error", "Unknown error")
                    return False, f"Webhook test failed: {error}"
            except Exception as e:
                logger.error(f"Webhook test failed: {e}")
                return False, f"Webhook test failed: {str(e)}"
        
        # Define result handler
        def handle_result(result):
            success, message = result
            self.status_var.set(message)
            if success:
                messagebox.showinfo("Success", message)
            else:
                messagebox.showerror("Error", message)
        
        # Run test task
        self.run_async(test_task, handle_result)
    
    def on_config_changed(self):
        """Called when configuration changes."""
        self.load_webhooks()
