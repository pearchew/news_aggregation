import requests
from pathlib import Path
from datetime import date, datetime
import logging

# 1. Import your database connection and model
from database import SessionLocal
from models import repo_daily

logger = logging.getLogger(__name__)

def save_github_readme(owner, repo, filename="README.md", output_folder="outputs"):
    """
    Fetches the raw README.md from a GitHub repository and saves it locally.
    """
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{filename}"
    
    headers = {
        "Accept": "application/vnd.github.v3.raw",
        "User-Agent": "Trending-Repo-Aggregator" # Good practice to name your User-Agent
    }

    try:
        logger.info(f"Fetching {filename} from {owner}/{repo}...")
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            output_path = Path(output_folder) / "READMEs"
            output_path.mkdir(parents=True, exist_ok=True)
            today_str = datetime.now().strftime("%Y-%m-%d")
            file_to_save = output_path / f"README_{repo}_{today_str}.md"
            
            file_to_save.write_text(response.text, encoding='utf-8')
            logger.info(f"✅ Successfully saved to: {file_to_save}")
        else:
            # Replaced print with logger.warning so it doesn't crash the loop
            logger.warning(f"⚠️ Could not fetch README for {owner}/{repo} (Status: {response.status_code})")

    except Exception as e:
        logger.error(f"❌ An error occurred fetching {owner}/{repo}: {e}")

def main():
    logger.info("--- FETCHING READMES FROM DATABASE REPOS ---")
    
    db = SessionLocal()
    today = date.today()
    
    try:
        # 2. Query the database for all repos scraped TODAY
        todays_repos = db.query(repo_daily).filter(repo_daily.date_scraped == today).all()
        
        if not todays_repos:
            logger.warning("No repositories found in the database for today. Did you run get_git.py first?")
            return

        logger.info(f"Found {len(todays_repos)} repository entries for today. Processing...")

        # 3. Create a Set to prevent downloading the same README twice
        # (Sometimes a repo is trending in BOTH the 'repos' and 'developers' lists)
        processed_repos = set()

        for entry in todays_repos:
            owner = entry.user_name
            repo_name = entry.repo_name
            
            # Defensive check: Make sure the repo actually has a name before trying to fetch
            if not owner or not repo_name:
                continue
                
            # Create a unique identifier like 'huggingface/ml-intern'
            repo_identifier = f"{owner}/{repo_name}"
            
            # Only download if we haven't seen it yet today
            if repo_identifier not in processed_repos:
                save_github_readme(owner, repo_name)
                processed_repos.add(repo_identifier)
                
    except Exception as e:
        logger.error(f"❌ Database query failed: {e}")
    finally:
        # 4. Always close the database connection
        db.close()

if __name__ == "__main__":
    # If you run this script directly, this sets up the logger formatting
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s - %(message)s")
        
    main()