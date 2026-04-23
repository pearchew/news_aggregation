import requests
import csv
import concurrent.futures
from pathlib import Path
import datetime

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
    print(f"Fetching IDs for {category_name}...")
    try:
        response = requests.get(f"{BASE_URL}/{endpoint}.json", timeout=10)
        response.raise_for_status()
        story_ids = response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {category_name} IDs: {e}")
        return []

    # If we need to sort by score, fetch up to the latest 200 items (the max for Ask/Show endpoints).
    # If not (like Top Stories which are pre-ranked), just fetch the first `limit` items to save time.
    ids_to_fetch = story_ids[:200] if sort_by_score else story_ids[:limit]
    
    print(f"Retrieving data for {len(ids_to_fetch)} items in {category_name}...")
    
    valid_stories = []
    # Use ThreadPoolExecutor to fetch items in parallel (much faster!)
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        results = executor.map(fetch_item_details, ids_to_fetch)
        
        for item in results:
            if item and item.get("type") == "story" and not item.get("dead") and not item.get("deleted"):
                # Clean up the data and add our category label
                valid_stories.append({
                    "category": category_name,
                    "id": item.get("id"),
                    "title": item.get("title"),
                    "by": item.get("by"),
                    "score": item.get("score", 0),
                    "time": item.get("time"),
                    "url": item.get("url", f"https://news.ycombinator.com/item?id={item.get('id')}")
                })

    # Sort descending by score if requested
    if sort_by_score:
        valid_stories.sort(key=lambda x: x["score"], reverse=True)

    return valid_stories[:limit]

def scrape_hn_to_csv():
    """
    Main function to scrape Ask HN, Show HN, and Top Stories and export to CSV.
    """
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    # 1. Setup outputs folder
    output_dir = Path("outputs")
    output_dir.mkdir(parents=True, exist_ok=True)
    file_path = output_dir / f"hn_curated_stories_{today}.csv"

    all_stories = []

    # 2. Fetch the top 50 Ask HN stories (sorted by highest score)
    ask_stories = get_top_items_for_category("askstories", "Ask HN", limit=50, sort_by_score=True)
    all_stories.extend(ask_stories)

    # 3. Fetch the top 50 Show HN stories (sorted by highest score)
    show_stories = get_top_items_for_category("showstories", "Show HN", limit=50, sort_by_score=True)
    all_stories.extend(show_stories)

    # 4. Fetch the 50 Top Stories of the day (already ranked by HN)
    top_stories = get_top_items_for_category("topstories", "Top Story", limit=50, sort_by_score=False)
    all_stories.extend(top_stories)

    if not all_stories:
        print("No stories were fetched. Exiting.")
        return

    # 5. Write everything to CSV
    fieldnames = ["category", "id", "title", "by", "score", "time", "url"]
    
    print(f"\nWriting {len(all_stories)} total stories to {file_path.absolute()}...")
    
    try:
        with open(file_path, mode='w', newline='', encoding='utf-8') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_stories)
            
        print("Successfully exported data!")
    except IOError as e:
        print(f"Error writing to CSV: {e}")

if __name__ == "__main__":
    scrape_hn_to_csv()