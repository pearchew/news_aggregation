import subprocess
import sys
import logging

# Configure logging for the main orchestrator
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_script(script_path):
    """
    Runs a python script using the current python executable to maintain the virtual environment.
    """
    logger.info(f"========== Running {script_path} ==========")
    try:
        # sys.executable guarantees it uses the activated venv Python
        subprocess.run([sys.executable, script_path], check=True)
        logger.info(f"✅ Successfully finished {script_path}\n")
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Error running {script_path}. Process exited with code {e.returncode}\n")

def main():
    logger.info("🚀 Starting Autonomous Tech News & Trends Aggregator Pipeline...\n")

    # 1. Product Hunt Workflow
    run_script("product_hunt_workflow/get_ph.py")

    # 2. Hacker News Workflow
    # Note: Requires fetching data first, then generating the digest
    run_script("hn_workflow/get_hn.py")
    run_script("hn_workflow/generate_hn_digest.py")

    # 3. GitHub Workflow
    # Note: Sequentially fetches repos -> downloads readmes -> analyzes readmes -> generates digest
    run_script("github_workflow/get_git.py")
    run_script("github_workflow/get_git_readme.py")
    run_script("github_workflow/generate_repo_analysis.py")
    run_script("github_workflow/generate_gh_digest.py")

    # 4. Website Scraping Workflow
    run_script("website_scraping_workflow/scrape_orchestrator.py")

    # (RSS feeds workflow has been excluded from the main execution loop)

    logger.info("🎉 All workflows completed successfully!")

if __name__ == "__main__":
    main()