"""
Discord Webhook Bot UI Module.

This package contains the user interface components for the Discord Webhook Bot.
"""

from .base_ui import BaseUI
from .discord_tab import DiscordTab
from .youtube_tab import YouTubeTab
from .api_config_tab import ApiConfigTab
from .schedule_tab import TasksTab, ScheduleTab
from .fetching_tab import FetchingTab
from .discord_bot_ui import DiscordBotUI

__all__ = ['BaseUI', 'DiscordTab', 'YouTubeTab', 'ApiConfigTab', 'TasksTab', 'ScheduleTab', 'FetchingTab', 'DiscordBotUI']
