import requests
from pathlib import Path
import pandas as pd
from datetime import datetime
import logging
import sys

root_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(root_dir))
from utils import OUTPUT_DIR

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def save_github_readme(owner, repo, filename="README.md"):
    """
    Fetches the raw README.md from a GitHub repository and saves it locally.
    """
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{filename}"
    
    # 2. Set headers
    # 'application/vnd.github.v3.raw' ensures we get the plain text/markdown 
    # instead of a JSON object containing base64 encoded content.
    headers = {
        "Accept": "application/vnd.github.v3.raw",
        "User-Agent": "Python-Script" # GitHub API requires a User-Agent
    }

    try:
        logger.info(f"Fetching {filename} from {owner}/{repo}...")
        response = requests.get(url, headers=headers)
        
        # Check if the request was successful
        if response.status_code == 200:
            output_path = OUTPUT_DIR / "github" / "read_me_files"
            output_path.mkdir(parents=True, exist_ok=True)
            today = datetime.now().strftime("%Y-%m-%d")
            file_to_save = output_path / f"README_{repo}_{today}.md"
            
            # 4. Save the content
            file_to_save.write_text(response.text, encoding='utf-8')
            logger.info(f"Successfully saved to: {file_to_save}")
        else:
            logger.error(f"Error: Received status code {response.status_code}")
            logger.error(f"Message: {response.json().get('message')}")

    except Exception as e:
        logger.error(f"An error occurred: {e}")

def parse_github_url(url):
    """
    Parses a GitHub URL to extract owner and repo name.
    Example: https://github.com/deepinsight/insightface -> ('deepinsight', 'insightface')
    """
    parts = url.rstrip('/').split('/')
    if len(parts) >= 5:
        owner = parts[3]
        repo = parts[4]
        return owner, repo
    return None, None

def main():
    today = datetime.now().strftime("%Y-%m-%d")
    file_path_repo = OUTPUT_DIR / 'github' / 'daily_scrapes' / f'gh_repos_daily_{today}.csv'
    file_path_dev = OUTPUT_DIR / 'github' / 'daily_scrapes' / f'gh_devs_daily_{today}.csv'
    df_repo = pd.read_csv(file_path_repo)
    df_dev = pd.read_csv(file_path_dev)[['username', 'repo_name', 'repo_url']]
    df_repo[['owner', 'repo_name']] = df_repo['url'].apply(lambda x: pd.Series(parse_github_url(x)))

    for owner, repo_name in zip(df_repo['owner'], df_repo['repo_name']):
        logger.info(f"Processing repository: {owner}/{repo_name}")
        save_github_readme(owner, repo_name)
        
    for owner, repo_name in zip(df_dev['username'], df_dev['repo_name']):
        logger.info(f"Processing developer's repository: {owner}/{repo_name}")
        save_github_readme(owner, repo_name)
    
if __name__ == "__main__":
    main()