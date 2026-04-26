import os
import re
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# 1. Set up the environment
output_dir = "hkma_annual_reports"
os.makedirs(output_dir, exist_ok=True)

base_domain = "https://www.hkma.gov.hk"
main_url = "https://www.hkma.gov.hk/eng/data-publications-and-research/publications/annual-report/"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def sanitize_filename(name):
    clean_name = re.sub(r'[<>:"/\\|?*]', '-', name)
    return clean_name.strip()

# 2. Fetch the main Annual Reports page
print("Fetching the main Annual Reports page...")
response = requests.get(main_url, headers=headers)

if response.status_code == 200:
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # 3. Find all report links on the main page
    # The links have titles like "Annual Report 2024", so we can search for those specifically
    report_links = soup.find_all('a', title=re.compile(r'^Annual Report'))
    print(f"Found {len(report_links)} report entries. Filtering...")
    print("-" * 40)
    
    for link_tag in report_links:
        title = link_tag.get('title', '').strip()
        sub_page_url = urljoin(base_domain, link_tag.get('href'))
        
        # 4. Extract the year and filter
        try:
            # "Annual Report 2024" -> 2024
            year = int(title.split()[-1])
        except (ValueError, IndexError):
            continue
            
        if year >= 2024:
            print(f"Processing: {title}")
            
            # 5. STEP TWO: Visit the sub-page to get the actual PDF link
            sub_page_response = requests.get(sub_page_url, headers=headers)
            
            if sub_page_response.status_code != 200:
                print(f"  ❌ Failed to load sub-page for {title}")
                continue
                
            sub_soup = BeautifulSoup(sub_page_response.text, 'html.parser')
            
            # Find the download link. Based on your HTML, it is an <a> tag 
            # with classes 'button highlight' inside a div with class 'panel'
            pdf_link_tag = sub_soup.select_one('.panel a.button.highlight')
            
            if not pdf_link_tag or 'href' not in pdf_link_tag.attrs:
                print(f"  ❌ Could not find PDF download link inside the sub-page for {title}")
                continue
                
            pdf_url = urljoin(base_domain, pdf_link_tag['href'])
            
            # 6. Format filename and check for duplicates
            filename = sanitize_filename(f"{year}_Annual_Report.pdf")
            filepath = os.path.join(output_dir, filename)
            
            if os.path.exists(filepath):
                print(f"  ⏭️ Skipping (already exists): {filename}\n")
                continue
                
            # 7. Download the PDF
            print(f"  Downloading: {filename}...")
            pdf_response = requests.get(pdf_url, headers=headers)
            
            if pdf_response.status_code == 200:
                with open(filepath, 'wb') as f:
                    f.write(pdf_response.content)
                print(f"  ✅ Saved successfully.\n")
            else:
                print(f"  ❌ Failed to download PDF. Status code: {pdf_response.status_code}\n")
            
            # Be polite to the server: pause for a second between downloads
            time.sleep(1)
else:
    print(f"Failed to fetch main page. Status code: {response.status_code}")