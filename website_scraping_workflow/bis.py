import requests
import os
import time
import re
import html

def sanitize_filename(filename):
    """
    Resolves HTML entities, removes invalid characters, and replaces spaces with hyphens.
    """
    clean_name = html.unescape(filename)
    # Remove characters that are illegal in file names
    clean_name = re.sub(r'[\\/*?:"<>|]', "", clean_name)
    # Replace any sequence of whitespace characters with a single hyphen
    clean_name = re.sub(r'\s+', '-', clean_name.strip())
    return clean_name

def download_bis_papers(api_url, download_folder):
    """
    Fetches the JSON from the given API URL, extracts the domain, downloads
    associated PDFs if published in 2024 or later, and tracks new downloads.
    """
    base_domain = "https://www.bis.org"
    topic_domain = api_url.split("/")[-1].replace(".json", "").replace("_research", "")
    new_downloads = 0  # Counter for new papers

    if not os.path.exists(download_folder):
        os.makedirs(download_folder)
        print(f"Created directory: {download_folder}")

    print(f"\n[{api_url}]")
    print("Fetching research list from API...")
    try:
        response = requests.get(api_url)
        response.raise_for_status() 
        data = response.json()
    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch API data: {e}")
        return 0

    document_list = data.get("list", {})
    total_docs = len(document_list)
    print(f"Found {total_docs} total documents. Filtering for 2024 and newer...\n")

    for index, (path_key, doc_info) in enumerate(document_list.items(), start=1):
        doc_path = doc_info.get("path")
        if not doc_path:
            continue
        
        pub_date = doc_info.get("publication_start_date", "Unknown_Date")
        raw_title = doc_info.get("short_title", "Untitled_Document")
        
        # Filter for 2024 and newer
        try:
            pub_year = int(pub_date.split("-")[0])
        except (ValueError, IndexError):
            pub_year = 0 

        if pub_year < 2024:
            continue

        pdf_url = f"{base_domain}{doc_path}.pdf"
        
        # Sanitize and format the title (spaces are now hyphens)
        safe_title = sanitize_filename(raw_title)
        
        filename = f"{pub_date}_{safe_title}_{topic_domain}.pdf"
        filepath = os.path.join(download_folder, filename)

        if os.path.exists(filepath):
            print(f"[{index}/{total_docs}] Already exists: '{filename}' - Skipping.")
            continue

        print(f"[{index}/{total_docs}] Downloading: '{filename}'...")
        try:
            pdf_response = requests.get(pdf_url, stream=True)
            
            if pdf_response.status_code == 200 and 'application/pdf' in pdf_response.headers.get('Content-Type', ''):
                with open(filepath, 'wb') as f:
                    for chunk in pdf_response.iter_content(chunk_size=8192):
                        f.write(chunk)
                print(f"   -> Successfully saved!")
                new_downloads += 1  # Increment the counter upon success
            else:
                print(f"   -> Failed: No PDF found at {pdf_url} (Status: {pdf_response.status_code})")
                
        except requests.exceptions.RequestException as e:
            print(f"   -> Error downloading {filename}: {e}")

        # Be polite to the server
        time.sleep(1)

    print(f"\nFinished processing '{topic_domain}'. Found {new_downloads} new paper(s).")
    return new_downloads

if __name__ == "__main__":
    target_apis = [
        "https://www.bis.org/api/document_lists/inflation_research.json",
        "https://www.bis.org/api/document_lists/green_finance_research.json",
        "https://www.bis.org/api/document_lists/fintech_research.json"
    ]
    
    shared_download_folder = "bis_research_papers"
    total_new_downloads = 0  # Grand total counter
    
    for api in target_apis:
        # Add the new downloads from each category to the grand total
        total_new_downloads += download_bis_papers(api, shared_download_folder)
        
    print(f"\nAll download loops are complete! Grand total of new papers downloaded: {total_new_downloads}")