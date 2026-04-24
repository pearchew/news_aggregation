import os
import csv
from datetime import date, datetime
import gtrending
import logging
from database import SessionLocal
from models import repo_daily

logger = logging.getLogger(__name__)

def fetch_and_save_repos():
    logger.info("--- FETCHING REPOSITORIES & SAVING TO CSV ---")
    filter_since = "daily"
    
    logger.info(f"Fetching {filter_since} trending repositories...")
    
    repos = gtrending.fetch_repos(
        since=filter_since
    )
    
    if not repos:
        logger.warning("No repositories found for these filters.")
        return
    
    db = SessionLocal()
    today = date.today()
    
    try:
        for repo in repos:
            new_repo_entry = repo_daily(
                date_scraped=today,
                user_name=repo.get('author', ''),
                repo_name=repo.get('name', ''),
                repo_description=repo.get('description', ''),
                repo_url=repo.get('url', '')
            )
            # Add to the staging area
            db.add(new_repo_entry)
            
        # 4. Commit all new repos to the database
        db.commit()
        logger.info(f"✅ Successfully saved {len(repos)} repositories to the database.")
    except Exception as e:
        logger.error(f"❌ Error saving repositories to DB: {e}")
        db.rollback() # If something goes wrong, undo the changes
    finally:
        db.close()

def fetch_and_save_developers():
    logger.info("--- FETCHING DEVELOPERS & SAVING TO CSV ---")
    filter_since = "daily"
    logger.info(f"Fetching {filter_since} trending developers...")
    devs = gtrending.fetch_developers(
        since=filter_since
    )
    if not devs:
        logger.warning("No developers found for these filters.")
        return
    
    db = SessionLocal()
    today = date.today()
    
    try:
        count = 0
        for dev in devs:
            # Extract the nested repo dictionary if it exists
            repo_data = dev.get('repo', {})
            
            # 3. Map the gtrending developer data to your SQLAlchemy model
            # Note: For developers, the 'user_name' is usually under 'username'
            new_dev_entry = repo_daily(
                date_scraped=today,
                user_name=dev.get('username', ''),
                repo_name=repo_data.get('name', '') if isinstance(repo_data, dict) else '',
                repo_description=repo_data.get('description', '') if isinstance(repo_data, dict) else '',
                repo_url=repo_data.get('url', '') if isinstance(repo_data, dict) else ''
            )
            
            db.add(new_dev_entry)
            count += 1
            
        # 4. Commit all new developer repos to the database
        db.commit()
        logger.info(f"✅ Successfully saved {count} developer repos to the database.")
    except Exception as e:
        logger.error(f"❌ Error saving developers to DB: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    fetch_and_save_repos()
    fetch_and_save_developers()