import subprocess
import sys
import logging 
import os

logging.basicConfig(
    level=logging.INFO, # Shows INFO, WARNING, ERROR, and CRITICAL logs
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

def run_script(script_path):
    """
    Helper function to run a python script using subprocess.
    Expects the relative path to the script.
    """
    logger.info(f"{'='*50}")
    logger.info(f"🚀 RUNNING: {script_path}")
    logger.info(f"{'='*50}")
    
    try:
        # sys.executable ensures we use the same Python interpreter running main.py
        result = subprocess.run([sys.executable, script_path], check=True)
        logger.info(f"✅ SUCCESSFULLY COMPLETED: {script_path}")
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ ERROR: {script_path} failed with exit code {e.returncode}")
        logger.error("Stopping workflow.")
        sys.exit(1)
    except FileNotFoundError:
        logger.error(f"❌ ERROR: Could not find script '{script_path}'")
        sys.exit(1)

def main():
    logger.info("🌟 STARTING NEWS AGGREGATION WORKFLOW 🌟")
    
    logger.info("\n--- GitHub Pipeline ---")
    run_script(os.path.join("github_workflow", "get_git.py"))
    run_script(os.path.join("github_workflow", "get_git_readme.py"))
    run_script(os.path.join("github_workflow", "generate_repo_analysis.py"))
    run_script(os.path.join("github_workflow", "generate_gh_digest.py"))
    
    # logger.info("\n--- Hacker News Pipeline ---")
    # run_script(os.path.join("hn_workflow", "get_hn.py"))
    # run_script(os.path.join("hn_workflow", "generate_hn_digest.py"))
    
    # logger.info("\n--- RSS Feeds Pipeline ---")
    # run_script(os.path.join("rss_feeds_workflow", "rss_feeds.py"))

    # logger.info("\n--- Website Scraping Pipeline ---")
    # run_script(os.path.join("website_scraping_workflow", "test_downloads.py"))

    logger.info("\n🎉 ALL PIPELINES COMPLETED SUCCESSFULLY! 🎉")

if __name__ == "__main__":
    main()