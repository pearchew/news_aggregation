import csv
from pathlib import Path
from datetime import datetime, timedelta, date
import ollama
import re
import time
import logging
from database_setup.database import SessionLocal
from database_setup.models import RepoInsight
from utils import send_to_discord

logger = logging.getLogger(__name__)
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1496808041428025465/0stNNhf2EHyjNld8vhD0oHJ9CF7rzLGM6rRCNlIG32ILLuCLFmIN1QC3cId7ZZEizOzf"

def generate_executive_summary(repo_data_string, model_name="gemma4:e4b"):
    """
    Sends the aggregated repository data to Ollama to generate a weekly trend summary.
    """
    prompt = f"""You are a senior technical analyst providing a weekly digest to a CTO. 
Your task is to group the following provided repositories into 5 to 7 emerging technology trends.

### TRENDING REPOSITORIES ###
{repo_data_string}

### INSTRUCTIONS ###
Write a 5-7 bullet point summary of the emerging trends found ONLY in the <repositories> data above. 
Focus on what technologies are gaining traction and what problems developers are trying to solve.
You must extract the EXACT text from the <name> tags to prove your trends.

You MUST follow a two-step process:
1. First, create a <think> block. Inside this block, analyze the data, group the repositories by trend, and verify that you have their exact <name> tags correct.
2. After the </think> block closes, output your final summary using this EXACT nested format:

- **[Trend Name]**
  - Repositories: [name1, name2]
  - Summary: [1-2 sentences describing the trend based on the data]

You MUST use this EXACT nested format for your output. List the repositories BEFORE writing the summary:

- **[Trend Name]**
  - Repositories: [name1, name2]
  - Summary: [1-2 sentences describing the trend based on the data]

Example Output:
- **Rise of Autonomous AI Agents**
  - Repositories: agentic-sdlc-handbook, ai-agents-for-beginners
  - Summary: Tools and frameworks for building and orchestrating AI agents are dominating, focusing on automating complex workflows and software development lifecycles.

Begin the bullet points now:"""

    try:
        response = ollama.chat(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": 0.0},
        )
        raw_content = response["message"]["content"]
        clean_content = re.sub(r'<think>.*?</think>', '', raw_content, flags=re.DOTALL).strip()
        return clean_content
    except Exception as e:
        logger.error(f"Ollama Error: {e}")
        return None

def generate_fun_pick(repo_data_string, model_name="qwen3:8b"):
    """
    Asks the model to find the most quirky, unique, or fun project in the dataset.
    """
    prompt = f"""You are a senior technical analyst providing a weekly digest to a CTO. 
Your task is to find the single most "fun", quirky, or uniquely niche project from the provided repositories.

### TRENDING REPOSITORIES ###
{repo_data_string}

### INSTRUCTIONS ###
Select ONE repository that stands out as a "fun pick". This should be something that solves a highly specific, unusual problem, is gamified, or is just generally entertaining compared to standard enterprise tools.

You MUST follow a two-step process:
1. First, create a <think> block. Inside this block, evaluate the repositories for their "fun" or "quirky" factor. Choose the best one and note its exact <name>.
2. After the </think> block closes, output your selection using this EXACT format:

**🎉 Fun Pick of the Week: [Exact Repo Name]**
[2-3 sentences explaining what it does and why it's a fun, quirky, or unique project that brings a little joy or novelty to the tech space.]
"""
    
    try:
        response = ollama.chat(
            model=model_name,
            messages=[{'role': 'user', 'content': prompt}],
            options={'temperature': 0.4} # Slightly higher temperature here to allow a bit of personality
        )
        
        raw_content = response['message']['content']
        clean_content = re.sub(r'<think>.*?</think>', '', raw_content, flags=re.DOTALL).strip()
        return clean_content
        
    except Exception as e:
        logger.error(f"Ollama Error in fun pick: {e}")
        return ""

