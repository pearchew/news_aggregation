import os
import re
import time
import requests
from bs4 import BeautifulSoup
import markdownify
from playwright.sync_api import sync_playwright
from dateutil import parser
from datetime import datetime, timedelta, timezone

import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(root_dir))
from utils import OUTPUT_DIR

def sanitize_filename(name):
    return re.sub(r'[<>:"/\\|?*]', '-', name).strip()

def scrape_cc_judge(cutoff_date):
    output_dir = OUTPUT_DIR / "website_scraping" / "cc_judge_insights"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    url = "https://www.jbs.cam.ac.uk/insight/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    all_articles = []
    new_downloads = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url)

        try:
            cookie_button = page.get_by_role("button", name=re.compile("Allow all|Accept all", re.IGNORECASE))
            if cookie_button.is_visible(timeout=5000):
                cookie_button.click()
                time.sleep(1)
        except Exception:
            pass

        # Only need 3 pages to cover a 7 day span
        for current_page_num in range(1, 4): 
            page.wait_for_selector('.b08Box', timeout=10000)
            soup = BeautifulSoup(page.content(), 'html.parser')
            boxes = soup.find_all('div', class_='b08Box')
            
            for box in boxes:
                title_tag = box.find('h3', class_='b08Title')
                if title_tag and title_tag.find('a'):
                    link = title_tag.find('a')['href']
                    title = title_tag.get_text(strip=True)
                    
                    year_match = re.search(r'/(\d{4})/', link)
                    # Broad filter on the initial pass
                    if year_match and int(year_match.group(1)) >= cutoff_date.year:
                        all_articles.append({'title': title, 'url': link})

            if current_page_num < 3:
                next_button = page.locator('#pagination-container a:has-text(">")')
                if next_button.is_visible():
                    next_button.click()
                    time.sleep(3) 
                else:
                    break
        browser.close()

    for article in all_articles:
        title = article['title']
        article_url = article['url']
        
        temp_name = sanitize_filename(title)
        existing_files = [f for f in os.listdir(output_dir) if temp_name in f]
        if existing_files:
            continue

        try:
            res = requests.get(article_url, headers=headers)
            if res.status_code != 200: continue
            
            article_soup = BeautifulSoup(res.text, 'html.parser')
            date_tag = article_soup.find('div', class_='date')
            date_str = date_tag.get_text(strip=True).strip('.') if date_tag else "Unknown"
            
            try:
                article_date = parser.parse(date_str, fuzzy=True)
                if article_date.tzinfo is not None:
                    article_date = article_date.replace(tzinfo=None)
            except ValueError:
                continue
            
            # Strict date comparison
            if article_date >= cutoff_date:
                content_body = article_soup.find('main', class_='container-main')
                if not content_body: continue
                
                md_text = markdownify.markdownify(str(content_body), heading_style="ATX")
                filename = sanitize_filename(f"{date_str}_{title}.md")
                filepath = os.path.join(output_dir, filename)
                
                final_content = f"# {title}\n**Date:** {date_str}\n**URL:** {article_url}\n\n---\n\n{md_text.strip()}"
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(final_content)
                
                new_downloads.append(filepath)
                print(f"✅ Saved: {filename}")
                time.sleep(1)
        except Exception as e:
            print(f"Error with {title}: {e}")

    return new_downloads
