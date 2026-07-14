print("Importing sqlalchemy...")
import sqlalchemy
print("SQLAlchemy imported successfully.")

print("Importing psycopg2...")
try:
    import psycopg2
    print("psycopg2 imported successfully.")
except Exception as e:
    print("Error importing psycopg2:", e)

print("Importing asyncpg...")
try:
    import asyncpg
    print("asyncpg imported successfully.")
except Exception as e:
    print("Error importing asyncpg:", e)

print("Running create_engine...")
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv
load_dotenv()
db_url = os.getenv("DATABASE_URL")
print("DATABASE_URL:", db_url)
try:
    engine = create_engine(db_url)
    print("Engine created.")
    # Attempt to connect to verify it's not a connection timeout
    print("Attempting to connect to the database...")
    connection = engine.connect()
    print("Connected successfully!")
    connection.close()
except Exception as e:
    print("Error with engine:", e)
