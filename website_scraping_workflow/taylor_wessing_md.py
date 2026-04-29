import os
import re
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import markdownify
from dateutil import parser
from datetime import datetime, timedelta, timezone
import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(root_dir))
from utils import OUTPUT_DIR

def sanitize_filename(name):
    return re.sub(r'[<>:"/\\|?*]', '-', name).strip()

def scrape_taylor_wessing(cutoff_date):
    output_dir = OUTPUT_DIR / "website_scraping" / "taylorwessing_insights"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    base_domain = "https://www.taylorwessing.com"
    target_urls = [
        "https://www.taylorwessing.com/en/insights-and-events/insights?sectors=549d9e24-870c-4577-8e7e-6e6e17fd529a",
        "https://www.taylorwessing.com/en/insights-and-events/insights?sectors=151355ce-3029-4a90-84b3-1c4b8ee8a814"
    ]
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    
    new_downloads = []

    for main_url in target_urls:
        response = requests.get(main_url, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            articles = soup.find_all('div', class_='insights--item')
            
            for article in articles:
                title_tag = article.find('p', class_='insights--item__title')
                if not title_tag: continue
                title = title_tag.get_text(strip=True)
                
                date_tag = article.find('div', class_='insights--item__time')
                if not date_tag: continue
                date_str = date_tag.get_text(strip=True)
                
                link_tag = article.find('a', class_='insights--item__link')
                if not link_tag or 'href' not in link_tag.attrs: continue
                article_url = urljoin(base_domain, link_tag['href'])
                
                try:
                    article_date = parser.parse(date_str, fuzzy=True)
                    if article_date.tzinfo is not None:
                        article_date = article_date.replace(tzinfo=None)
                except ValueError:
                    continue
                    
                # Evaluate against cutoff date
                if article_date >= cutoff_date:
                    safe_title = sanitize_filename(title)[:150]
                    safe_date = sanitize_filename(date_str)
                    filename = f"{safe_date}_{safe_title}.md"
                    filepath = os.path.join(output_dir, filename)
                    
                    if os.path.exists(filepath): continue
                        
                    print(f"Processing: {title}")
                    article_response = requests.get(article_url, headers=headers)
                    if article_response.status_code != 200: continue
                        
                    article_soup = BeautifulSoup(article_response.text, 'html.parser')
                    content_body = article_soup.find('div', class_='content--body')
                    if not content_body: continue
                        
                    md_text = markdownify.markdownify(str(content_body), heading_style="ATX")
                    final_md_content = f"# {title}\n\n**Date:** {date_str}\n\n**Original URL:** {article_url}\n\n---\n\n{md_text.strip()}"
                    
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(final_md_content)
                    
                    new_downloads.append(filepath)
                    print(f"✅ Saved successfully: {filename}")
                    time.sleep(1)

    return new_downloads