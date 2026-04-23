import subprocess
import sys

def run_script(script_name):
    """
    Helper function to run a python script using subprocess.
    """
    print(f"\n{'='*50}")
    print(f"🚀 RUNNING: {script_name}")
    print(f"{'='*50}\n")
    
    try:
        # sys.executable ensures we use the same Python interpreter running main.py
        result = subprocess.run([sys.executable, script_name], check=True)
        print(f"\n✅ SUCCESSFULLY COMPLETED: {script_name}")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ ERROR: {script_name} failed with exit code {e.returncode}")
        print("Stopping workflow.")
        sys.exit(1)
    except FileNotFoundError:
        print(f"\n❌ ERROR: Could not find script '{script_name}'")
        sys.exit(1)

def main():
    print("🌟 STARTING NEWS AGGREGATION WORKFLOW 🌟")
    
    # ---------------------------------------------------------
    # 1. GITHUB TRENDING PIPELINE
    # ---------------------------------------------------------
    print("\n--- Phase 1: GitHub Pipeline ---")
    
    # Step 1.1: Get trending repositories
    run_script("get_git.py")
    
    # Step 1.2: Download READMEs for those repositories
    run_script("get_git_readme.py")
    
    # Step 1.3: Extract insights from READMEs using Ollama
    run_script("generate_repo_analysis.py")
    
    # Step 1.4: Generate the 7-day executive digest and send to Discord
    run_script("generate_gh_digest.py")


    # ---------------------------------------------------------
    # 2. HACKER NEWS PIPELINE
    # ---------------------------------------------------------
    print("\n--- Phase 2: Hacker News Pipeline ---")
    
    # Step 2.1: Scrape top Ask HN, Show HN, and Top Stories
    run_script("get_hn.py")
    
    # Step 2.2: Analyze trends using Ollama and send to Discord
    run_script("generate_hn_digest.py")

    print("\n🎉 ALL PIPELINES COMPLETED SUCCESSFULLY! 🎉")

if __name__ == "__main__":
    main()