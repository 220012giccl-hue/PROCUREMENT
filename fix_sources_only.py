"""
Fix Priority Search Sources
- Saray sources delete karo
- Sirf Blackwoods aur Sydney Tools raho
"""
import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from config.database import SessionLocal, init_db
from database.models import PrioritySearchSource

init_db()
db = SessionLocal()

try:
    # Saray existing sources delete karo
    deleted = db.query(PrioritySearchSource).delete()
    db.commit()
    print(f"Removed {deleted} old sources.")

    # Sirf yeh do add karo
    only_sources = [
        {
            "name": "Blackwoods",
            "url": "https://www.blackwoods.com.au/",
            "priority": 10,
            "priority_for": "Industrial & Safety",
            "is_active": True,
        },
        {
            "name": "Sydney Tools",
            "url": "https://sydneytools.com.au/",
            "priority": 10,
            "priority_for": "Tools & Equipment",
            "is_active": True,
        },
    ]

    for s in only_sources:
        source = PrioritySearchSource(**s)
        db.add(source)

    db.commit()
    print("Done! Only Blackwoods and Sydney Tools are now in the Priority Search Sources list.")
    print("  - Blackwoods: https://www.blackwoods.com.au/")
    print("  - Sydney Tools: https://sydneytools.com.au/")

except Exception as e:
    db.rollback()
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()
