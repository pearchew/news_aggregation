import logging
from dotenv import load_dotenv

# --- Import your workflow main functions ---
# These imports rely on the __init__.py files being present in the respective folders
from product_hunt_workflow.get_ph import main as get_ph_main
from hn_workflow.get_hn import scrape_hn_to_csv
from hn_workflow.generate_hn_digest import main as generate_hn_main
from github_workflow.get_git import main as get_git_main
from github_workflow.get_git_readme import main as get_git_readme_main
from github_workflow.generate_repo_analysis import main as generate_repo_analysis_main
from github_workflow.generate_gh_digest import main as generate_gh_digest_main
from website_scraping_workflow.scrape_orchestrator import main as scrape_orchestrator_main

# Configure logging at the root level exactly once
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    # Load environment variables from the .env file
    load_dotenv()
    
    logger.info("🚀 Starting Autonomous Tech News & Trends Aggregator Pipeline...\n")

    try:
        logger.info("========== Running Product Hunt Workflow ==========")
        get_ph_main()
    except Exception as e:
        logger.error(f"❌ Product Hunt Workflow failed: {e}")

    try:
        logger.info("========== Running Hacker News Workflow ==========")
        scrape_hn_to_csv()
        generate_hn_main()
    except Exception as e:
        logger.error(f"❌ Hacker News Workflow failed: {e}")

    try:
        logger.info("========== Running GitHub Workflow ==========")
        get_git_main()
        get_git_readme_main()
        generate_repo_analysis_main()
        generate_gh_digest_main()
    except Exception as e:
        logger.error(f"❌ GitHub Workflow failed: {e}")

    try:
        logger.info("========== Running Website Scraping Workflow ==========")
        scrape_orchestrator_main()
    except Exception as e:
        logger.error(f"❌ Website Scraping Workflow failed: {e}")

    logger.info("🎉 All workflows completed successfully!")

if __name__ == "__main__":
    main()