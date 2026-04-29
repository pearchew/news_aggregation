import os
import re
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime, timedelta, timezone
import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(root_dir))
from utils import OUTPUT_DIR

def sanitize_filename(name):
    return re.sub(r'[<>:"/\\|?*]', '-', name).strip()

def scrape_hkma_annual(cutoff_date):
    output_dir = OUTPUT_DIR / "website_scraping" / "hkma_annual_reports"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    base_domain = "https://www.hkma.gov.hk"
    main_url = "https://www.hkma.gov.hk/eng/data-publications-and-research/publications/annual-report/"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    
    new_downloads = []

    response = requests.get(main_url, headers=headers)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        report_links = soup.find_all('a', title=re.compile(r'^Annual Report'))
        
        for link_tag in report_links:
            title = link_tag.get('title', '').strip()
            sub_page_url = urljoin(base_domain, link_tag.get('href'))
            
            try:
                year = int(title.split()[-1])
            except (ValueError, IndexError):
                continue
                
            if year >= cutoff_date.year:
                sub_page_response = requests.get(sub_page_url, headers=headers)
                if sub_page_response.status_code != 200: continue
                    
                sub_soup = BeautifulSoup(sub_page_response.text, 'html.parser')
                pdf_link_tag = sub_soup.select_one('.panel a.button.highlight')
                
                if not pdf_link_tag or 'href' not in pdf_link_tag.attrs: continue
                    
                pdf_url = urljoin(base_domain, pdf_link_tag['href'])
                filename = sanitize_filename(f"{year}_Annual_Report.pdf")
                filepath = os.path.join(output_dir, filename)
                
                if os.path.exists(filepath): continue
                    
                print(f"Downloading: {filename}...")
                pdf_response = requests.get(pdf_url, headers=headers)
                if pdf_response.status_code == 200:
                    with open(filepath, 'wb') as f:
                        f.write(pdf_response.content)
                    new_downloads.append(filepath)
                    print(f"✅ Saved successfully.")
                    time.sleep(1)
    return new_downloads