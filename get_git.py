import os
import csv
from datetime import datetime
import gtrending

def demonstrate_utilities():
    print("--- 1. UTILITY AND CONVERSION FUNCTIONS ---")
    
    # List available programming languages
    print("Available programming languages (first 3):")
    langs = gtrending.languages_list()
    print([lang['name'] for lang in langs[:10]])

    # List available spoken languages
    print("\nAvailable spoken languages (first 3):")
    spoken_langs = gtrending.spoken_languages_list()
    print([lang['name'][0] for lang in spoken_langs[:3]])

    # Convert names to API parameter format
    print("\nConverting 'C++' to param:", gtrending.convert_language_name_to_param("c++"))
    print("Converting 'English' to code:", gtrending.convert_spoken_language_name_to_code("English"))

    # Validating inputs
    print("\nValidation Checks:")
    print("Is 'python' a valid language?", gtrending.check_language("python"))
    print("Is 'en' a valid spoken language code?", gtrending.check_spoken_language_code("en"))
    print("Is 'monthly' a valid time range?", gtrending.check_since("monthly"))
    print("Is 'yearly' a valid time range?", gtrending.check_since("yearly"))
    print("\n" + "="*50 + "\n")


def demonstrate_fetch_developers():
    print("--- 2. FETCHING TRENDING DEVELOPERS ---")
    
    # Fetch developers trending today in Python who have a sponsor URL
    devs = gtrending.fetch_developers(language="python", since="daily", sponsorable=True)
    
    if devs:
        print(f"Found {len(devs)} sponsorable Python developers trending today.")
        print(f"Top developer: {devs[0]['name']} ({devs[0]['username']})")
        print(f"Trending for repo: {devs[0]['repo']['name'] if devs[0]['repo'] else 'N/A'}")
    else:
        print("No sponsorable Python developers found trending today.")
    print("\n" + "="*50 + "\n")


def fetch_and_save_repos():
    print("--- 3. FETCHING REPOSITORIES & SAVING TO CSV ---")
    
    # Set our filters
    filter_lang = "python"
    filter_spoken = "en"  # English
    filter_since = "daily"
    
    print(f"Fetching {filter_since} trending {filter_lang} repositories (Spoken Language: {filter_spoken})...")
    
    repos = gtrending.fetch_repos(
        language=filter_lang,
        spoken_language_code=filter_spoken,
        since=filter_since
    )
    
    if not repos:
        print("No repositories found for these filters.")
        return

    # Create the outputs directory if it doesn't exist
    output_dir = "outputs"
    os.makedirs(output_dir, exist_ok=True)
    
    # Format the filename: gh_{applied filters}_{date_scraped}.csv
    date_scraped = datetime.now().strftime("%Y-%m-%d")
    applied_filters = f"{filter_lang}_{filter_spoken}_{filter_since}"
    filename = f"gh_{applied_filters}_{date_scraped}.csv"
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
            
    print(f"Successfully saved {len(repos)} repositories to '{filepath}'")


if __name__ == "__main__":
    demonstrate_utilities()
    demonstrate_fetch_developers()
    fetch_and_save_repos()