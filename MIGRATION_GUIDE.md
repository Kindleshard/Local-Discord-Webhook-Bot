# Discord Webhook Bot Migration Guide

This document provides instructions for migrating from the original version of the Discord Webhook Bot (main.py) to the refactored version (refactored_main.py).

## Overview of Changes

The refactored version introduces several improvements:

1. **Modular Architecture**: Code has been reorganized into a more maintainable structure with separate components for each functionality.
2. **Improved UI**: The interface now uses a tabbed layout for better organization.
3. **Enhanced Error Handling**: Better error handling and logging throughout the application.
4. **Background Scheduler**: Scheduled tasks now run in a background thread.
5. **Standardized API Connectors**: All platform integrations follow a consistent interface.

## Directory Structure

```
discord-webhook-bot/
├── config/
│   ├── config.json          # App configuration
│   └── credentials.json     # API keys (gitignored)
├── src/
│   ├── api_connectors/      # API integration modules
│   │   ├── discord.py       # Discord webhook connector
│   │   ├── factory.py       # Connector factory
│   │   ├── reddit.py        # Reddit API connector
│   │   ├── twitter.py       # Twitter API connector
│   │   └── youtube.py       # YouTube API connector
│   ├── ui/                  # UI components
│   │   ├── api_config_tab.py  # API configuration tab
│   │   ├── base_ui.py       # Base UI components and utilities
│   │   ├── discord_tab.py   # Discord webhook management
│   │   ├── schedule_tab.py  # Scheduled tasks management
│   │   └── youtube_tab.py   # YouTube content search
├── main.py                  # Original entry point
├── refactored_main.py       # New entry point
├── requirements.txt         # Dependencies
└── README.md                # Documentation
```

## Migration Steps

### For End Users

1. **Backup Your Configuration**:
   ```bash
   cp config/config.json config/config.json.backup
   cp config/credentials.json config/credentials.json.backup
   ```

2. **Update to the New Version**:
   - If you've made customizations to the original code, you'll need to adapt them to the new structure
   - Otherwise, you can simply start using the refactored version

3. **Run the New Application**:
   ```bash
   python refactored_main.py
   ```

### For Developers

1. **Understanding the Architecture**:
   - Review the `src/ui/base_ui.py` file to understand the base UI components
   - Review the `src/api_connectors/factory.py` to understand how connectors are created

2. **Adding New Platforms**:
   - Create a new connector in the `src/api_connectors/` directory
   - Register the connector in the `factory.py` file
   - Add a new tab in the `src/ui/` directory if needed

3. **Modifying Existing Functionality**:
   - Each feature is contained in its own tab and connector
   - Changes should respect the existing interfaces

## Migration Progress

- [x] Create base framework
- [x] Implement Discord tab
- [x] Implement YouTube tab
- [x] Implement Reddit tab
- [x] Add scheduler functionality
- [ ] Implement Twitter tab
- [ ] Port Instagram functionality
- [ ] Complete integration testing
- [ ] Switch default entry point from main.py to refactored_main.py

## Configuration Migration

The new version uses the same configuration format, with a few additions:

1. **Added `scheduled_tasks` Section**:
   This section stores information about scheduled tasks:
   ```json
   {
     "webhooks": [...],
     "scheduled_tasks": [
       {
         "platform": "youtube",
         "source": "Channel Name",
         "webhook": "Webhook Name",
         "interval": 3600,
         "next_run": "2023-01-01T12:00:00",
         "enabled": true
       }
     ]
   }
   ```

2. **API Credentials**: The format remains the same, but validation is now more consistent.

## Testing

Before fully migrating:

1. Ensure all your webhooks are properly configured
2. Test scheduled tasks functionality
3. Verify API connections work as expected

## Troubleshooting

Common issues during migration:

1. **Configuration Not Found**: Make sure your config files are in the correct location
2. **Missing Dependencies**: Run `pip install -r requirements.txt` to ensure all dependencies are installed
3. **API Connection Issues**: Verify your API credentials in the API Config tab

## Rollback Procedure

If you need to revert to the original version:

1. Copy your backup configuration files back
2. Run the original main.py script

## Support

For issues with the migration process, please open an issue on the project's repository.
