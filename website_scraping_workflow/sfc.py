import os
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# 1. Set up the environment
output_dir = "sfc_papers"
# This line creates the folder if it does not exist
os.makedirs(output_dir, exist_ok=True)

url = "https://www.sfc.hk/en/Published-resources/Research-papers"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# Helper function to remove characters that are invalid in file paths
def sanitize_filename(name):
    # Replaces < > : " / \ | ? * with a hyphen
    clean_name = re.sub(r'[<>:"/\\|?*]', '-', name)
    return clean_name.strip()

# 2. Fetch the webpage
print("Fetching the webpage...")
response = requests.get(url, headers=headers)

if response.status_code == 200:
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # 3. Find all rows in the table
    for row in soup.find_all('tr'):
        cols = row.find_all('td')
        
        # Ensure we have at least two columns (Title/Link and Date)
        if len(cols) >= 2:
            link_tag = cols[0].find('a')
            
            # Skip rows that don't have a link
            if not link_tag:
                continue
            
            # Extract the raw data using strip=True to clear out the &nbsp;
            paper_name = link_tag.get_text(strip=True)
            pdf_url = urljoin(url, link_tag.get('href'))
            date_str = cols[1].get_text(strip=True)
            
            # 4. Parse the year and filter
            try:
                # "Feb 2026" -> splits into ["Feb", "2026"] -> takes the last item
                year = int(date_str.split()[-1])
            except (ValueError, IndexError):
                # If the date column doesn't contain a readable year, skip it
                continue
                
            if year > 2024:
                # 5. Format the filename and path
                safe_paper_name = sanitize_filename(paper_name)
                safe_date = sanitize_filename(date_str)
                
                filename = f"{safe_date}_{safe_paper_name}.pdf"
                filepath = os.path.join(output_dir, filename)
                
                # 6. Check for duplicates before downloading
                if os.path.exists(filepath):
                    print(f"⏭️ Skipping (already exists): {filename}")
                    continue
                
                print(f"Downloading: {filename}")
                
                # 7. Download and save the PDF
                pdf_response = requests.get(pdf_url, headers=headers)
                
                if pdf_response.status_code == 200:
                    with open(filepath, 'wb') as f:
                        f.write(pdf_response.content)
                    print(f"✅ Saved successfully.\n")
                else:
                    print(f"❌ Failed to download. Status code: {pdf_response.status_code}\n")
else:
    print(f"Failed to fetch the main page. Status code: {response.status_code}")