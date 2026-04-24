from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# 1. The Engine: This is the actual connection to the database file.
# SQLite will create "insights.db" in your root folder automatically.
SQLALCHEMY_DATABASE_URL = "sqlite:///./insights.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False} # Needed for SQLite in Python
)

# 2. The Session: This is your "workspace" for database operations. 
# You open a session, make changes, and then commit them.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 3. The Base: All of our database models will inherit from this class.
Base = declarative_base()