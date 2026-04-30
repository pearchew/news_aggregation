import os
import sys
import time
from pathlib import Path
import requests
import re
import html
from dateutil import parser
from datetime import datetime, timedelta, timezone
from bs4 import BeautifulSoup
from markdownify import markdownify

# Setup paths based on your structure
root_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(root_dir))
from utils import OUTPUT_DIR

def sanitize_filename(filename):
    clean_name = html.unescape(filename)
    clean_name = re.sub(r'[\\/*?:"<>|]', "", clean_name)
    clean_name = re.sub(r'\s+', '-', clean_name.strip())
    return clean_name

def scrape_sequoia_perspectives(cutoff_date):
    # Updated URL to target the specific category
    target_url = "https://sequoiacap.com/stories/?_story-category=perspective"
    
    # Create the structured download folder
    download_folder = OUTPUT_DIR / "website_scraping" / "sequoia_perspectives"
    download_folder.mkdir(parents=True, exist_ok=True)
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    new_downloads = []

    try:
        response = requests.get(target_url, headers=headers)
        response.raise_for_status() 
    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch main page {target_url}: {e}")
        return new_downloads

    soup = BeautifulSoup(response.text, 'html.parser')
    articles = soup.find_all("a", class_="ink")

    if not articles:
        print("No articles found on the main page.")
        return new_downloads

    total_articles = len(articles)
    print(f"Found {total_articles} articles on the Perspective page. Starting scan...\n")

    for index, article in enumerate(articles, 1):
        link = article.get("href")
        if not link: continue
        
        # Ensure absolute URL
        if link.startswith('/'):
            link = "https://sequoiacap.com" + link

        title_tag = article.find("h2", class_="ink__title")
        raw_title = title_tag.text.strip() if title_tag else "Untitled_Document"

        print(f"[{index}/{total_articles}] Checking: {raw_title}")

        # Fetch the inner article page to get the exact publication date and content
        try:
            article_resp = requests.get(link, headers=headers)
            article_resp.raise_for_status()
            article_soup = BeautifulSoup(article_resp.text, 'html.parser')
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Error fetching {link}: {e}")
            time.sleep(1)
            continue

        # Look for the specific <time> tag provided in your HTML snippet
        time_tag = article_soup.find("time", class_="wp-block-mg-post-date")
        
        # Fallback to meta tags if the specific time class isn't found
        if not time_tag:
            date_meta = article_soup.find("meta", property="article:published_time")
            pub_date_str = date_meta.get("content") if date_meta else ""
        else:
            pub_date_str = time_tag.get("datetime")

        if not pub_date_str:
            print(f"   ⏭️ Skipping (No precise date found)")
            time.sleep(1)
            continue

        try:
            pub_date = parser.parse(pub_date_str, fuzzy=True)
            # Strip timezone info if present so it can be compared cleanly against the cutoff_date
            if pub_date.tzinfo is not None:
                pub_date = pub_date.replace(tzinfo=None)
        except ValueError:
            print(f"   ⏭️ Skipping (Could not parse date {pub_date_str})")
            time.sleep(1)
            continue

        # HARD STOP: Break the loop entirely if the article is older than the cutoff date
        if pub_date < cutoff_date:
            print(f"\n🛑 Reached an article published on {pub_date.strftime('%Y-%m-%d')}, which is older than the cutoff date ({cutoff_date.strftime('%Y-%m-%d')}). Stopping scrape.")
            break

        # Process and download the article if it is within the timeframe
        safe_title = sanitize_filename(raw_title)
        date_prefix = pub_date.strftime("%Y-%m-%d")
        filename = f"{date_prefix}_{safe_title}.md"
        filepath = os.path.join(download_folder, filename)

        if os.path.exists(filepath):
            print(f"   ⏭️ Skipping (already exists): {filename}")
            time.sleep(1)
            continue

        print(f"   📥 Downloading: '{filename}'...")
        
        # Target the specific container for the text body to avoid hero banners and social sharing sections
        content_container = article_soup.find('section', class_="wp-block-mg-post-container")
        
        # Fallback to broader tags if the specific section class is missing
        if not content_container:
            content_container = article_soup.find('article') or article_soup.find('main') or article_soup.body
        
        if content_container:
            # Convert the clean HTML directly to markdown
            md_content = markdownify(str(content_container), heading_style="ATX")
            final_md = f"# {raw_title}\n\n**Published:** {pub_date.strftime('%B %d, %Y')}\n**Source:** {link}\n\n---\n\n{md_content}"
            
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(final_md)
                new_downloads.append(filepath)
                print(f"   ✅ Successfully saved!")
            except Exception as e:
                print(f"   ❌ Error saving {filename}: {e}")
        else:
            print(f"   ❌ Could not find article content container")
        
        # Polite delay to avoid rate limiting
        time.sleep(1)

    return new_downloads