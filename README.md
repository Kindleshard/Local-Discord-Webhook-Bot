# Discord Content Curator

A locally hosted Discord webhook bot that aggregates content from various social media platforms and posts it to Discord channels based on custom filters and preferences.

## Features

- Multi-platform integration (YouTube, WIP: Reddit, Twitter, Instagram/Facebook)
- Content filtering based on keywords, sources, and engagement metrics
- Manual content fetching with a button click
- Scheduled task automation for periodic content posting
- Local database for content storage and management
- Custom formatting for Discord messages
- Simple, tab-based user interface

## Setup

1. Install Python dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Configure API credentials:
   - Copy `config/credentials.example.json` to `config/credentials.json`
   - Add your API keys for each platform
   - Add your Discord webhook URL

3. Configure the application:
   - Edit `config/config.json` with your preferences

4. Run the application:
   ```
   python refactored_main.py
   ```

## Usage

### Discord Tab
- Manage webhooks for different Discord channels
- Test webhook connections
- Send manual messages

### YouTube Tab
- Search YouTube for content by keyword, topic, or channel
- Preview video details
- Send selected videos to Discord webhooks

### Reddit Tab
- Search Reddit by subreddit or keyword
- Browse hot, new, or top posts
- Send Reddit posts to Discord with custom formatting

### Schedule Tab
- Set up automated tasks to post content periodically
- Configure how often content is fetched and posted
- Enable/disable scheduled tasks as needed

### API Config Tab
- Manage API credentials for different platforms
- Test API connections
- View API usage statistics

## API Integrations

- YouTube
- Discord Webhooks
- Reddit (planned)
- Twitter (planned)
- Instagram/Facebook (planned)
- More to come...

## Architecture

The application follows a modular architecture:
- API Connectors: Standardized interfaces for different platforms
- UI Components: Tab-based interface for different features
- Configuration Management: Centralized configuration storage
- Scheduler: Background task execution

## License

MIT
