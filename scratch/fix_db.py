import sys
import os

# Add the project root to sys.path
sys.path.append(os.getcwd())

from config.database import SessionLocal, engine
from sqlalchemy import text, inspect

def fix_db():
    db = SessionLocal()
    try:
        print("Checking priority_search_sources table...")
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        if 'priority_search_sources' not in tables:
            print("Table 'priority_search_sources' NOT FOUND. Attempting to create all tables...")
            from database.models import Base
            Base.metadata.create_all(bind=engine)
            print("Tables created.")
        else:
            columns = [c['name'] for c in inspector.get_columns('priority_search_sources')]
            print(f"Current columns: {columns}")
            
            if 'priority_for' not in columns:
                print("Adding 'priority_for' column...")
                db.execute(text("ALTER TABLE priority_search_sources ADD COLUMN priority_for VARCHAR(255)"))
                db.commit()
                print("Column added successfully.")
            else:
                print("'priority_for' column already exists.")
                
        print("Database sync complete.")
    except Exception as e:
        print(f"ERROR: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    fix_db()
