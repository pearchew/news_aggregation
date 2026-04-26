import os
import json
import csv
from pathlib import Path
from datetime import datetime
import ollama
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def extract_readme_insights(readme_content, model_name="gemma4:e4b"):
    """
    Sends the README content to Ollama and asks for structured JSON output.
    """
    prompt = f"""
    You are a technical analyst. Analyze the following GitHub repository README content.
    Extract the following information:
    1. Key Topics: The main technologies, frameworks, or domain areas (e.g., "Machine Learning", "React", "DevOps").
    2. Key Goals: A concise 1-2 sentence summary of what the project aims to solve or achieve.
    3. Key Use Cases: Specific scenarios where someone would use this project.

    Provide the output EXCLUSIVELY as a JSON object with the exact keys: "key_topics", "key_goals", and "key_use_cases".
    Ensure the values for "key_topics" and "key_use_cases" are arrays of strings.

    README CONTENT:
    ---
    {readme_content[:4000]} # Truncating to 6000 chars to comfortably fit context windows and speed up inference
    ---
    """

    try:
        # Using format='json' forces Ollama to output valid JSON
        response = ollama.chat(
            model=model_name,
            messages=[{'role': 'user', 'content': prompt}],
            format='json', 
            options={'temperature': 0.1} # Low temperature for more deterministic, factual extraction
        )
        
        # Parse the JSON string returned by the model
        return json.loads(response['message']['content'])
    except json.JSONDecodeError:
        logger.error("Failed to decode JSON from model response.")
        return None
    except Exception as e:
        logger.error(f"Ollama Error: {e}")
        return None

def main():
    today = datetime.now().strftime("%Y-%m-%d")
    output_folder = Path("outputs")/"read_me_insights"
    readme_folder = Path("outputs") / "read_me_files"
    output_csv = output_folder / f"repo_insights_daily_{today}.csv"
    output_folder.mkdir(parents=True, exist_ok=True)

    if not readme_folder.exists():
        logger.warning(f"Could not find the folder {readme_folder}. Have you run get_git_readme.py today?")
        return

    extracted_data = []
    logger.info(f"Found {len(list(readme_folder.glob(f'README_*_{today}.md')))} README files to analyze.")
    # Find all READMEs downloaded today
    for readme_path in readme_folder.glob(f"README_*_{today}.md"):
        # Extract the repo name from the filename
        # Format is typically README_reponame_YYYY-MM-DD.md
        repo_name = readme_path.name.replace("README_", "").replace(f"_{today}.md", "")
        logger.info(f"🤖 Analyzing {repo_name}...")
        
        content = readme_path.read_text(encoding='utf-8', errors='ignore')
        
        insights = extract_readme_insights(content)
        
        if insights:
            # Flatten lists into comma-separated strings for the CSV
            topics = ", ".join(insights.get("key_topics", []))
            use_cases = "; ".join(insights.get("key_use_cases", []))
            
            extracted_data.append({
                "repo_name": repo_name,
                "key_topics": topics,
                "key_goals": insights.get("key_goals", "N/A"),
                "key_use_cases": use_cases
            })

    # Save results to a CSV file
    if extracted_data:
        logger.info(f"\nWriting {len(extracted_data)} insights to {output_csv}...")
        fieldnames = ["repo_name", "key_topics", "key_goals", "key_use_cases"]
        
        with open(output_csv, mode='w', newline='', encoding='utf-8') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(extracted_data)
        
        logger.info("✅ Pipeline complete! Your daily digest data is ready.")
    else:
        logger.warning("No insights were extracted. Check your Ollama installation and logs.")

if __name__ == "__main__":
    main()