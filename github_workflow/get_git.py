import os
import csv
from datetime import datetime
import gtrending
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def fetch_and_save_repos():
    logger.info("--- FETCHING REPOSITORIES & SAVING TO CSV ---")
    filter_since = "daily"
    
    logger.info(f"Fetching {filter_since} trending repositories...")
    
    repos = gtrending.fetch_repos(
        since=filter_since
    )
    
    if not repos:
        logger.warning("No repositories found for these filters.")
        return

    # Create the outputs directory if it doesn't exist
    output_dir = "outputs/daily_scrapes"
    os.makedirs(output_dir, exist_ok=True)
    
    # Format the filename: gh_{applied filters}_{date_scraped}.csv
    date_scraped = datetime.now().strftime("%Y-%m-%d")
    applied_filters = f"{filter_since}"
    filename = f"gh_repos_{applied_filters}_{date_scraped}.csv"
    filepath = os.path.join(output_dir, filename)
    
    # Get the headers from the first repository dictionary keys
    # (Keys generally include: author, name, avatar, description, url, language, stars, forks, currentPeriodStars, fullname, etc.)
    headers = list(repos[0].keys())
    
    # Write to CSV
    with open(filepath, mode="w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=headers)
        writer.writeheader()
        
        for repo in repos:
            # The 'builtBy' field is a list of dictionaries. 
            # We convert it to a string so it fits safely into a single CSV cell.
            if 'builtBy' in repo and isinstance(repo['builtBy'], list):
                repo['builtBy'] = str(repo['builtBy'])
                
            writer.writerow(repo)
            
    logger.info(f"Successfully saved {len(repos)} repositories to '{filepath}'")

def fetch_and_save_developers():
    logger.info("--- FETCHING DEVELOPERS & SAVING TO CSV ---")
    
    # Set our filters
    # Note: Developer trending does not utilize spoken language filters
    filter_since = "daily"
    
    logger.info(f"Fetching {filter_since} trending developers...")
    
    devs = gtrending.fetch_developers(
        since=filter_since
    )
    
    if not devs:
        logger.warning("No developers found for these filters.")
        return

    # Create the outputs directory if it doesn't exist
    output_dir = "outputs/daily_scrapes"
    os.makedirs(output_dir, exist_ok=True)
    
    # Format the filename: gh_devs_{applied filters}_{date_scraped}.csv
    date_scraped = datetime.now().strftime("%Y-%m-%d")
    applied_filters = f"{filter_since}"
    filename = f"gh_devs_{applied_filters}_{date_scraped}.csv"
    filepath = os.path.join(output_dir, filename)
    
    flattened_devs = []
    for dev in devs:
        # Create a copy to avoid mutating the original data
        flat_dev = dev.copy()
        
        # Extract repo dictionary if it exists
        repo_data = flat_dev.pop('repo', {})
        
        if isinstance(repo_data, dict):
            flat_dev['repo_name'] = repo_data.get('name', '')
            flat_dev['repo_url'] = repo_data.get('url', '')
            flat_dev['repo_description'] = repo_data.get('description', '')
            flat_dev['repo_descriptionUrl'] = repo_data.get('descriptionUrl', '')
        else:
            # Fallback if repo is missing or empty
            flat_dev['repo_name'] = ''
            flat_dev['repo_url'] = ''
            flat_dev['repo_description'] = ''
            flat_dev['repo_descriptionUrl'] = ''
            
        flattened_devs.append(flat_dev)
    
    # Get the headers from the first flattened developer dictionary keys
    headers = list(flattened_devs[0].keys())
    
    # Write to CSV
    with open(filepath, mode="w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=headers)
        writer.writeheader()
        
        for dev in flattened_devs:
            writer.writerow(dev)
            
    logger.info(f"Successfully saved {len(flattened_devs)} developers to '{filepath}'")

if __name__ == "__main__":
    fetch_and_save_repos()
    fetch_and_save_developers()