from sqlalchemy import Column, Integer, String, Text, Date
from database_setup.database import Base

class RepoInsight(Base):
    __tablename__ = "repo_insights"

    # Every database table needs a Primary Key (a unique ID)
    id = Column(Integer, primary_key=True, index=True)
    
    # These match the columns you were previously saving in your CSV
    date_scraped = Column(Date, index=True) # Adding a date so you can track trends over time!
    repo_name = Column(String, index=True)
    key_topics = Column(Text)
    key_goals = Column(Text)
    key_use_cases = Column(Text)
    
class repo_daily(Base):
    __tablename__ = "repo_daily"

    # Every database table needs a Primary Key (a unique ID)
    id = Column(Integer, primary_key=True, index=True)
    
    # These match the columns you were previously saving in your CSV
    date_scraped = Column(Date, index=True)
    user_name = Column(String, index=True)
    repo_name = Column(String, index=True)
    repo_description = Column(String)
    repo_url = Column(String)
    
class hacker_news_daily(Base):
    __tablename__ = "hacker_news_daily"
    id = Column(Integer, primary_key=True, index=True)
    date_scraped = Column(Date, index=True) 
    category = Column(String, index=True)  # e.g., "Ask HN", "Show HN", "Top Story"
    hn_id = Column(Integer, unique=True, index=True) 
    title = Column(String)
    author = Column(String)  
    score = Column(Integer)
    time_posted = Column(Integer) 
    url = Column(String)