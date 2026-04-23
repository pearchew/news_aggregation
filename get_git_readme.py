import requests
from pathlib import Path
import pandas as pd
from datetime import datetime

def save_github_readme(owner, repo, filename="README.md", output_folder="outputs"):
    """
    Fetches the raw README.md from a GitHub repository and saves it locally.
    """
    # 1. Define the API endpoint
    # The format is: https://api.github.com/repos/{owner}/{repo}/contents/{path}
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{filename}"
    
    # 2. Set headers
    # 'application/vnd.github.v3.raw' ensures we get the plain text/markdown 
    # instead of a JSON object containing base64 encoded content.
    headers = {
        "Accept": "application/vnd.github.v3.raw",
        "User-Agent": "Python-Script" # GitHub API requires a User-Agent
    }

    try:
        print(f"Fetching {filename} from {owner}/{repo}...")
        response = requests.get(url, headers=headers)
        
        # Check if the request was successful
        if response.status_code == 200:
            # 3. Use pathlib to handle the output directory
            output_path = Path(output_folder)/"READMEs"
            output_path.mkdir(parents=True, exist_ok=True)
            today = datetime.now().strftime("%Y-%m-%d")
            file_to_save = output_path / f"README_{repo}_{today}.md"
            
            # 4. Save the content
            file_to_save.write_text(response.text, encoding='utf-8')
            print(f"Successfully saved to: {file_to_save}")
        else:
            print(f"Error: Received status code {response.status_code}")
            print(f"Message: {response.json().get('message')}")

    except Exception as e:
        print(f"An error occurred: {e}")

def parse_github_url(url):
    """
    Parses a GitHub URL to extract owner and repo name.
    Example: https://github.com/deepinsight/insightface -> ('deepinsight', 'insightface')
    """
    # Remove trailing slashes and split by '/'
    parts = url.rstrip('/').split('/')
    
    # In a standard GitHub URL (https://github.com/owner/repo), 
    # the owner is at index 3 and the repo is at index 4
    if len(parts) >= 5:
        owner = parts[3]
        repo = parts[4]
        return owner, repo
    return None, None

def main():
    today = datetime.now().strftime("%Y-%m-%d")
    file_path_repo = Path('outputs')/f'gh_repos_daily_{today}.csv'
    file_path_dev = Path('outputs')/f'gh_devs_daily_{today}.csv'
    df_repo = pd.read_csv(file_path_repo)
    df_dev = pd.read_csv(file_path_dev)[['username', 'repo_name', 'repo_url']]
    df_repo[['owner', 'repo_name']] = df_repo['url'].apply(lambda x: pd.Series(parse_github_url(x)))

    print("Extracted Owner and Repo names:")
    print(df_repo[['url', 'owner', 'repo_name']].head())
    print(df_dev[['repo_url', 'username', 'repo_name']].head())

    for owner, repo_name in zip(df_repo['owner'], df_repo['repo_name']):
        save_github_readme(owner, repo_name)
        
    for owner, repo_name in zip(df_dev['username'], df_dev['repo_name']):
        save_github_readme(owner, repo_name)
    
if __name__ == "__main__":
    main()