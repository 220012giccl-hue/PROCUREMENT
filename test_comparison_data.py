import os
import sys
from datetime import datetime

# Path setup for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Fix Windows encoding
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from config.database import SessionLocal, init_db
from database.models import Contact, Topic, RFQ, Supplier, SupplierQuote, ProductResult

def seed_test_data():
    print("[*] Connecting to Database...")
    init_db()
    db = SessionLocal()
    
    try:
        # -- 1. Demo Contact
        print("[*] Creating Demo Contact...")
        c = Contact(contact_name='BuildCo Engineering', email_domain='buildco.com.au',
                    contact_emails=['purchasing@buildco.com.au'])
        db.add(c)
        db.flush()

        # -- 2. Demo Projects (Topics)
        print("[*] Creating Demo Projects...")
        p1 = Topic(contact_id=c.id, topic_name='Site A Office Fitout',
                   topic_reference='PRJ-2026-001', status='ACTIVE')
        p2 = Topic(contact_id=c.id, topic_name='Greenfield Warehouse Build',
                   topic_reference='PRJ-2026-002', status='ACTIVE')
        db.add_all([p1, p2])
        db.flush()

        # -- 3. Demo Suppliers (upsert — no duplicates)
        print("[*] Creating Demo Suppliers...")

        def get_or_create_supplier(name, email, categories):
            """Find existing or create new supplier (case-insensitive name match)."""
            s = db.query(Supplier).filter(Supplier.name.ilike(name)).first()
            if s:
                # Merge categories
                new_cats = set(c.strip() for c in categories.split(',') if c.strip())
                old_cats = set(c.strip() for c in (s.categories or '').split(',') if c.strip())
                s.categories = ', '.join(sorted(old_cats | new_cats))
                db.flush()
                return s
            sup = Supplier(name=name, email=email, categories=categories)
            db.add(sup)
            db.flush()
            return sup

        s_bunnings  = get_or_create_supplier('Bunnings Trade',  'trade@bunnings.com.au',   'Hardware, Building Materials')
        s_sydney    = get_or_create_supplier('Sydney Tools',    'sales@sydneytools.com.au', 'Tools, Power Tools')
        s_blackwood = get_or_create_supplier('Blackwoods',      'orders@blackwoods.com.au', 'PPE, Safety')

        # ---- PROJECT 1: Site A Office Fitout
        # Items: LED Downlight (Building Materials), Safety Helmet (PPE),
        #        PVC Pipe (Building Materials), Door Handle (Building Materials)
        print("[*] Creating RFQs for Project 1...")

        r_led   = RFQ(rfq_number='RFQ-TEST2026-002', project_id=p1.id, supplier_id=s_bunnings.id,
                      quantity='30 units', status='RECEIVED',
                      technical_requirements='LED Downlight 10W')
        r_helm  = RFQ(rfq_number='RFQ-TEST2026-003', project_id=p1.id, supplier_id=s_blackwood.id,
                      quantity='20 sets', status='SENT',
                      technical_requirements='Safety Helmet EN397')
        r_pipe  = RFQ(rfq_number='RFQ-TEST2026-001', project_id=p1.id, supplier_id=s_bunnings.id,
                      quantity='50m', status='RECEIVED',
                      technical_requirements='PVC Pipe 50mm')
        r_door  = RFQ(rfq_number='RFQ-TEST2026-004', project_id=p1.id, supplier_id=s_sydney.id,
                      quantity='15 sets', status='APPROVED',
                      technical_requirements='Door Handle Set')
        db.add_all([r_led, r_helm, r_pipe, r_door])
        db.flush()

        # Vendor Quotes for Project 1
        print("[*] Adding Vendor Quotes for Project 1...")
        sq_led1 = SupplierQuote(
            rfq_id=r_led.id, supplier_id=s_sydney.id,
            quoted_price=18.00, lead_time='2-3 days',
            warranty='2 Years', compliance_notes='AS/NZS 60598',
            status='SELECTED',
            brand='Philips',
            specs_json={"Wattage": "10W", "Lumens": "1050 lm", "IP Rating": "IP44", "Colour Temp": "4000K"}
        )
        sq_pipe1 = SupplierQuote(
            rfq_id=r_pipe.id, supplier_id=s_sydney.id,
            quoted_price=13.50, lead_time='1 week',
            warranty=None, compliance_notes='AS/NZS 1260',
            status='PENDING',
            brand='Vinidex',
            specs_json={"Diameter": "50mm", "Material": "uPVC", "Pressure Class": "PN12", "Length": "6m"}
        )
        sq_pipe2 = SupplierQuote(
            rfq_id=r_pipe.id, supplier_id=s_bunnings.id,
            quoted_price=11.00, lead_time='3-5 days',
            warranty=None, compliance_notes='AS/NZS 1260',
            status='REVIEWED',
            brand='Vinidex',
            specs_json={"Diameter": "50mm", "Material": "uPVC", "Pressure Class": "PN12", "Length": "6m"}
        )
        db.add_all([sq_led1, sq_pipe1, sq_pipe2])
        db.flush()

        # AI Market Research for Project 1
        print("[*] Adding AI Market Research for Project 1...")
        ai_led = ProductResult(
            topic_id=p1.id, item_name='LED Downlight 10W',
            supplier='Beacon Lighting', unit_price=22.00, unit='each',
            source_url='https://www.beaconlighting.com.au/led-downlight-10w',
            category='Building Materials',
            brand='Beacon',
            confidence_level='High',
            best_for='Commercial office fit-out',
            specs_json={"Wattage": "10W", "Lumens": "900 lm", "IP Rating": "IP44", "Colour Temp": "4000K"}
        )
        ai_pipe1 = ProductResult(
            topic_id=p1.id, item_name='PVC Pipe 50mm',
            supplier='Reece Plumbing', unit_price=11.80, unit='m',
            source_url='https://www.reece.com.au/pvc-pipe-50mm',
            category='Building Materials',
            brand='Vinidex',
            confidence_level='High',
            best_for='Drainage and stormwater',
            specs_json={"Diameter": "50mm", "Material": "uPVC", "Pressure Class": "PN12", "Compliance": "AS/NZS 1260"}
        )
        ai_pipe2 = ProductResult(
            topic_id=p1.id, item_name='PVC Pipe 50mm',
            supplier='Bunnings', unit_price=12.50, unit='m',
            source_url='https://www.bunnings.com.au/pvc-pipe-50mm',
            category='Building Materials',
            brand='Iplex',
            confidence_level='Medium',
            best_for='General plumbing',
            specs_json={"Diameter": "50mm", "Material": "uPVC", "Pressure Class": "PN10", "Compliance": "AS/NZS 1260"}
        )
        ai_helm = ProductResult(
            topic_id=p1.id, item_name='Safety Helmet EN397',
            supplier='Blackwoods', unit_price=45.00, unit='each',
            source_url='https://www.blackwoods.com.au/safety-helmet-en397',
            category='PPE',
            brand='3M',
            confidence_level='High',
            best_for='General construction site use',
            specs_json={"Safety Rating": "EN397 / AS/NZS 1801", "Size Range": "S-XL", "Material": "ABS Plastic", "Adjustment": "Ratchet"}
        )
        db.add_all([ai_led, ai_pipe1, ai_pipe2, ai_helm])

        # ---- PROJECT 2: Greenfield Warehouse Build
        # Items: Cordless Drill (Tools), Safety Boots (PPE)
        print("[*] Creating RFQs for Project 2...")
        r_drill = RFQ(rfq_number='RFQ-TEST2026-010', project_id=p2.id, supplier_id=s_sydney.id,
                      quantity='5 units', status='RECEIVED',
                      technical_requirements='Cordless Hammer Drill 18V')
        r_boots = RFQ(rfq_number='RFQ-TEST2026-011', project_id=p2.id, supplier_id=s_blackwood.id,
                      quantity='20 pairs', status='RECEIVED',
                      technical_requirements='Safety Boots Steel Cap')
        db.add_all([r_drill, r_boots])
        db.flush()

        # Vendor Quotes for Project 2
        print("[*] Adding Vendor Quotes for Project 2...")
        sq_drill1 = SupplierQuote(
            rfq_id=r_drill.id, supplier_id=s_sydney.id,
            quoted_price=339.00, lead_time='2 days',
            warranty='3 Years', compliance_notes=None,
            status='SELECTED',
            brand='Milwaukee',
            specs_json={"Voltage": "18V", "Battery Included": "Yes (2x 5Ah)", "Warranty": "3 Years", "Chuck Size": "13mm"}
        )
        sq_drill2 = SupplierQuote(
            rfq_id=r_drill.id, supplier_id=s_bunnings.id,
            quoted_price=345.00, lead_time='In Stock',
            warranty='3 Years', compliance_notes=None,
            status='REVIEWED',
            brand='DeWalt',
            specs_json={"Voltage": "18V", "Battery Included": "Yes (1x 5Ah)", "Warranty": "3 Years", "Chuck Size": "13mm"}
        )
        sq_boots1 = SupplierQuote(
            rfq_id=r_boots.id, supplier_id=s_blackwood.id,
            quoted_price=89.00, lead_time='In Stock',
            warranty='6 Months', compliance_notes='AS/NZS 2210',
            status='SELECTED',
            brand='Blundstone',
            specs_json={"Safety Rating": "AS/NZS 2210.3", "Size Range": "US 6-15", "Material": "Full Grain Leather", "Toe Cap": "Steel"}
        )
        db.add_all([sq_drill1, sq_drill2, sq_boots1])
        db.flush()

        # AI Market Research for Project 2
        print("[*] Adding AI Market Research for Project 2...")
        ai_drill1 = ProductResult(
            topic_id=p2.id, item_name='Cordless Hammer Drill 18V',
            supplier='Sydney Tools', unit_price=349.00, unit='each',
            source_url='https://www.sydneytools.com.au/milwaukee-m18-hammer-drill',
            category='Tools',
            brand='Milwaukee',
            confidence_level='High',
            best_for='Heavy-duty commercial construction',
            specs_json={"Voltage": "18V", "Battery Included": "Yes", "Warranty": "5 Years", "Chuck Size": "13mm"}
        )
        ai_drill2 = ProductResult(
            topic_id=p2.id, item_name='Cordless Hammer Drill 18V',
            supplier='Bunnings', unit_price=299.00, unit='each',
            source_url='https://www.bunnings.com.au/dewalt-18v-drill',
            category='Tools',
            brand='DeWalt',
            confidence_level='Medium',
            best_for='General construction use',
            specs_json={"Voltage": "18V", "Battery Included": "Yes", "Warranty": "3 Years", "Chuck Size": "13mm"}
        )
        ai_boots = ProductResult(
            topic_id=p2.id, item_name='Safety Boots Steel Cap',
            supplier='Blackwoods', unit_price=95.00, unit='pair',
            source_url='https://www.blackwoods.com.au/blundstone-safety-boots',
            category='PPE',
            brand='Blundstone',
            confidence_level='High',
            best_for='General construction site',
            specs_json={"Safety Rating": "AS/NZS 2210.3", "Size Range": "US 5-14", "Material": "Leather", "Toe Cap": "Steel"}
        )
        db.add_all([ai_drill1, ai_drill2, ai_boots])

        db.commit()
        print("\n[OK] TEST DATA SUCCESSFULLY INJECTED!")
        print("=" * 60)
        print("Projects created:")
        print("  Project 1: Site A Office Fitout       (ID: %d)  -- 4 RFQs" % p1.id)
        print("  Project 2: Greenfield Warehouse Build  (ID: %d)  -- 2 RFQs" % p2.id)
        print()
        print("Categories covered:")
        print("  [Tools]             Cordless Hammer Drill 18V")
        print("  [PPE]               Safety Helmet EN397, Safety Boots")
        print("  [Building Materials] LED Downlight 10W, PVC Pipe 50mm")
        print()
        print("Now test:")
        print("  1. Go to http://localhost:8069/rfq.html")
        print("  2. Click 'View Report' on any project")
        print("  3. You should see category-grouped comparison tables")
        print("=" * 60)

    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        print("[ERROR] Error injecting test data:", e)
    finally:
        db.close()

if __name__ == "__main__":
    seed_test_data()
