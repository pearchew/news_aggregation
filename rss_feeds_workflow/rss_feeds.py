import sqlite3
import feedparser
import logging

logger = logging.getLogger(__name__)

# # 1. Connect to your EXISTING database
# conn = sqlite3.connect('insights.db')
# cursor = conn.cursor()

# # 2. Setup Tables (Prefixed with 'rss_' to avoid conflicting with your existing data)
# cursor.execute('''CREATE TABLE IF NOT EXISTS rss_feeds
#                   (id INTEGER PRIMARY KEY, name TEXT, url TEXT)''')

# cursor.execute('''CREATE TABLE IF NOT EXISTS rss_articles
#                   (id INTEGER PRIMARY KEY, feed_id INTEGER, title TEXT, 
#                    link TEXT, guid TEXT UNIQUE, is_read INTEGER DEFAULT 0)''')

# # Add a test feed just to have something to poll
# cursor.execute("INSERT OR IGNORE INTO rss_feeds (id, name, url) VALUES (1, ' Bank for International Settlements', 'https://www.bis.org/doclist/bisih_publications.rss')")
# conn.commit()

# # 3. The Polling Logic
# def poll_feeds():
#     cursor.execute("SELECT id, url FROM rss_feeds")
#     feeds = cursor.fetchall()
    
#     for feed_id, url in feeds:
#         print(f"Polling {url}...")
#         parsed_feed = feedparser.parse(url)
        
#         for entry in parsed_feed.entries:
#             # RSS feeds usually have an 'id' (guid), but fallback to the link if they don't
#             item_guid = getattr(entry, 'id', entry.link)
            
#             # INSERT OR IGNORE tells SQLite to silently skip this if the guid already exists
#             cursor.execute('''INSERT OR IGNORE INTO rss_articles 
#                               (feed_id, title, link, guid) 
#                               VALUES (?, ?, ?, ?)''', 
#                            (feed_id, entry.title, entry.link, item_guid))
            
#     conn.commit()
#     print("Polling complete. Database updated!")

# # 4. Reading your feed
# def get_unread_articles():
#     cursor.execute("SELECT id, title, link FROM rss_articles WHERE is_read = 0")
#     return cursor.fetchall()

# # --- Execution ---
# if __name__ == "__main__":
#     poll_feeds()
    
#     unread = get_unread_articles()
#     print(f"\nYou have {len(unread)} unread articles sitting in insights.db.")


bis_innovation_hub_feed = feedparser.parse('https://www.bis.org/doclist/bisih_publications.rss')
finextra_headline_feed = feedparser.parse('https://www.finextra.com/rss/headlines.aspx')
finextra_blog_feed = feedparser.parse('https://www.finextra.com/rss/blogs.aspx')
finextra_ai_feed = feedparser.parse('https://www.finextra.com/rss/channel.aspx?channel=ai')
finextra_payments_feed = feedparser.parse('https://www.finextra.com/rss/channel.aspx?channel=payments')
finextra_regulation_feed = feedparser.parse('https://www.finextra.com/rss/channel.aspx?channel=regulation')
finextra_crime_feed = feedparser.parse('https://www.finextra.com/rss/channel.aspx?channel=crime')