import subprocess
import sys
import logging 

logging.basicConfig(
    level=logging.INFO, # Shows INFO, WARNING, ERROR, and CRITICAL logs
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

def run_script(script_name):
    """
    Helper function to run a python script using subprocess.
    """
    logger.info(f"{'='*50}")
    logger.info(f"🚀 RUNNING: {script_name}")
    logger.info(f"{'='*50}")
    
    try:
        # sys.executable ensures we use the same Python interpreter running main.py
        result = subprocess.run([sys.executable, script_name], check=True)
        logger.info(f"✅ SUCCESSFULLY COMPLETED: {script_name}")
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ ERROR: {script_name} failed with exit code {e.returncode}")
        logger.error("Stopping workflow.")
        sys.exit(1)
    except FileNotFoundError:
        logger.error(f"❌ ERROR: Could not find script '{script_name}'")
        sys.exit(1)

def main():
    logger.info("🌟 STARTING NEWS AGGREGATION WORKFLOW 🌟")
    logger.info("\n--- GitHub Pipeline ---")
    run_script("get_git.py")
    run_script("get_git_readme.py")
    run_script("generate_repo_analysis.py")
    run_script("generate_gh_digest.py")
    logger.info("\n--- Hacker News Pipeline ---")
    run_script("get_hn.py")
    run_script("generate_hn_digest.py")
    logger.info("\n🎉 ALL PIPELINES COMPLETED SUCCESSFULLY! 🎉")

if __name__ == "__main__":
    main()