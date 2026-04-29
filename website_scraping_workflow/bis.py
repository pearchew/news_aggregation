import os
import time
import requests
import re
import html
from dateutil import parser
from datetime import datetime, timedelta, timezone

def sanitize_filename(filename):
    clean_name = html.unescape(filename)
    clean_name = re.sub(r'[\\/*?:"<>|]', "", clean_name)
    clean_name = re.sub(r'\s+', '-', clean_name.strip())
    return clean_name

def scrape_bis(cutoff_date):
    target_apis = [
        "https://www.bis.org/api/document_lists/inflation_research.json",
        "https://www.bis.org/api/document_lists/green_finance_research.json",
        "https://www.bis.org/api/document_lists/fintech_research.json"
    ]
    download_folder = "outputs/bis_research_papers"
    os.makedirs(download_folder, exist_ok=True)
    
    base_domain = "https://www.bis.org"
    new_downloads = []

    for api_url in target_apis:
        topic_domain = api_url.split("/")[-1].replace(".json", "").replace("_research", "")
        try:
            response = requests.get(api_url)
            response.raise_for_status() 
            data = response.json()
        except requests.exceptions.RequestException as e:
            print(f"Failed to fetch API data for {api_url}: {e}")
            continue

        document_list = data.get("list", {})
        for path_key, doc_info in document_list.items():
            doc_path = doc_info.get("path")
            if not doc_path: continue
            
            pub_date_str = doc_info.get("publication_start_date", "")
            raw_title = doc_info.get("short_title", "Untitled_Document")
            
            try:
                pub_date = parser.parse(pub_date_str, fuzzy=True)
                # Strip timezone info if present so it can be compared cleanly
                if pub_date.tzinfo is not None:
                    pub_date = pub_date.replace(tzinfo=None)
            except ValueError:
                continue

            # Compare against our 7-day cutoff
            if pub_date >= cutoff_date:
                pdf_url = f"{base_domain}{doc_path}.pdf"
                safe_title = sanitize_filename(raw_title)
                filename = f"{pub_date_str}_{safe_title}_{topic_domain}.pdf"
                filepath = os.path.join(download_folder, filename)

                if os.path.exists(filepath):
                    print(f"⏭️ Skipping (already exists): {filename}")
                    continue

                print(f"Downloading: '{filename}'...")
                try:
                    pdf_response = requests.get(pdf_url, stream=True)
                    if pdf_response.status_code == 200 and 'application/pdf' in pdf_response.headers.get('Content-Type', ''):
                        with open(filepath, 'wb') as f:
                            for chunk in pdf_response.iter_content(chunk_size=8192):
                                f.write(chunk)
                        new_downloads.append(filepath)
                        print(f"   ✅ Successfully saved!")
                except requests.exceptions.RequestException as e:
                    print(f"   ❌ Error downloading {filename}: {e}")
                time.sleep(1)

    return new_downloads