"""
Database Module
Handles storage and retrieval of content items
"""
import os
import json
import logging
import sqlite3
from datetime import datetime

logger = logging.getLogger('content_curator.database')

class Database:
    def __init__(self, db_path):
        """
        Initialize the database
        
        Args:
            db_path (str): Path to the SQLite database file
        """
        self.db_path = db_path
        self.conn = None
        self._initialize_db()
    
    def _initialize_db(self):
        """Initialize the database schema if it doesn't exist"""
        logger.info(f"Initializing database at {self.db_path}")
        
        # Create the database directory if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(self.db_path)), exist_ok=True)
        
        # Connect to the database
        self.conn = sqlite3.connect(self.db_path)
        cursor = self.conn.cursor()
        
        # Create the content table if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS content (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            platform TEXT NOT NULL,
            content_id TEXT NOT NULL,
            title TEXT,
            url TEXT NOT NULL,
            author TEXT,
            published_at TEXT,
            data TEXT,
            posted BOOLEAN DEFAULT 0,
            created_at TEXT NOT NULL,
            UNIQUE(platform, content_id)
        )
        ''')
        
        # Create the settings table if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
        ''')
        
        self.conn.commit()
        logger.info("Database initialization complete")
    
    def store_content(self, platform, items):
        """
        Store content items in the database
        
        Args:
            platform (str): The platform the content is from
            items (list): List of content items
            
        Returns:
            int: Number of items stored
        """
        if not items:
            return 0
            
        logger.info(f"Storing {len(items)} items from {platform}")
        
        cursor = self.conn.cursor()
        stored_count = 0
        
        for item in items:
            # Extract common fields
            content_id = str(item.get('id', ''))
            title = item.get('title', '')
            url = item.get('url', '')
            author = item.get('author', '')
            published_at = item.get('published_at', '')
            
            # Store the full item data as JSON
            data = json.dumps(item)
            
            try:
                cursor.execute('''
                INSERT OR IGNORE INTO content 
                (platform, content_id, title, url, author, published_at, data, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    platform, 
                    content_id, 
                    title, 
                    url, 
                    author, 
                    published_at, 
                    data, 
                    datetime.now().isoformat()
                ))
                
                if cursor.rowcount > 0:
                    stored_count += 1
            except sqlite3.Error as e:
                logger.error(f"Error storing content item: {e}")
        
        self.conn.commit()
        logger.info(f"Stored {stored_count} new items")
        return stored_count
    
    def get_content(self, platform=None, limit=10, posted=False):
        """
        Get content items from the database
        
        Args:
            platform (str, optional): Filter by platform
            limit (int, optional): Maximum number of items to return
            posted (bool, optional): Filter by posted status
            
        Returns:
            list: List of content items
        """
        cursor = self.conn.cursor()
        
        query = "SELECT * FROM content WHERE posted = ?"
        params = [1 if posted else 0]
        
        if platform:
            query += " AND platform = ?"
            params.append(platform)
        
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        
        items = []
        for row in cursor.fetchall():
            item = {
                'id': row[0],
                'platform': row[1],
                'content_id': row[2],
                'title': row[3],
                'url': row[4],
                'author': row[5],
                'published_at': row[6],
                'data': json.loads(row[7]),
                'posted': bool(row[8]),
                'created_at': row[9]
            }
            items.append(item)
        
        return items
    
    def mark_as_posted(self, item_id):
        """
        Mark a content item as posted
        
        Args:
            item_id (int): ID of the content item
            
        Returns:
            bool: True if successful
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("UPDATE content SET posted = 1 WHERE id = ?", (item_id,))
            self.conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            logger.error(f"Error marking content as posted: {e}")
            return False
    
    def save_setting(self, key, value):
        """
        Save a setting to the database
        
        Args:
            key (str): Setting key
            value (str): Setting value
            
        Returns:
            bool: True if successful
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                (key, str(value))
            )
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Error saving setting: {e}")
            return False
    
    def get_setting(self, key, default=None):
        """
        Get a setting from the database
        
        Args:
            key (str): Setting key
            default: Default value to return if the setting doesn't exist
            
        Returns:
            str: Setting value or default
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
            result = cursor.fetchone()
            return result[0] if result else default
        except sqlite3.Error as e:
            logger.error(f"Error getting setting: {e}")
            return default
    
    def close(self):
        """Close the database connection"""
        if self.conn:
            self.conn.close()
            self.conn = None
