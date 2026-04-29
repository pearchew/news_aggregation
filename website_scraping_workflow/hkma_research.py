import os
import re
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
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

def scrape_hkma_research(cutoff_date):
    output_dir = OUTPUT_DIR / "website_scraping" / "hkma_papers"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    url = "https://www.hkma.gov.hk/eng/data-publications-and-research/research/research-memorandums/"
    base_domain = "https://www.hkma.gov.hk"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    
    new_downloads = []
    html_content = ""
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url)
        
        try:
            # Click a few times to get recent papers, no need to load indefinitely
            for _ in range(3): 
                load_more_btn = page.locator('#btn-research-memorandum-more')
                if load_more_btn.is_visible():
                    load_more_btn.click()
                    time.sleep(2) 
                else:
                    break
        except Exception:
            pass
        
        html_content = page.content()
        browser.close()

    if html_content:
        soup = BeautifulSoup(html_content, 'html.parser')
        items = soup.find_all('li', class_='related-links-item')
        
        for item in items:
            link_tag = item.find('a')
            if not link_tag or 'href' not in link_tag.attrs: continue
                
            paper_name = link_tag.get('title', link_tag.get_text(strip=True))
            pdf_url = urljoin(base_domain, link_tag['href'])
            
            remark_div = item.find('div', class_='remark')
            if not remark_div: continue
                
            remark_text = remark_div.get_text(separator='|', strip=True)
            date_str = remark_text.split('|')[0].strip()
            
            try:
                paper_date = parser.parse(date_str, fuzzy=True)
                if paper_date.tzinfo is not None:
                    paper_date = paper_date.replace(tzinfo=None)
            except ValueError:
                continue
                
            # Filter strictly by 7 days
            if paper_date >= cutoff_date:
                safe_paper_name = sanitize_filename(paper_name)[:150]
                safe_date = sanitize_filename(date_str)
                filename = f"{safe_date}_{safe_paper_name}.pdf"
                filepath = os.path.join(output_dir, filename)
                
                if os.path.exists(filepath): continue
                
                print(f"Downloading: {filename}")
                pdf_response = requests.get(pdf_url, headers=headers)
                if pdf_response.status_code == 200:
                    with open(filepath, 'wb') as f:
                        f.write(pdf_response.content)
                    new_downloads.append(filepath)
                    print(f"✅ Saved successfully.")
                    
    return new_downloads