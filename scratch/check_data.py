import sys
import os

# Add the project root to sys.path
sys.path.append(os.getcwd())

from config.database import SessionLocal
from database.models import PrioritySearchSource

def check_data():
    db = SessionLocal()
    try:
        sources = db.query(PrioritySearchSource).all()
        print(f"Found {len(sources)} sources.")
        for s in sources:
            print(f"ID: {s.id}, Name: {s.name}, URL: {s.url}, Priority: {s.priority}, PriorityFor: {s.priority_for}")
    except Exception as e:
        print(f"ERROR: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_data()
