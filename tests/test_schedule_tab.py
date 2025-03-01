"""
Tests for the ScheduleTab component.
"""

import unittest
import tkinter as tk
from tkinter import ttk
import os
import sys
import json
from datetime import datetime, timedelta

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.ui.schedule_tab import ScheduleTab
from src.ui.base_ui import ConfigManager


class MockConfigManager:
    """Mock ConfigManager for testing."""
    
    def __init__(self):
        self.config = {
            "webhooks": [
                {"name": "Test Webhook", "url": "https://discord.com/api/webhooks/test"},
            ],
            "scheduled_tasks": [
                {
                    "platform": "youtube",
                    "source": "Test Channel",
                    "webhook": "Test Webhook",
                    "interval": 3600,
                    "next_run": (datetime.now() + timedelta(hours=1)).isoformat(),
                    "enabled": True
                }
            ]
        }
        self.observers = []
    
    def add_observer(self, callback):
        """Add an observer."""
        self.observers.append(callback)
    
    def update_config(self, section, values):
        """Update config section."""
        self.config[section] = values
        for callback in self.observers:
            callback()
    
    def save_config(self, config):
        """Save the entire config."""
        self.config = config
        for callback in self.observers:
            callback()


class TestScheduleTab(unittest.TestCase):
    """Tests for the ScheduleTab class."""
    
    @classmethod
    def setUpClass(cls):
        """Set up the test class."""
        cls.root = tk.Tk()
        cls.notebook = ttk.Notebook(cls.root)
        cls.config_manager = MockConfigManager()
    
    @classmethod
    def tearDownClass(cls):
        """Clean up the test class."""
        cls.root.destroy()
    
    def setUp(self):
        """Set up each test."""
        self.schedule_tab = ScheduleTab(self.notebook, self.config_manager)
    
    def test_init(self):
        """Test initialization."""
        self.assertIsNotNone(self.schedule_tab)
        self.assertEqual(self.schedule_tab.tab_name, "Schedule")
    
    def test_load_tasks(self):
        """Test loading tasks."""
        # Clear the treeview first
        for item in self.schedule_tab.tasks_tree.get_children():
            self.schedule_tab.tasks_tree.delete(item)
        
        # Load tasks
        self.schedule_tab._load_tasks()
        
        # Check that task is in the treeview
        items = self.schedule_tab.tasks_tree.get_children()
        self.assertEqual(len(items), 1)
        
        # Check task values
        values = self.schedule_tab.tasks_tree.item(items[0], "values")
        self.assertEqual(values[0], "youtube")
        self.assertEqual(values[1], "Test Channel")
        self.assertEqual(values[2], "Test Webhook")
    
    def test_save_tasks(self):
        """Test saving tasks."""
        # Modify tasks
        tasks = [
            {
                "platform": "youtube",
                "source": "New Channel",
                "webhook": "Test Webhook",
                "interval": 7200,
                "next_run": (datetime.now() + timedelta(hours=2)).isoformat(),
                "enabled": True
            }
        ]
        
        # Save tasks
        self.schedule_tab.tasks = tasks
        self.schedule_tab.save_tasks()
        
        # Check that tasks were saved
        self.assertEqual(self.config_manager.config["scheduled_tasks"], tasks)


if __name__ == "__main__":
    unittest.main()