def generate_deep_dive_recommendation(repo_data_string, model_name="qwen3:8b"):
    """
    Asks the model to highlight one specific repository that warrants serious enterprise investigation.
    """
    prompt = f"""You are a senior technical analyst providing a weekly digest to a CTO. 
Your task is to identify ONE repository from the provided data that has the highest potential for real-world enterprise application, ROI, or strategic advantage.

### TRENDING REPOSITORIES ###
{repo_data_string}

### INSTRUCTIONS ###
Select the ONE repository that the CTO and engineering leadership should seriously investigate this week.

You MUST follow a two-step process:
1. First, create a <think> block. Inside this block, evaluate the repositories based on enterprise value, potential to reduce costs, improve developer velocity, or solve major architectural pain points. Choose the strongest candidate and note its exact <name>.
2. After the </think> block closes, output your recommendation using this EXACT format:

**🔍 CTO Deep Dive Recommendation: [Exact Repo Name]**
**Why you should care:** [2-3 sentences providing a hard, business-focused justification on its real-world application, potential ROI, or how it solves a critical enterprise bottleneck. Speak directly to the CTO.]
"""
    
    try:
        response = ollama.chat(
            model=model_name,
            messages=[{'role': 'user', 'content': prompt}],
            options={'temperature': 0.0} # Keep this at 0.0 for strict, serious analytical focus
        )
        
        raw_content = response['message']['content']
        clean_content = re.sub(r'<think>.*?</think>', '', raw_content, flags=re.DOTALL).strip()
        return clean_content
        
    except Exception as e:
        logger.error(f"Ollama Error in deep dive: {e}")
        return ""

def main():
    today = date.today()
    today_str = today.strftime("%Y-%m-%d")
    
    output_folder = Path("outputs") / Path("gh_insights")
    output_folder.mkdir(parents=True, exist_ok=True)
    output_md = output_folder / f"past_day_digest_{today_str}.md"

    logger.info("Gathering repository insights from the database...")
    db = SessionLocal()
    
    try:
        # 2. Query the database instead of CSVs
        todays_insights = db.query(RepoInsight).filter(RepoInsight.date_scraped == today).all()
        
        if not todays_insights:
            logger.warning("No repository insights found in the database for today. Please run generate_repo_analysis.py first.")
            return

        logger.info(f"Found {len(todays_insights)} analyzed repositories for today.")
        
        # 3. Build the XML-like string for Ollama
        aggregated_data = "<repositories>\n"
        for insight in todays_insights:
            aggregated_data += "<repo>\n"
            aggregated_data += f"  <name>{insight.repo_name}</name>\n"
            aggregated_data += f"  <topics>{insight.key_topics}</topics>\n"
            aggregated_data += f"  <goal>{insight.key_goals}</goal>\n"
            aggregated_data += f"  <use_cases>{insight.key_use_cases}</use_cases>\n"
            aggregated_data += "</repo>\n"
        aggregated_data += "</repositories>"

    except Exception as e:
        logger.error(f"Database query failed: {e}")
        return
    finally:
        db.close()

    logger.info(f"\n🤖 Synthesizing trends with Ollama... (This might take a moment depending on data size)")
    
    # 4. Generate the digests (Your prompt logic stays untouched)
    summary = generate_executive_summary(aggregated_data, "qwen3:8b")
    deep_dive = generate_deep_dive_recommendation(aggregated_data, "qwen3:8b")
    fun_pick = generate_fun_pick(aggregated_data, "qwen3:8b")
    
    if summary:
        # Save locally
        full_digest_content = f"{summary}\n\n---\n\n{deep_dive}\n\n---\n\n{fun_pick}"
        with open(output_md, mode='w', encoding='utf-8') as f:
            f.write(f"# Weekly GitHub Trending Digest - Ending {today_str}\n\n")
            f.write(full_digest_content)
        logger.info(f"✅ Success! Your weekly digest has been saved locally to {output_md}")
        
        # Send to Discord using utils
        github_avatar = "https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png"
        
        msg1 = f"**📊 Past 7 day GitHub Trending Digest ({today_str})**\n\n{summary}"
        send_to_discord(DISCORD_WEBHOOK_URL, msg1, username="Trending Repo Digest", avatar_url=github_avatar)
        time.sleep(1.5)
        
        if deep_dive:
            send_to_discord(DISCORD_WEBHOOK_URL, deep_dive, username="Trending Repo Digest", avatar_url=github_avatar)
            time.sleep(1.5)
            
        if fun_pick:
            send_to_discord(DISCORD_WEBHOOK_URL, fun_pick, username="Trending Repo Digest", avatar_url=github_avatar)
            
    else:
        logger.error("❌ Failed to generate the main summary. Halting execution.")

if __name__ == "__main__":
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s - %(message)s")
    main()