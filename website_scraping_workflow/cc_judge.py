import os
import re
import time
import requests
from bs4 import BeautifulSoup
import markdownify
from playwright.sync_api import sync_playwright

# 1. Set up environment
output_dir = "cc_judge_insights"
os.makedirs(output_dir, exist_ok=True)

url = "https://www.jbs.cam.ac.uk/insight/"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def sanitize_filename(name):
    clean_name = re.sub(r'[<>:"/\\|?*]', '-', name)
    return clean_name.strip()

all_articles = []

# 2. Use Playwright to paginate
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    
    print(f"Opening {url}...")
    page.goto(url)

    # --- NEW: Cookie Banner Handler ---
    print("Checking for cookie banner...")
    try:
        # We wait for the Cookiebot 'Allow all' button and click it
        # Common Cookiebot ID is #CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll
        # We'll use a text-based selector to be safer
        cookie_button = page.get_by_role("button", name=re.compile("Allow all|Accept all", re.IGNORECASE))
        if cookie_button.is_visible(timeout=5000):
            cookie_button.click()
            print("✅ Cookie banner dismissed.")
            # Small wait to let the overlay disappear from the screen
            time.sleep(1)
    except Exception:
        print("No cookie banner found or already dismissed.")

    for current_page_num in range(1, 6):
        print(f"--- Scraping Page {current_page_num} ---")
        
        # Ensure articles are loaded
        page.wait_for_selector('.b08Box', timeout=10000)
        
        # Parse the current view
        soup = BeautifulSoup(page.content(), 'html.parser')
        boxes = soup.find_all('div', class_='b08Box')
        
        for box in boxes:
            title_tag = box.find('h3', class_='b08Title')
            if title_tag and title_tag.find('a'):
                link = title_tag.find('a')['href']
                title = title_tag.get_text(strip=True)
                
                year_match = re.search(r'/(\d{4})/', link)
                if year_match and int(year_match.group(1)) >= 2024:
                    all_articles.append({'title': title, 'url': link})

        # Pagination Logic
        if current_page_num < 5:
            # Re-locate the button on every loop to ensure it's "fresh"
            next_button = page.locator('#pagination-container a:has-text(">")')
            
            if next_button.is_visible():
                print(f"Clicking 'Next' button to go to Page {current_page_num + 1}...")
                # We use .force=True here if the banner is being particularly stubborn, 
                # but clicking it properly above is the better way.
                next_button.click()
                time.sleep(3) 
            else:
                print("Next button not found. Ending pagination early.")
                break

    browser.close()

# 3. Step Two: Process the collected articles (Remains the same)
print(f"\nTotal articles found (2024+): {len(all_articles)}")
# ... rest of the code as before ...
print("-" * 40)

for article in all_articles:
    title = article['title']
    article_url = article['url']
    
    try:
        # Check if we already have it
        # We need a temporary filename check here before downloading
        temp_name = sanitize_filename(title)
        # We don't have the date yet, so we just check if any file ends with this title
        existing_files = [f for f in os.listdir(output_dir) if temp_name in f]
        if existing_files:
            print(f"⏭️ Skipping (possible duplicate): {title}")
            continue

        print(f"Downloading content: {title}")
        res = requests.get(article_url, headers=headers)
        if res.status_code != 200: continue
        
        article_soup = BeautifulSoup(res.text, 'html.parser')
        
        # Extract Date
        date_tag = article_soup.find('div', class_='date')
        date_str = date_tag.get_text(strip=True).strip('.') if date_tag else "Unknown"
        
        # Extract Content
        content_body = article_soup.find('main', class_='container-main')
        if not content_body: continue
        
        # Convert to Markdown
        md_text = markdownify.markdownify(str(content_body), heading_style="ATX")
        
        # Final Save
        filename = sanitize_filename(f"{date_str}_{title}.md")
        filepath = os.path.join(output_dir, filename)
        
        final_content = f"# {title}\n**Date:** {date_str}\n**URL:** {article_url}\n\n---\n\n{md_text.strip()}"
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(final_content)
        
        print(f"✅ Saved: {filename}")
        time.sleep(1)

    except Exception as e:
        print(f"Error with {title}: {e}")

print("\nProcessing complete!")