import csv
from pathlib import Path
from datetime import datetime, timedelta
import ollama
import requests

DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1496808041428025465/0stNNhf2EHyjNld8vhD0oHJ9CF7rzLGM6rRCNlIG32ILLuCLFmIN1QC3cId7ZZEizOzf"

def send_to_discord(webhook_url, content):
    """
    Sends the generated summary to a Discord channel via webhook.
    """
    print("\nSending summary to Discord...")
    
    # Discord has a 2000 character limit for the 'content' field.
    # If the summary is too long, we truncate it to avoid a 400 Bad Request error.
    if len(content) > 2000:
        print("Warning: Digest exceeds 2000 characters. Truncating for Discord limit...")
        content = content[:1993] + "..."
        
    payload = {
        "content": content,
        "username": "Trending Repo Digest", # You can customize the bot's name here
        "avatar_url": "https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png" # Optional GitHub logo
    }
    
    try:
        response = requests.post(webhook_url, json=payload)
        response.raise_for_status()
        print("✅ Successfully posted to Discord!")
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to send to Discord: {e}")

def generate_executive_summary(repo_data_string, model_name="gemma4:e4b"):
    """
    Sends the aggregated repository data to Ollama to generate a weekly trend summary.
    """
    prompt = f"""
    You are a senior technical analyst providing a weekly digest to a CTO. 
    Here are the top trending GitHub repositories over the past 7 days, including their topics, goals, and use cases.
    Some repositories might appear multiple times if they trended on multiple days.
    
    {repo_data_string}
    
    Based on this data, write a 5-10 bullet points (adjust the amount of bullet points as you see fit) that act as a summary of the emerging trends in software development this week.
    Focus on what technologies are gaining traction, what problems developers are trying to solve, and any notable shifts in the ecosystem.
    In each bullet point, make sure to include the relevant repository names and their key topics to provide context.
    The tone should be concise, insightful, and suitable for a CTO audience looking to stay informed about the latest trends in the software development world.
    """
    
    try:
        response = ollama.chat(
            model=model_name,
            messages=[{'role': 'user', 'content': prompt}],
            options={'temperature': 0.6}
        )
        return response['message']['content']
    except Exception as e:
        print(f"Ollama Error: {e}")
        return None

def main():
    # Setup paths
    today = datetime.now()
    today_str = today.strftime("%Y-%m-%d")
    output_folder = Path("outputs")
    output_md = output_folder / f"weekly_digest_{today_str}.md"

    print("Gathering insights from the past 7 days...")
    
    aggregated_data = ""
    files_processed = 0

    # Loop backwards through the past 7 days (including today)
    for i in range(7):
        target_date = (today - timedelta(days=i)).strftime("%Y-%m-%d")
        input_csv = output_folder / f"repo_insights_daily_{target_date}.csv"

        if input_csv.exists():
            print(f"  - Found data for {target_date}")
            files_processed += 1
            aggregated_data += f"\n### Trending Repos on {target_date} ###\n"
            
            try:
                with open(input_csv, mode='r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        aggregated_data += f"- Repo: {row['repo_name']}\n"
                        aggregated_data += f"  Topics: {row['key_topics']}\n"
                        aggregated_data += f"  Goal: {row['key_goals']}\n"
                        aggregated_data += f"  Use Cases: {row['key_use_cases']}\n\n"
            except Exception as e:
                print(f"Error reading {input_csv}: {e}")
        else:
            print(f"  - No data found for {target_date} (Skipping)")

    if files_processed == 0 or not aggregated_data.strip():
        print("\nNo CSV files found for the past 7 days. Please run the analyze_readmes.py script first.")
        return

    # 2. Feed to Ollama for the final synthesis
    print(f"\n🤖 Synthesizing {files_processed} days of trends with Ollama... (This might take a moment depending on data size)")
    summary = generate_executive_summary(aggregated_data)

    # 3. Save the final digest
    if summary:
        with open(output_md, mode='w', encoding='utf-8') as f:
            f.write(f"# Weekly GitHub Trending Digest - Ending {today_str}\n\n")
            f.write(summary)
        print(f"✅ Success! Your weekly digest has been saved to {output_md}")
        
        # print("\n--- BEGIN DIGEST ---\n")
        # print(summary)
        
        # print("\n--- END DIGEST ---")
        
        discord_message = f"**📊 Past 7 day GitHub Trending Digest ({today_str})**\n\n{summary}"
        
        # Send to Discord
        send_to_discord(DISCORD_WEBHOOK_URL, discord_message)
    else:
        print("Failed to generate the summary.")

if __name__ == "__main__":
    main()