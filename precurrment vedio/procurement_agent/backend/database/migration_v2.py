import os
import sys

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.database.session import engine
from sqlalchemy import text

def migrate():
    with engine.connect() as conn:
        print("Checking for missing columns in 'quoted_prices'...")
        try:
            # Check if received_at exists
            conn.execute(text("SELECT received_at FROM quoted_prices LIMIT 1"))
            print("Column 'received_at' already exists.")
        except Exception:
            # Rollback for Postgres
            conn.execute(text("ROLLBACK"))
            print("Adding missing column 'received_at' to 'quoted_prices'...")
            conn.execute(text("ALTER TABLE quoted_prices ADD COLUMN received_at TIMESTAMP WITHOUT TIME ZONE"))
            conn.execute(text("COMMIT"))
            print("Successfully added 'received_at'.")

if __name__ == "__main__":
    migrate()
