import csv
import json
import requests
import re
from datetime import date,datetime
from pathlib import Path
import ollama
from utils import send_to_discord
import logging
from database import SessionLocal
from models import hacker_news_daily
from utils import send_to_discord

logger = logging.getLogger(__name__)

MODEL_NAME = "qwen3:8b"
TODAY_STR = datetime.now().strftime("%Y-%m-%d")
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
    
    # Updated prompt to enforce brevity and prevent hallucinated formatting
    system_prompt = (
        "You are an expert tech analyst and Hacker News historian. "
        "Your job is to analyze a list of today's top Hacker News stories (Top, Ask HN, Show HN) and extract the overarching themes, tools, and developer sentiment. "
        "Output your response strictly in the following format:\n\n"
        "- **1.** [5 word headline]: [1-2 short sentences describing the trend]\n"
        "- **2.** [5 word headline]: [1-2 short sentences describing the trend]\n"
        "- **3.** [5 word headline]: [1-2 short sentences describing the trend]\n"
        "- **4.** [5 word headline]: [1-2 short sentences describing the trend]\n"
        "- **5.** [5 word headline]: [1-2 short sentences describing the trend]\n\n"
        "**Rising Technologies/Keywords**:\n"
        "[Comma separated list of specific tech or repeating keywords, e.g., Rust, TPUs, Local LLMs]\n"
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

def load_hn_data():
    """Reads today's data from the database and formats it for the LLM."""
    logger.info("Fetching today's Hacker News stories from the database...")
    db = SessionLocal()
    today = date.today()
    
    try:
        # Query the database for today's stories, ordered by highest score
        stories = db.query(hacker_news_daily).filter(hacker_news_daily.date_scraped == today).order_by(hacker_news_daily.score.desc()).all()
        
        if not stories:
            return None
            
        formatted_stories = [f"[{s.category}] (Score: {s.score}) {s.title}" for s in stories]
        return "\n".join(f"{i+1}. {story}" for i, story in enumerate(formatted_stories))
    except Exception as e:
        logger.error(f"Failed to query database: {e}")
        return None
    finally:
        db.close()

hn_avatar = "https://news.ycombinator.com/y18.svg"
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1496808041428025465/0stNNhf2EHyjNld8vhD0oHJ9CF7rzLGM6rRCNlIG32ILLuCLFmIN1QC3cId7ZZEizOzf"

def main():
    try:
        # Step 1: Load Data from DB
        stories_text = load_hn_data()
        if not stories_text:
            logger.warning("No Hacker News stories found for today. Exiting.")
            return
            
        # Step 2: Analyze with Ollama
        analysis = analyze_trends(stories_text)
        
        # Step 3: Save insights locally
        save_insights(analysis)
        
        # Step 4: Broadcast to Discord
        full_message = f"## 📈 Hacker News Daily Pulse: {TODAY_STR}\n\n{analysis}"
        send_to_discord(DISCORD_WEBHOOK_URL, full_message, username="HN Trend Bot", avatar_url="https://news.ycombinator.com/y18.svg")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")

if __name__ == "__main__":
    # Standardize our logging format if running standalone
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s - %(message)s")
    main()