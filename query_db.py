# query_db.py
from database import SessionLocal
from models import RepoInsight
from datetime import date

def run_queries():
    # 1. Open a session (your workspace)
    db = SessionLocal()

    print("\n--- 1. GET THE FIRST 3 RECORDS ---")
    # .limit(3) gets only 3 records, .all() executes the query
    first_three = db.query(RepoInsight).limit(3).all()
    
    for repo in first_three:
        print(f"Repo: {repo.repo_name} | Date: {repo.date_scraped}")
        print(f"Topics: {repo.key_topics}\n")

    print("\n--- 2. FILTER BY A SPECIFIC DATE ---")
    target_date = date(2026, 4, 24)
    # .filter() acts like a WHERE clause in SQL
    todays_repos = db.query(RepoInsight).filter(RepoInsight.date_scraped == target_date).all()
    
    print(f"Found {len(todays_repos)} repos trending on {target_date}.")

    print("\n--- 3. SEARCH FOR A SPECIFIC KEYWORD ---")
    # .ilike() is a case-insensitive search. The '%' are wildcards (meaning text can come before or after)
    ai_repos = db.query(RepoInsight).filter(RepoInsight.key_topics.ilike("%AI Agents%")).all()
    
    print(f"Found {len(ai_repos)} repos related to 'AI Agents':")
    for repo in ai_repos:
        print(f" - {repo.repo_name}")

    # Always close your session when done!
    db.close()

if __name__ == "__main__":
    run_queries()