import requests
import concurrent.futures
from datetime import date
import logging

# 1. Import your database tools
from database import SessionLocal
from models import hacker_news_daily

logger = logging.getLogger(__name__)
BASE_URL = "https://hacker-news.firebaseio.com/v0"

def fetch_item_details(item_id):
    """Fetches the details for a single HN item."""
    try:
        response = requests.get(f"{BASE_URL}/item/{item_id}.json", timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException:
        return None

def get_top_items_for_category(endpoint, category_name, limit=20, sort_by_score=True):
    """
    Fetches IDs from an endpoint, retrieves their details, and returns the top items.
    """
    logger.info(f"Fetching IDs for {category_name}...")
    try:
        response = requests.get(f"{BASE_URL}/{endpoint}.json", timeout=10)
        response.raise_for_status()
        story_ids = response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching {category_name} IDs: {e}")
        return []

    ids_to_fetch = story_ids[:200] if sort_by_score else story_ids[:limit]
    logger.info(f"Retrieving data for {len(ids_to_fetch)} items in {category_name}...")
    
    valid_stories = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        results = executor.map(fetch_item_details, ids_to_fetch)
        
        for item in results:
            if item and item.get("type") == "story" and not item.get("dead") and not item.get("deleted"):
                valid_stories.append({
                    "category": category_name,
                    "id": item.get("id"),
                    "title": item.get("title"),
                    "by": item.get("by"),
                    "score": item.get("score", 0),
                    "time": item.get("time"),
                    "url": item.get("url", f"https://news.ycombinator.com/item?id={item.get('id')}")
                })

    if sort_by_score:
        valid_stories.sort(key=lambda x: x["score"], reverse=True)

    return valid_stories[:limit]

def scrape_hn_to_db():
    """
    Main function to scrape Ask HN, Show HN, and Top Stories and save to SQLite.
    """
    logger.info("--- STARTING HACKER NEWS SCRAPE ---")
    
    all_stories = []

    # 1. Fetch stories
    ask_stories = get_top_items_for_category("askstories", "Ask HN", limit=50, sort_by_score=True)
    all_stories.extend(ask_stories)

    show_stories = get_top_items_for_category("showstories", "Show HN", limit=50, sort_by_score=True)
    all_stories.extend(show_stories)

    top_stories = get_top_items_for_category("topstories", "Top Story", limit=50, sort_by_score=False)
    all_stories.extend(top_stories)

    if not all_stories:
        logger.warning("No stories were fetched. Exiting.")
        return

    logger.info(f"Preparing to save {len(all_stories)} total stories to the database...")

    # 2. Save to Database
    db = SessionLocal()
    today = date.today()
    added_count = 0
    skipped_count = 0

    try:
        # Get a list of all existing Hacker News IDs currently in the database
        # This prevents us from crashing on duplicate entries
        existing_ids_tuples = db.query(hacker_news_daily.hn_id).all()
        existing_ids = {row[0] for row in existing_ids_tuples}

        for story in all_stories:
            story_id = story.get("id")
            
            # Uniqueness Check: If we already have this post, skip it
            if story_id in existing_ids:
                skipped_count += 1
                continue

            new_story = hacker_news_daily(
                date_scraped=today,
                category=story.get("category"),
                hn_id=story_id,
                title=story.get("title"),
                author=story.get("by"),
                score=story.get("score"),
                time_posted=story.get("time"),
                url=story.get("url")
            )
            
            db.add(new_story)
            # Add to our local set so we don't accidentally add it twice in the same run!
            existing_ids.add(story_id) 
            added_count += 1

        db.commit()
        logger.info(f"✅ Successfully added {added_count} new stories to the database! (Skipped {skipped_count} duplicates)")
        
    except Exception as e:
        logger.error(f"❌ Error saving HN stories to DB: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    # Setup basic logging just in case this is run directly instead of through main.py
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s - %(message)s")
        
    scrape_hn_to_db()