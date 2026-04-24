Here is a comprehensive, exhaustive README for your newly modernized project. You can copy and paste this directly into a `README.md` file in the root of your project directory. 

***

# 🌐 Autonomous Tech News & Trends Aggregator

An end-to-end, fully automated pipeline that scrapes, analyzes, and summarizes the bleeding edge of the tech industry. 

This project pulls daily trending repositories from GitHub and top stories from Hacker News. Instead of just giving you a list of links, it uses local Large Language Models (via Ollama) to read repository READMEs and forum posts, synthesize the overarching trends, and deliver a clean, executive-level markdown digest directly to your Discord server. All historical data is persistently stored in a local SQLite database for future querying and analytics.

## ✨ Key Features
* **GitHub Trending Analysis:** Scrapes daily trending repositories and developers, downloads their READMEs, and uses AI to extract key topics, goals, and use cases.
* **Hacker News Pulse:** Pulls the top Ask HN, Show HN, and Top Stories, using AI to deduce the current sentiment and rising technologies in the developer community.
* **Local AI Processing:** 100% private and free AI summarization utilizing Ollama.
* **Relational Database:** Replaces messy CSVs with an industry-standard SQLite database using SQLAlchemy ORM, featuring duplicate-prevention and efficient querying.
* **Discord Integration:** Automatically formats and beams formatted, highly readable digests to a Discord channel.

---

## 🛠️ Step-by-Step Setup Guide

Follow these instructions to get the pipeline running on your local machine.

### Step 1: Prerequisites
Before touching the code, ensure you have the following installed on your system:
1.  **Python 3.8+**
2.  **Ollama:** Download and install [Ollama](https://ollama.com/) to run local LLMs.
3.  **A Discord Server:** You need a server where you have permission to create a Webhook. 

### Step 2: Environment Setup
It is highly recommended to isolate the project dependencies using a Virtual Environment (`venv`). 

1. Open your terminal and navigate to the project directory.
2. Create the virtual environment:
   ```bash
   python -m venv venv
   ```
3. Activate the virtual environment:
   * **Mac/Linux:** `source venv/bin/activate`
   * **Windows:** `venv\Scripts\activate`
*(You should now see `(venv)` at the start of your terminal prompt).*

### Step 3: Install Dependencies
With your environment activated, install the required packages using the provided `requirements.txt`:
```bash
pip install -r requirements.txt
```
*(This will install everything you need, including `sqlalchemy`, `ollama`, `requests`, and `gtrending`).*

### Step 4: Download Local AI Models
This project relies on two specific LLMs via Ollama to generate the summaries. Open a separate terminal window and pull them:
```bash
ollama pull qwen3:8b
ollama pull gemma4:e4b
```
*(Note: Make sure the Ollama application is running in the background before moving forward).*

### Step 5: Configure Your Discord Webhook
To receive the digests, you need to provide the scripts with your unique Discord Webhook URL.
1. In Discord, go to **Server Settings > Integrations > Webhooks** and click **New Webhook**.
2. Copy the Webhook URL.
3. Open `generate_gh_digest.py` and `generate_hn_digest.py` in your code editor.
4. Replace the `DISCORD_WEBHOOK_URL` string near the top of both files with your copied URL.

### Step 6: Initialize the Database
Before running the scrapers, we must build the SQLite database tables (`repo_daily`, `repo_insights`, and `hacker_news_daily`). 

Open your terminal (with the `venv` activated) and run the interactive Python shell:
```bash
python
```
Then, paste these exact three lines and hit Enter:
```python
from database import engine, Base
import models 
Base.metadata.create_all(bind=engine)
```
Type `exit()` to leave the shell. You will now see an `insights.db` file in your project folder!

---

## 🚀 Running the Pipeline

You don't need to run the scripts one by one. The project includes a master orchestrator script. 

To run the entire pipeline from start to finish, simply execute:
```bash
python main.py
```

**What happens when you run this?**
1. **`get_git.py`**: Scrapes trending GitHub data and saves it to the DB.
2. **`get_git_readme.py`**: Queries the DB for today's repos and downloads their READMEs.
3. **`generate_repo_analysis.py`**: Reads the READMEs, asks Ollama (`gemma4:e4b`) to extract insights, and saves them to the DB.
4. **`generate_gh_digest.py`**: Queries the extracted insights, asks Ollama (`qwen3:8b`) to write an executive digest, saves a local Markdown file, and posts to Discord.
5. **`get_hn.py`**: Scrapes Hacker News APIs and saves top posts to the DB.
6. **`generate_hn_digest.py`**: Queries the DB, asks Ollama to identify overarching trends, logs the data to JSONL, and posts to Discord.

---

## 🗄️ How to View and Query Your Database

All of your scraped data and AI insights are safely stored in `insights.db`. Here are the best ways to explore it:

### 1. Inside VS Code (Recommended)
You don't need to leave your code editor to see your data!
* **For quick viewing:** Install the **"SQLite Viewer"** extension. Click on `insights.db` in your file tree to see a spreadsheet-like view of your tables.
* **For writing SQL:** Install the **"SQLTools"** extension (along with the SQLite driver). You can connect to `insights.db` and run custom SQL queries directly in the editor.

### 2. Using Python Scripts
You can programmatically query your database to build custom analytics. A sample script called `query_db.py` is included in the project. 
Run it to see examples of how to fetch the latest repos, filter by date, or search for specific keywords like "AI Agents":
```bash
python query_db.py
```

### 3. Dedicated Desktop GUI
If you want a robust graphical interface, download [DB Browser for SQLite](https://sqlitebrowser.org/) (Free/Open Source). Open the application, click "Open Database", select `insights.db`, and use the "Browse Data" or "Execute SQL" tabs.