import os
import re
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import markdownify

# 1. Set up the environment
output_dir = "taylorwessing_insights"
os.makedirs(output_dir, exist_ok=True)

base_domain = "https://www.taylorwessing.com"

# Put all the target sector URLs into a list
target_urls = [
    "https://www.taylorwessing.com/en/insights-and-events/insights?sectors=549d9e24-870c-4577-8e7e-6e6e17fd529a",
    "https://www.taylorwessing.com/en/insights-and-events/insights?sectors=151355ce-3029-4a90-84b3-1c4b8ee8a814"
]

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def sanitize_filename(name):
    clean_name = re.sub(r'[<>:"/\\|?*]', '-', name)
    return clean_name.strip()

# 2. Loop through each main URL in our list
for main_url in target_urls:
    print(f"\n{'='*60}")
    print(f"Fetching insights from:\n{main_url}")
    print(f"{'='*60}")
    
    response = requests.get(main_url, headers=headers)
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 3. Find all article containers on this specific page
        articles = soup.find_all('div', class_='insights--item')
        print(f"Found {len(articles)} articles on this page. Filtering...")
        print("-" * 40)
        
        for article in articles:
            # Extract title
            title_tag = article.find('p', class_='insights--item__title')
            if not title_tag:
                continue
            title = title_tag.get_text(strip=True)
            
            # Extract date
            date_tag = article.find('div', class_='insights--item__time')
            if not date_tag:
                continue
            date_str = date_tag.get_text(strip=True)
            
            # Extract link
            link_tag = article.find('a', class_='insights--item__link')
            if not link_tag or 'href' not in link_tag.attrs:
                continue
            article_url = urljoin(base_domain, link_tag['href'])
            
            # 4. Parse the year and filter
            try:
                # "12 March 2026" -> 2026
                year = int(date_str.split()[-1])
            except (ValueError, IndexError):
                continue
                
            if year >= 2024:
                # 5. Format the filename
                safe_title = sanitize_filename(title)
                safe_date = sanitize_filename(date_str)
                
                if len(safe_title) > 150:
                    safe_title = safe_title[:150] + "..."
                    
                filename = f"{safe_date}_{safe_title}.md"
                filepath = os.path.join(output_dir, filename)
                
                # Check for duplicates (this also prevents downloading the same article if it appears in both sectors!)
                if os.path.exists(filepath):
                    print(f"⏭️ Skipping (already exists): {filename}")
                    continue
                    
                print(f"Processing: {title}")
                
                # 6. STEP TWO: Visit the article page
                article_response = requests.get(article_url, headers=headers)
                
                if article_response.status_code != 200:
                    print(f"  ❌ Failed to load article page. Status: {article_response.status_code}")
                    continue
                    
                article_soup = BeautifulSoup(article_response.text, 'html.parser')
                
                # Find the content body based on the snippet provided
                content_body = article_soup.find('div', class_='content--body')
                
                if not content_body:
                    print(f"  ❌ Could not find the content body on the page.")
                    continue
                    
                # 7. Convert HTML to Markdown
                md_text = markdownify.markdownify(str(content_body), heading_style="ATX")
                
                # Create a nice header block for the top of the Markdown file
                final_md_content = (
                    f"# {title}\n\n"
                    f"**Date:** {date_str}\n\n"
                    f"**Original URL:** {article_url}\n\n"
                    f"---\n\n"
                    f"{md_text.strip()}"
                )
                
                # 8. Save the Markdown file
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(final_md_content)
                    
                print(f"  ✅ Saved successfully: {filename}\n")
                
                # Pause to be polite to the server
                time.sleep(1)
                
    else:
        print(f"Failed to fetch main page. Status code: {response.status_code}")

print("\nAll done!")