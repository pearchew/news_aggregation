import requests
from bs4 import BeautifulSoup
import json
import os
import re
from markdownify import markdownify as md

# --- Configuration ---
STORIES_URL = "https://sequoiacap.com/stories/"
LOG_FILE = "scraped_articles_log.json"
OUTPUT_DIR = "downloaded_articles"
TARGET_YEAR = "2026"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def load_seen_urls():
    """Loads the list of previously scraped URLs from the JSON log."""
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            return set(json.load(f))
    return set()

def save_seen_urls(seen_urls):
    """Saves the updated list of scraped URLs to the JSON log."""
    with open(LOG_FILE, 'w', encoding='utf-8') as f:
        json.dump(list(seen_urls), f, indent=4)

def sanitize_filename(title):
    """Removes illegal characters from the title to create a valid filename."""
    clean_name = re.sub(r'[\\/*?:"<>|]', "", title)
    return clean_name.strip()[:100] 

def get_article_links():
    """Scrapes the main stories page for article URLs."""
    print(f"Fetching story list from {STORIES_URL}...")
    response = requests.get(STORIES_URL, headers=HEADERS)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    links = []
    cards = soup.find_all('a', class_='ink')
    for card in cards:
        href = card.get('href')
        if href:
            links.append(href)
    return links

def process_article(url):
    """Fetches an article, checks its year, and saves it if it matches 2026.
       Returns True if the URL was successfully processed (saved OR skipped)."""
    print(f"  -> Checking article: {url}")
    
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"  -> [ERROR] Failed to fetch {url}: {e}")
        return False
        
    soup = BeautifulSoup(response.text, 'html.parser')

    # --- 1. Check Publication Date ---
    published_meta = soup.find('meta', property='article:published_time')
    if published_meta:
        published_date = published_meta.get('content', '') # Format: "2026-04-30T..."
        
        if not published_date.startswith(TARGET_YEAR):
            print(f"  -> [SKIPPED] Article is from {published_date[:4]}, not {TARGET_YEAR}.")
            # Return True so it gets added to the log and we don't check it again next time
            return True 
    else:
        print(f"  -> [WARNING] No publication date found. Skipping to be safe.")
        return True

    # --- 2. Extract Title ---
    title_element = soup.find('h1', class_=lambda c: c and 'hero-posts__title' in c)
    title = title_element.text.strip() if title_element else "Untitled_Article"

    # --- 3. Extract Content ---
    content_element = soup.find('section', class_=lambda c: c and 'wp-block-mg-post-container' in c)
    
    if not content_element:
        print(f"  -> [WARNING] Could not find content body for {url}. Skipping.")
        return True

    # --- 4. Convert HTML to Markdown ---
    markdown_content = md(str(content_element), heading_style="ATX")
    
    # --- 5. Save to File ---
    filename = f"{sanitize_filename(title)}.md"
    filepath = os.path.join(OUTPUT_DIR, filename)
    
    final_document = f"# {title}\n\n*Published: {published_date[:10]}*\n*Source: {url}*\n\n---\n\n{markdown_content}"
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(final_document)
        
    print(f"  -> [SAVED] Successfully downloaded to {filepath}")
    return True

def main():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    seen_urls = load_seen_urls()
    article_links = get_article_links()
    
    new_articles_processed = False

    for link in article_links:
        if link in seen_urls:
            continue
            
        new_articles_processed = True
        success = process_article(link)
        
        if success:
            seen_urls.add(link)
            save_seen_urls(seen_urls)

    if not new_articles_processed:
        print("\nNo new articles found. Everything is up to date!")
    else:
        print("\nFinished processing new articles.")

if __name__ == "__main__":
    main()