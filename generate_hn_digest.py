import csv
import json
import requests
from datetime import datetime
from pathlib import Path
import ollama

# --- CONFIGURATION ---
MODEL_NAME = "gemma4:e4b"
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1496808041428025465/0stNNhf2EHyjNld8vhD0oHJ9CF7rzLGM6rRCNlIG32ILLuCLFmIN1QC3cId7ZZEizOzf" # Replace with your Discord Webhook
TODAY_STR = datetime.now().strftime("%Y-%m-%d")

# Paths setup using pathlib
BASE_DIR = Path("outputs")
DATA_FILE = BASE_DIR / f"hn_curated_stories_{TODAY_STR}.csv" # Assuming scraper saves with date
INSIGHTS_DIR = BASE_DIR / "hn_insights"
MD_DIR = INSIGHTS_DIR / "markdown"
JSONL_FILE = INSIGHTS_DIR / "trends_history.jsonl"

# Ensure directories exist
MD_DIR.mkdir(parents=True, exist_ok=True)

def load_hn_data(file_path: Path):
    """Reads the CSV and formats the data for the LLM."""
    if not file_path.exists():
        raise FileNotFoundError(f"Data file not found: {file_path}")
    stories = []
    with file_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # We only need the category, score, and title for trend analysis
            stories.append(f"[{row['category']}] (Score: {row['score']}) {row['title']}")
    # Join into a numbered list to save tokens
    return "\n".join(f"{i+1}. {story}" for i, story in enumerate(stories))

def analyze_trends(stories_text: str):
    """Calls Ollama to extract trends."""
    
    system_prompt = (
        "You are an expert tech analyst and Hacker News historian. "
        "Your job is to analyze a list of today's top Hacker News stories (Top, Ask HN, Show HN) "
        "and extract the overarching themes, tools, and developer sentiment. "
        "Output your response strictly in the following format:\n\n"
        "- [Trend 1]: [Brief description]\n"
        "- [Trend 2]: [Brief description]\n"
        "- [Trend 3]: [Brief description]\n"
        "- [Trend 4]: [Brief description]\n"
        "- [Trend 5]: [Brief description]\n\n"
        "**Rising Technologies/Keywords**:\n"
        "[Comma separated list of specific tech, e.g., Rust, TPUs, Local LLMs]\n\n"
    )

    user_prompt = f"Here are the top Hacker News stories for {TODAY_STR}:\n\n{stories_text}\n\nWhat are today's trends?"

    print(f"Sending data to Ollama model '{MODEL_NAME}'...")
    response = ollama.chat(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    )
    return response['message']['content']

def save_insights(analysis_text: str):
    """Saves the insight to a Markdown file and a JSON Lines file for long-term tracking."""
    
    # 1. Save to daily Markdown file
    md_file = MD_DIR / f"hn_trends_{TODAY_STR}.md"
    md_content = f"# Hacker News Trends: {TODAY_STR}\n\n{analysis_text}"
    md_file.write_text(md_content, encoding="utf-8")
    print(f"Saved markdown report to {md_file}")

    # 2. Extract Keywords (Quick and dirty parsing based on our prompt structure)
    keywords = []
    try:
        # Tries to find the line after "**Rising Technologies/Keywords**:"
        parts = analysis_text.split("**Rising Technologies/Keywords**:\n")
        if len(parts) > 1:
            keywords_line = parts[1].split("\n\n")[0]
            keywords = [k.strip() for k in keywords_line.split(",")]
    except Exception as e:
        print("Could not parse keywords for JSON.")

    # 3. Save to JSONL for long-term programmatic tracking
    json_record = {
        "date": TODAY_STR,
        "keywords": keywords,
        "raw_analysis": analysis_text
    }
    
    # Append to jsonl file
    with JSONL_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(json_record) + "\n")
    print(f"Appended structured data to {JSONL_FILE}")

def send_to_discord(analysis_text: str):
    """Sends the formatted analysis to a Discord channel via Webhook."""
    if DISCORD_WEBHOOK_URL == "YOUR_DISCORD_WEBHOOK_URL_HERE":
        print("Skipping Discord notification (no webhook URL provided).")
        return

    payload = {
        "username": "HN Trend Bot",
        "avatar_url": "https://news.ycombinator.com/y18.svg",
        "content": f"## 📈 Hacker News Daily Pulse: {TODAY_STR}\n\n{analysis_text}"
    }

    response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
    if response.status_code in [200, 204]:
        print("Successfully posted to Discord!")
    else:
        print(f"Failed to post to Discord. Status code: {response.status_code}")

def main():
    try:
        # Step 1: Load Data
        stories_text = load_hn_data(DATA_FILE)
        
        # Step 2: Analyze with Ollama
        analysis = analyze_trends(stories_text)
        
        # Step 3: Save insights locally
        save_insights(analysis)
        
        # Step 4: Broadcast to Discord
        send_to_discord(analysis)
        
    except Exception as e:
        print(f"Pipeline failed: {e}")

if __name__ == "__main__":
    # If testing with the uploaded file, uncomment the following line to override DATA_FILE:
    # DATA_FILE = Path("hn_curated_stories_2026-04-23.csv")
    main()