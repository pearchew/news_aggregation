import os
import re
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright

# 1. Set up the environment
output_dir = "hkma_papers"
os.makedirs(output_dir, exist_ok=True)

url = "https://www.hkma.gov.hk/eng/data-publications-and-research/research/research-memorandums/"
base_domain = "https://www.hkma.gov.hk"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# Helper function to remove characters that are invalid in file paths
def sanitize_filename(name):
    clean_name = re.sub(r'[<>:"/\\|?*]', '-', name)
    return clean_name.strip()

# 2. Fetch the webpage using Playwright to handle the dropdown
print("Starting browser automation to load all papers...")
html_content = ""

with sync_playwright() as p:
    # Launch a headless browser (runs invisibly in the background)
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    
    print(f"Navigating to {url}...")
    page.goto(url)
    
    print("Clicking 'Load More' to load all older papers...")
    try:
        # Loop to continuously click the "Load More" button
        while True:
            # Locate the button using its ID
            load_more_btn = page.locator('#btn-research-memorandum-more')
            
            # Check if the button is still on the screen
            if load_more_btn.is_visible():
                print("Clicking 'Load More'...")
                load_more_btn.click()
                
                # Wait a few seconds for the new papers to load into the HTML
                time.sleep(3) 
            else:
                # If the button is no longer visible, we've loaded everything!
                print("All papers loaded!")
                break
                
    except Exception as e:
        print(f"Encountered an issue while clicking 'Load More': {e}")
    
    print("Extracting fully loaded HTML...")
    html_content = page.content()
    browser.close()

# 3. Parse the loaded HTML with BeautifulSoup
if html_content:
    soup = BeautifulSoup(html_content, 'html.parser')
    
    items = soup.find_all('li', class_='related-links-item')
    print(f"Found {len(items)} items to process.\n")
    print("-" * 40)
    
    for item in items:
        # Find the link tag
        link_tag = item.find('a')
        if not link_tag or 'href' not in link_tag.attrs:
            continue
            
        # Get the paper name from the 'title' attribute (fallback to text if missing)
        paper_name = link_tag.get('title', link_tag.get_text(strip=True))
        
        # Resolve the relative URL to an absolute URL
        pdf_url = urljoin(base_domain, link_tag['href'])
        
        # Find the div containing the date and file info
        remark_div = item.find('div', class_='remark')
        if not remark_div:
            continue
            
        # Extract the text, replacing <br> with a | so we can split it safely
        remark_text = remark_div.get_text(separator='|', strip=True)
        date_str = remark_text.split('|')[0].strip()
        
        # 4. Parse the year and filter
        try:
            # e.g., "22 April 2026" -> ["22", "April", "2026"] -> 2026
            year = int(date_str.split()[-1])
        except (ValueError, IndexError):
            continue
            
        # Filter for papers strictly after 2024
        if year > 2024:
            # 5. Format the filename and path
            safe_paper_name = sanitize_filename(paper_name)
            safe_date = sanitize_filename(date_str)
            
            # Prevent overly long filenames (Windows limits paths to 260 characters)
            if len(safe_paper_name) > 150:
                safe_paper_name = safe_paper_name[:150] + "..."
            
            filename = f"{safe_date}_{safe_paper_name}.pdf"
            filepath = os.path.join(output_dir, filename)
            
            # 6. Check for duplicates before downloading
            if os.path.exists(filepath):
                print(f"⏭️ Skipping (already exists): {filename}")
                continue
            
            print(f"Downloading: {filename}")
            
            # 7. Download and save the PDF using standard requests
            pdf_response = requests.get(pdf_url, headers=headers)
            
            if pdf_response.status_code == 200:
                with open(filepath, 'wb') as f:
                    f.write(pdf_response.content)
                print(f"✅ Saved successfully.\n")
            else:
                print(f"❌ Failed to download. Status code: {pdf_response.status_code}\n")
else:
    print("Failed to retrieve HTML content.")