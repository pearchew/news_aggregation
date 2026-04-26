# 1. Standard Library Imports
import csv
import logging
import re
import sys
from datetime import datetime
from pathlib import Path
import json
import os
import time

# 2. Third-Party Imports
import ollama
import feedparser

# 3. Modify Path for Local Imports
root_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(root_dir))

# 4. Local Imports
from utils import send_to_discord

# --- Script setup ---
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# --- CRITICAL FIX: Spoof User-Agent to bypass firewall blocks ---
feedparser.USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"

# Configuration
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1497846292414595084/guq5BTHbWCxHYq4c7F_Amn9WKtWpU-SkfhevBS9989S41aZq-vEyDgJy4Vfd1kQBXeMa"
SEEN_FILE = 'seen_articles.json'

FEEDS = {
    "BIS Innovation Hub": "https://www.bis.org/doclist/bisih_publications.rss"
}

def load_seen_articles():
    """Loads the list of previously seen article URLs from a JSON file."""
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE, 'r') as f:
            try:
                return set(json.load(f))
            except json.JSONDecodeError:
                print(f"Warning: '{SEEN_FILE}' is empty or corrupted. Starting fresh.")
                return set()
    return set()

def save_seen_articles(seen_articles):
    """Saves the updated list of seen article URLs back to the JSON file."""
    with open(SEEN_FILE, 'w') as f:
        json.dump(list(seen_articles), f)

def main():
    seen_articles = load_seen_articles()
    new_articles_count = 0

    print("Checking feeds for new updates...")

    for feed_name, url in FEEDS.items():
        print(f"Fetching {feed_name}...")
        feed = feedparser.parse(url)
        
        # Check if the feed actually returned entries (helpful for debugging future blocks)
        if not feed.entries:
            print(f"  -> Warning: No entries found for {feed_name}. It might still be blocking us.")
            continue

        for entry in feed.entries:
            article_url = entry.get('link', '')
            article_title = entry.get('title', 'No Title')
            article_desc = entry.get('description', 'No Description')
            print(article_desc)
            if not article_url:
                continue
            
            if article_url not in seen_articles:
                print(f"  -> New story found: {article_title}")
                
                # Optional: You had a print statement here for terminal debugging
                content = f"**{feed_name}**: [{article_title}]({article_url})\n{article_desc}\n"
                print(content)
                send_to_discord(DISCORD_WEBHOOK_URL, content, feed_name)
                time.sleep(3)  # Sleep to avoid hitting Discord rate limits
                
                seen_articles.add(article_url)
                new_articles_count += 1

    if new_articles_count > 0:
        save_seen_articles(seen_articles)
        print(f"Finished! Sent {new_articles_count} new updates to Discord.")
    else:
        print("Finished! No new stories found today.")

if __name__ == "__main__":
    main()