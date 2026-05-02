# 1. Standard Library Imports
import csv
import logging
import re
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
import os

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

def generate_executive_summary(repo_data_string, model_name="gemma4:e4b"):
    """
    Sends the aggregated repository data to Ollama to generate a weekly trend summary.
    """
    prompt = f"""You are a senior technical analyst providing a weekly digest to a CTO. 
Your task is to group the following provided repositories into 5 to 7 emerging technology trends.

### TRENDING REPOSITORIES ###
{repo_data_string}

### INSTRUCTIONS ###
Write a 5 bullet point summary of the emerging trends found ONLY in the <repositories> data above. 
Focus on what technologies are gaining traction and what problems developers are trying to solve.
You must extract the EXACT text from the <name> tags to prove your trends.

You MUST follow a two-step process:
1. First, create a <think> block. Inside this block, analyze the data, group the repositories by trend, and verify that you have their exact <name> tags correct.
2. After the </think> block closes, output your final summary using this EXACT nested format:

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
    today = datetime.now()
    today_str = today.strftime("%Y-%m-%d")
    output_folder = OUTPUT_DIR / "github" / "digests"
    output_folder.mkdir(parents=True, exist_ok=True)
    output_md = output_folder / f"past_day_digest_{today_str}.md"

    logger.info("Gathering insights from the past day...")
    aggregated_data = "<repositories>\n"
    files_processed = 0
    for i in range(1):
        target_date = (today - timedelta(days=i)).strftime("%Y-%m-%d")
        input_csv = OUTPUT_DIR / "github" / "read_me_insights" / f"repo_insights_daily_{target_date}.csv"
        if input_csv.exists():
            logger.info(f"  - Found data for {target_date}")
            files_processed += 1
            aggregated_data += f"\n\n"
            try:
                with open(input_csv, mode="r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        aggregated_data += "<repo>\n"
                        aggregated_data += f"  <name>{row['repo_name']}</name>\n"
                        aggregated_data += f"  <topics>{row['key_topics']}</topics>\n"
                        aggregated_data += f"  <goal>{row['key_goals']}</goal>\n"
                        aggregated_data += (
                            f"  <use_cases>{row['key_use_cases']}</use_cases>\n"
                        )
                        aggregated_data += "</repo>\n"
            except Exception as e:
                logger.error(f"Error reading {input_csv}: {e}")
        else:
            logger.info(f"  - No data found for {target_date} (Skipping)")
    aggregated_data += "</repositories>"

    if (
        files_processed == 0
        or aggregated_data.strip() == "<repositories>\n</repositories>"
    ):
        logger.info(
            "\nNo CSV files found for the past day. Please run the analyze_readmes.py script first."
        )
        return

    logger.info(
        f"\n🤖 Synthesizing {files_processed} days of trends with Ollama... (This might take a moment depending on data size)"
    )
    
    logger.info("\nGenerating main trends...")
    summary = generate_executive_summary(aggregated_data, "qwen3:8b")
    logger.info("Formulating Deep Dive recommendation...")
    deep_dive = generate_deep_dive_recommendation(aggregated_data, "qwen3:8b")
    logger.info("Finding the Fun Pick...")
    fun_pick = generate_fun_pick(aggregated_data, "qwen3:8b")
    
    if summary:
        # Save everything to the local Markdown file as one cohesive document
        full_digest_content = f"{summary}\n\n---\n\n{deep_dive}\n\n---\n\n{fun_pick}"
        with open(output_md, mode='w', encoding='utf-8') as f:
            f.write(f"# Daily GitHub Trending Digest - {today_str}\n\n")
            f.write(full_digest_content)
        logger.info(f"\n✅ Success! Your daily digest has been saved locally to {output_md}")
        msg1 = f"**📊 {today_str} GitHub Trending Digest**\n\n{summary}"
        DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
        github_avatar = "https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png"
        send_to_discord(DISCORD_WEBHOOK_URL, msg1, username="Trending Repo Digest", avatar_url=github_avatar)
        time.sleep(1.5)
        send_to_discord(DISCORD_WEBHOOK_URL, deep_dive, username="Trending Repo Digest", avatar_url=github_avatar)
        time.sleep(1.5)
        send_to_discord(DISCORD_WEBHOOK_URL, fun_pick, username="Trending Repo Digest", avatar_url=github_avatar)
    else:
        logger.error("\n❌ Failed to generate the main summary. Halting execution.")

if __name__ == "__main__":
    main()