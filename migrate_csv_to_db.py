import csv
from pathlib import Path
from datetime import datetime
from database import SessionLocal, engine, Base
from models import RepoInsight

def init_db():
    # This command actually creates the tables in insights.db based on models.py
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)

def migrate_data():
    db = SessionLocal()
    csv_dir = Path("outputs/gh_insights/csv")
    
    if not csv_dir.exists():
        print("No CSV directory found.")
        return

    # Find all your daily insight CSVs
    for csv_file in csv_dir.glob("repo_insights_daily_*.csv"):
        # Extract the date from the filename (e.g., "2026-04-24")
        date_str = csv_file.stem.split("_")[-1]
        scraped_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        
        print(f"Migrating data from {csv_file.name}...")
        
        with open(csv_file, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Create a new Python object for each row
                insight = RepoInsight(
                    date_scraped=scraped_date,
                    repo_name=row['repo_name'],
                    key_topics=row['key_topics'],
                    key_goals=row['key_goals'],
                    key_use_cases=row['key_use_cases']
                )
                # Add the object to our session workspace
                db.add(insight)
                
    # Commit all the additions to the database permanently
    db.commit()
    db.close()
    print("✅ Migration complete! All CSV data is now in insights.db")

if __name__ == "__main__":
    init_db()
    migrate_data()