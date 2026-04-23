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


# # Example usage for save_github_readme
# if __name__ == "__main__":
#     # From URL: https://github.com/deepinsight/insightface
#     # owner = deepinsight, repo = insightface
#     save_github_readme("deepinsight", "insightface")

# Apply the parsing function to the 'url' column
# This creates two new columns in the dataframe
today = datetime.now().strftime("%Y-%m-%d")
file_path = Path('outputs')/f'gh_python_en_daily_{today}.csv'
df = pd.read_csv(file_path)
df[['owner', 'repo_name']] = df['url'].apply(lambda x: pd.Series(parse_github_url(x)))

# Display the first few rows to verify
print("Extracted Owner and Repo names:")
print(df[['url', 'owner', 'repo_name']].head())
df.to_csv(file_path, index=False)
print(f"\nUpdated CSV saved to {file_path}")

for owner, repo_name in zip(df['owner'], df['repo_name']):
    save_github_readme(owner, repo_name)