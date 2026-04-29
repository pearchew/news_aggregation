import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, StorageContext

# Import your newly refactored scraper functions
# Import your newly refactored scraper functions
from website_scraping_workflow.bis import scrape_bis
from website_scraping_workflow.cc_judge import scrape_cc_judge
from website_scraping_workflow.hkma_annual import scrape_hkma_annual
from website_scraping_workflow.hkma_research import scrape_hkma_research
from website_scraping_workflow.sfc import scrape_sfc
from website_scraping_workflow.taylor_wessing_md import scrape_taylor_wessing
import os
# Load from the environment variables (loaded by main.py)
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

root_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(root_dir))
from utils import process_single_paper_no_rag, send_to_discord

# Ensure this matches your actual webhook URL

def main():
    print("Starting Autonomous Research Aggregator...")
    
    # Define the 7-day cutoff window
    # Ensure timezone awareness matches the server you run this on
    cutoff_date = datetime.now() - timedelta(days=7)
    
    # Map friendly source names to their respective scraper functions
    scrapers = [
        ("BIS Innovation Hub", scrape_bis),
        ("Cambridge Judge Business School", scrape_cc_judge),
        ("HKMA Annual Reports", scrape_hkma_annual),
        ("HKMA Research", scrape_hkma_research),
        ("SFC Research", scrape_sfc),
        ("Taylor Wessing Insights", scrape_taylor_wessing),
    ]

    all_new_files = []

    # 1. Scrape all sources
    for source_name, scraper_func in scrapers:
        print(f"\n--- Checking {source_name} for updates in the last 7 days ---")
        try:
            new_files = scraper_func(cutoff_date)
            # Tag each file with its source for the AI context
            for file_path in new_files:
                all_new_files.append((source_name, Path(file_path)))
        except Exception as e:
            print(f"❌ Error executing scraper for {source_name}: {e}")

    print(f"\n=== Scraping Complete. Found {len(all_new_files)} new files ===")

    # 2. Process new files through LlamaIndex & Ollama
    for source_name, file_path in all_new_files:
        print(f"\n🧠 Sending '{file_path.name}' to LLM for insight extraction...")
        try:
            # Note: process_single_paper_no_rag handles PDFs and Markdown natively via SimpleDirectoryReader
            insights = process_single_paper_no_rag(file_path, source_name)

            # 3. Format the Discord Message
            discord_msg = f"## 📄 New Research Alert: {source_name}\n"
            discord_msg += f"**Title:** {insights['paper_title']}\n"
            discord_msg += f"**1. Conclusion:**\n{insights['insight_1']}\n"
            discord_msg += f"**2. Policy/Economic Impact:**\n{insights['insight_2']}\n"
            discord_msg += f"**3. Methodology:**\n{insights['insight_3']}\n"
            discord_msg += f"**4. Applications/Beneficiaries:**\n{insights['insight_4']}\n"

            # 4. Send to Discord
            send_to_discord(
                webhook_url=DISCORD_WEBHOOK_URL, 
                content=discord_msg, 
                username="Research Analyst Bot",
                avatar_url="https://cdn-icons-png.flaticon.com/512/3022/3022558.png" # Optional custom icon
            )
            
        except Exception as e:
            print(f"❌ Error processing or sending insights for {file_path.name}: {e}")

if __name__ == "__main__":
    main()