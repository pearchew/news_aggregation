from datetime import datetime, timedelta, timezone
import os
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from dateutil import parser
import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(root_dir))
from utils import OUTPUT_DIR

output_dir = OUTPUT_DIR / "website_scraping" / "sfc_papers"
output_dir.mkdir(parents=True, exist_ok=True)
    
# Helper function to remove characters that are invalid in file paths
def sanitize_filename(name):
    # Replaces < > : " / \ | ? * with a hyphen
    clean_name = re.sub(r'[<>:"/\\|?*]', '-', name)
    return clean_name.strip()

def scrape_sfc(cutoff_date):
    url = "https://www.sfc.hk/en/Published-resources/Research-papers"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    new_downloads = []
    # 2. Fetch the webpage
    print("Fetching the webpage...")
    response = requests.get(url, headers=headers)
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        
        for row in soup.find_all('tr'):
            cols = row.find_all('td')
            if len(cols) >= 2:
                link_tag = cols[0].find('a')
                if not link_tag: continue
                
                paper_name = link_tag.get_text(strip=True)
                pdf_url = urljoin(url, link_tag.get('href'))
                date_str = cols[1].get_text(strip=True)
                
                # <-- Change year filtering to exact datetime parsing
                try:
                    paper_date = parser.parse(date_str, fuzzy=True)
                except ValueError:
                    continue
                    
                # <-- Compare to the 7 day cutoff
                if paper_date >= cutoff_date:
                    safe_paper_name = sanitize_filename(paper_name)
                    safe_date = sanitize_filename(date_str)
                    filename = f"{safe_date}_{safe_paper_name}.pdf"
                    filepath = os.path.join(output_dir, filename)
                    
                    if os.path.exists(filepath):
                        print(f"⏭️ Skipping (already exists): {filename}")
                        continue
                    
                    print(f"Downloading: {filename}")
                    pdf_response = requests.get(pdf_url, headers=headers)
                    if pdf_response.status_code == 200:
                        with open(filepath, 'wb') as f:
                            f.write(pdf_response.content)
                        # <-- Add the file path to our list
                        new_downloads.append(filepath) 
                        print(f"✅ Saved successfully.\n")

    return new_downloads
