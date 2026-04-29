import json
import requests
import time
from datetime import datetime, timedelta, timezone
import sys
from pathlib import Path

# Modify Path for Local Imports to access utils.py
root_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(root_dir))

from utils import send_to_discord

# Configuration
TOKEN = "fm5s2FoN_YsNt-zvc3qtPRpfJ8w2JlSZPhBqFztw15s"
API_URL = "https://api.producthunt.com/v2/api/graphql"
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1496808041428025465/0stNNhf2EHyjNld8vhD0oHJ9CF7rzLGM6rRCNlIG32ILLuCLFmIN1QC3cId7ZZEizOzf"

def fetch_top_products(posted_after, posted_before, limit=10):
    """
    Fetches the top products from Product Hunt for a given timeframe,
    now including Topics and Thumbnails.
    """
    query = """
    query GetTopProducts($postedAfter: DateTime, $postedBefore: DateTime, $limit: Int) {
      posts(first: $limit, order: VOTES, postedAfter: $postedAfter, postedBefore: $postedBefore) {
        edges {
          node {
            name
            tagline
            description
            votesCount
            url
            thumbnail {
              url
            }
            topics(first: 3) {
              edges {
                node {
                  name
                }
              }
            }
          }
        }
      }
    }
    """
    
    variables = {
        "postedAfter": posted_after,
        "postedBefore": posted_before,
        "limit": limit
    }
    
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    try:
        response = requests.post(API_URL, json={"query": query, "variables": variables}, headers=headers)
        response.raise_for_status() 
        
        response_data = response.json()
        if "errors" in response_data:
            print("GraphQL Errors:", response_data["errors"])
            return []
        return response_data["data"]["posts"]["edges"]
            
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return []

def send_products_sequentially(title, edges, webhook_url):
    """
    Sends an intro title, then loops through each product and sends it individually,
    including its topics and an embedded image.
    """
    print(f"Sending {title}...")
    
    if not edges:
        send_to_discord(webhook_url, f"## 🚀 {title.upper()}\nNo products found for this timeframe.", username="Product Hunt Bot")
        return

    # 1. Send the title header
    send_to_discord(webhook_url, f"## 🚀 {title.upper()}", username="Product Hunt Bot")
    time.sleep(1)

    # 2. Send each product as a separate message
    for i, edge in enumerate(edges, 1):
        node = edge["node"]
        name = node.get("name", "Unknown")
        votes = node.get("votesCount", 0)
        tagline = node.get("tagline", "")
        url = node.get("url", "")
        
        # Extract Topics
        topics_edges = node.get("topics", {}).get("edges", [])
        topics_list = [t["node"]["name"] for t in topics_edges if "node" in t and "name" in t["node"]]
        topics_str = ", ".join(topics_list) if topics_list else "Uncategorized"
        
        # Extract Thumbnail URL
        thumbnail_url = node.get("thumbnail", {}).get("url", "") if node.get("thumbnail") else ""
        
        # Build the message format
        content = f"**{i}. [{name}]({url})** | ⬆ {votes} Upvotes\n"
        content += f"> *{tagline}*\n"
        content += f"🏷️ **Topics:** {topics_str}\n"
        
        send_to_discord(webhook_url, content, username="Product Hunt Bot")
        
        # Wait 1 second before sending the next one to respect Discord's rate limits
        time.sleep(1)

# --- Execution Logic ---

if __name__ == "__main__":
    now = datetime.now(timezone.utc)
    day_ago = now - timedelta(days=1)
    week_ago = now - timedelta(days=7)

    now_str = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    day_ago_str = day_ago.strftime("%Y-%m-%dT%H:%M:%SZ")
    week_ago_str = week_ago.strftime("%Y-%m-%dT%H:%M:%SZ")

    print("Fetching top products of the day...")
    daily_posts = fetch_top_products(posted_after=day_ago_str, posted_before=now_str)
    send_products_sequentially("Top Products of the Day", daily_posts, DISCORD_WEBHOOK_URL)

    print("Fetching top products of the week...")
    time.sleep(2)

    weekly_posts = fetch_top_products(posted_after=week_ago_str, posted_before=now_str)
    send_products_sequentially("Top Products of the Week", weekly_posts, DISCORD_WEBHOOK_URL)