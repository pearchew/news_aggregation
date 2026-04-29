# 1. Standard Library Imports
import csv
import os
import logging
import re
import sys
from datetime import datetime
from pathlib import Path
import json

# 2. Third-Party Imports
import ollama

# 3. Modify Path for Local Imports
root_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(root_dir))

# 4. Local Imports
from utils import send_to_discord, OUTPUT_DIR

# --- Script setup ---
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

MODEL_NAME = "qwen3:8b"
TODAY_STR = datetime.now().strftime("%Y-%m-%d")
BASE_DIR = OUTPUT_DIR / "hacker_news"
DATA_FILE = BASE_DIR / "raw_data" / f"hn_curated_stories_{TODAY_STR}.csv" 
INSIGHTS_DIR = BASE_DIR / "insights"
MD_DIR = INSIGHTS_DIR / "markdown"
JSONL_FILE = BASE_DIR / "tracking" / "trends_history.jsonl"

# Ensure tracking directory exists
JSONL_FILE.parent.mkdir(parents=True, exist_ok=True)
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
    
    # Updated prompt to enforce brevity and prevent hallucinated formatting
    system_prompt = (
        "You are an expert tech analyst and Hacker News historian. "
        "Your job is to analyze a list of today's top Hacker News stories (Top, Ask HN, Show HN) "
        "and extract the overarching themes, tools, and developer sentiment. "
        "Keep your descriptions concise to fit within strict character limits of 2000 characters. "
        "Output your response strictly in the following format:\n\n"
        "- **Trend 1 Name**: [2 short sentences describing the trend and its implications]\n"
        "- **Trend 2 Name**: [2 short sentences describing the trend and its implications]\n"
        "- **Trend 3 Name**: [2 short sentences describing the trend and its implications]\n"
        "- **Trend 4 Name**: [2 short sentences describing the trend and its implications]\n"
        "**Rising Technologies/Keywords**:\n"
        "[Comma separated list of specific tech, e.g., Rust, TPUs, Local LLMs]\n"
    )

    user_prompt = f"Here are the top Hacker News stories for {TODAY_STR}:\n\n{stories_text}\n\nWhat are today's trends?"

    logger.info(f"Sending data to Ollama model '{MODEL_NAME}'...")
    response = ollama.chat(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        options={'temperature': 0.0} # Lower temperature for strict formatting
    )
    
    raw_content = response['message']['content']
    
    # Strip out any <think> blocks the model might generate
    clean_content = re.sub(r'<think>.*?</think>', '', raw_content, flags=re.DOTALL).strip()
    
    return clean_content

def save_insights(analysis_text: str):
    """Saves the insight to a Markdown file and a JSON Lines file for long-term tracking."""
    
    # 1. Save to daily Markdown file
    md_file = MD_DIR / f"hn_trends_{TODAY_STR}.md"
    md_content = f"# Hacker News Trends: {TODAY_STR}\n\n{analysis_text}"
    md_file.write_text(md_content, encoding="utf-8")
    logger.info(f"Saved markdown report to {md_file}")

    # 2. Extract Keywords (Quick and dirty parsing based on our prompt structure)
    keywords = []
    try:
        # Tries to find the line after "**Rising Technologies/Keywords**:"
        parts = analysis_text.split("**Rising Technologies/Keywords**:\n")
        if len(parts) > 1:
            keywords_line = parts[1].split("\n\n")[0]
            keywords = [k.strip() for k in keywords_line.split(",")]
    except Exception as e:
        logger.error("Could not parse keywords for JSON.")

    # 3. Save to JSONL for long-term programmatic tracking
    json_record = {
        "date": TODAY_STR,
        "keywords": keywords,
        "raw_analysis": analysis_text
    }
    
    # Append to jsonl file
    with JSONL_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(json_record) + "\n")
    logger.info(f"Appended structured data to {JSONL_FILE}")

def main():
    try:
        stories_text = load_hn_data(DATA_FILE)
        analysis = analyze_trends(stories_text)
        save_insights(analysis)
        
        hn_avatar = "https://news.ycombinator.com/y18.svg"
        full_message = f"## 📈 Hacker News Daily Pulse: {TODAY_STR}\n\n{analysis}"
        DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
        send_to_discord(
            webhook_url=DISCORD_WEBHOOK_URL, 
            content=full_message, 
            username="HN Trend Bot", 
            avatar_url=hn_avatar
        )
        logger.info("Sent daily trends to Discord channel.")
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")

if __name__ == "__main__":
    main()