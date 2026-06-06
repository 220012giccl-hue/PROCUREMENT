"""
cleanup_duplicate_suppliers.py
Merges duplicate supplier records (same name, case-insensitive) into one,
transferring all RFQ + SupplierQuote references to the kept record.
"""
import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.database import SessionLocal
from database.models import Supplier, RFQ, SupplierQuote
from sqlalchemy import func

def merge_duplicates():
    db = SessionLocal()
    try:
        # 1. Find all lower-cased names that appear more than once
        dupes = (
            db.query(func.lower(Supplier.name).label('lname'), func.count(Supplier.id).label('cnt'))
            .group_by(func.lower(Supplier.name))
            .having(func.count(Supplier.id) > 1)
            .all()
        )

        if not dupes:
            print("[OK] No duplicate suppliers found. Database is clean!")
            return

        print(f"[!] Found {len(dupes)} duplicate supplier name(s) to merge:\n")
        total_removed = 0

        for row in dupes:
            lname = row.lname
            records = db.query(Supplier).filter(func.lower(Supplier.name) == lname).order_by(Supplier.id).all()
            
            # Keep the FIRST (oldest) record, merge the rest into it
            keeper = records[0]
            duplicates = records[1:]

            # Merge categories from all duplicates
            all_cats = set(c.strip() for c in (keeper.categories or '').split(',') if c.strip())
            for d in duplicates:
                all_cats.update(c.strip() for c in (d.categories or '').split(',') if c.strip())
            keeper.categories = ', '.join(sorted(all_cats))

            # Merge email if keeper is missing one
            if not keeper.email:
                for d in duplicates:
                    if d.email:
                        keeper.email = d.email
                        break

            print(f"  Merging '{keeper.name}' (ID {keeper.id}) <- {[d.id for d in duplicates]}")
            print(f"    Merged categories: {keeper.categories}")

            # Re-link RFQs and SupplierQuotes to the keeper
            for dup in duplicates:
                rfq_count = db.query(RFQ).filter(RFQ.supplier_id == dup.id).count()
                quote_count = db.query(SupplierQuote).filter(SupplierQuote.supplier_id == dup.id).count()
                
                if rfq_count > 0:
                    db.query(RFQ).filter(RFQ.supplier_id == dup.id).update({'supplier_id': keeper.id})
                    print(f"    Re-linked {rfq_count} RFQ(s) from ID {dup.id} -> {keeper.id}")
                
                if quote_count > 0:
                    db.query(SupplierQuote).filter(SupplierQuote.supplier_id == dup.id).update({'supplier_id': keeper.id})
                    print(f"    Re-linked {quote_count} SupplierQuote(s) from ID {dup.id} -> {keeper.id}")

                db.delete(dup)
                total_removed += 1

            db.flush()

        db.commit()
        print(f"\n[OK] Done! {total_removed} duplicate supplier record(s) removed.")
        print("[OK] All RFQs and SupplierQuotes have been re-linked to the canonical records.")

    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        print(f"\n[ERROR] {e}")
    finally:
        db.close()

if __name__ == "__main__":
    merge_duplicates()
