from sqlalchemy import text, inspect
from .session import engine, init_db

def run_migration():
    print("DEBUG: Starting database migration fix (Postgres Compatible)...")
    
    # 1. Initialize DB (create missing tables like quoted_prices)
    init_db()
    
    inspector = inspect(engine)
    
    with engine.connect() as conn:
        # --- Handle 'emails' table ---
        cols = [c['name'] for c in inspector.get_columns('emails')]
        print(f"DEBUG: Found emails columns: {cols}")
        
        if 'message_id' not in cols:
            print("DEBUG: Adding message_id to emails")
            conn.execute(text("ALTER TABLE emails ADD COLUMN message_id VARCHAR"))
            
        if 'sender' not in cols:
            if 'sender_email' in cols:
                print("DEBUG: Renaming sender_email to sender")
                conn.execute(text("ALTER TABLE emails RENAME COLUMN sender_email TO sender"))
            else:
                print("DEBUG: Adding sender to emails")
                conn.execute(text("ALTER TABLE emails ADD COLUMN sender VARCHAR"))
        
        if 'provider' not in cols:
            print("DEBUG: Adding provider to emails")
            conn.execute(text("ALTER TABLE emails ADD COLUMN provider VARCHAR"))
            if 'provider_id' in cols:
                conn.execute(text("UPDATE emails SET provider = provider_id"))

        if 'is_processed' not in cols:
            print("DEBUG: Adding is_processed to emails")
            conn.execute(text("ALTER TABLE emails ADD COLUMN is_processed BOOLEAN DEFAULT FALSE"))

        if 'is_read' not in cols:
            print("DEBUG: Adding is_read to emails")
            conn.execute(text("ALTER TABLE emails ADD COLUMN is_read BOOLEAN DEFAULT FALSE"))

        # --- Handle 'vendor_drafts' table ---
        cols_drafts = [c['name'] for c in inspector.get_columns('vendor_drafts')]
        if 'recipient' not in cols_drafts:
            print("DEBUG: Adding recipient to vendor_drafts")
            conn.execute(text("ALTER TABLE vendor_drafts ADD COLUMN recipient VARCHAR"))
        if 'vendor_name' not in cols_drafts:
            print("DEBUG: Adding vendor_name to vendor_drafts")
            conn.execute(text("ALTER TABLE vendor_drafts ADD COLUMN vendor_name VARCHAR"))
        if 'source_id' not in cols_drafts:
            print("DEBUG: Adding source_id to vendor_drafts")
            conn.execute(text("ALTER TABLE vendor_drafts ADD COLUMN source_id INTEGER"))

        conn.commit()
    print("DEBUG: Migration check complete.")
