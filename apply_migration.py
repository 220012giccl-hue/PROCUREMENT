import os
import sys

# Path setup for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.database import SessionLocal, engine
from sqlalchemy import text

def apply_migration():
    print("Applying migration 006...")
    with engine.connect() as conn:
        with open('database/migrations/006_add_dynamic_specs.sql', 'r') as f:
            sql = f.read()
            
        # execute statements one by one
        for statement in sql.split(';'):
            statement = statement.strip()
            if statement:
                try:
                    conn.execute(text(statement))
                    print(f"Executed: {statement[:50]}...")
                except Exception as e:
                    print(f"Error executing statement: {e}")
        
        conn.commit()
    print("Migration applied successfully!")

if __name__ == "__main__":
    apply_migration()
