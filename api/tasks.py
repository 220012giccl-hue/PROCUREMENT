import asyncio
from sqlalchemy.orm import Session
from database.models import User, Email
from agents.rfq_agent.style_agent import StyleAgent
from agents.rfq_agent.outlook_graph import OutlookGraphFetcher
from datetime import datetime

async def sync_user_writing_style(user_id: int, provider: str):
    """
    Background task to fetch last 50 sent emails and analyze writing style.
    """
    from config.database import SessionLocal
    db = SessionLocal()
    try:
        print(f"[TASK] Starting style sync for User {user_id} via {provider}...")
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            print(f"[TASK] User {user_id} not found.")
            return

        emails_to_analyze = []

        if provider == 'outlook':
            fetcher = OutlookGraphFetcher()
            if fetcher.connect():
                # Fetch last 50 sent emails
                sent_emails = fetcher.fetch_sent_emails(limit=50)
                for e in sent_emails:
                    emails_to_analyze.append({
                        "subject": e.get('subject', ''),
                        "body": e.get('body', '')
                    })
        
        elif provider == 'gmail':
            from agents.rfq_agent.gmail_api_client import GmailAPIFetcher
            fetcher = GmailAPIFetcher()
            if fetcher.connect():
                # Fetch last 50 sent emails
                sent_emails = fetcher.fetch_sent_emails(limit=50)
                for e in sent_emails:
                    emails_to_analyze.append({
                        "subject": e.get('subject', ''),
                        "body": e.get('body', '')
                    })

        if emails_to_analyze:
            # 1. Save to Database so manual sync and RFI Assistant can use them
            for e in emails_to_analyze:
                # Basic duplicate check
                exists = db.query(Email).filter(Email.subject == e['subject'], Email.body == e['body']).first()
                if not exists:
                    new_email = Email(
                        subject=e['subject'],
                        body=e['body'],
                        sender=user.email,
                        received_at=datetime.utcnow(),
                        is_sent=True,
                        thread_id="SYNC_HISTORICAL"
                    )
                    db.add(new_email)
            
            db.commit()

            # 2. Analyze Style
            style_agent = StyleAgent()
            guide = style_agent.extract_style_from_emails(emails_to_analyze)
            
            user.writing_style_guide = guide
            user.last_style_sync = datetime.utcnow()
            db.commit()
            print(f"[TASK] Style sync complete for User {user_id}. Guide updated and emails saved.")
        else:
            print(f"[TASK] No sent emails found to analyze for User {user_id}.")

    except Exception as e:
        print(f"[TASK] Error during style sync: {e}")
        db.rollback()
    finally:
        db.close()


async def run_market_research(topic_id: int, items: list):
    """
    Task 1: Triggered after context resolver successfully assigns a topic
    Searches supplier sources for item prices.
    Saves results to product_results table linked to topic_id.
    Updates rfq_workflows.status -> 'drafts_ready' when done.
    """
    from config.database import SessionLocal
    from database.models import ProductResult, RFQWorkflow
    db = SessionLocal()
    try:
        print(f"[TASK] Starting market research for topic {topic_id}")
        
        # Mocking the market research for now, as we don't have actual scraping logic
        for item in items:
            item_name = item.get("item_name", "Unknown Item")
            
            result = ProductResult(
                topic_id=topic_id,
                item_name=item_name,
                supplier="Bunnings", # Mock supplier
                unit_price=100.0,    # Mock price
                unit="each",
                source_url="https://www.bunnings.com.au"
            )
            db.add(result)
        
        # Update workflow status to drafts_ready
        workflow = db.query(RFQWorkflow).filter(RFQWorkflow.topic_id == topic_id).first()
        if workflow:
            workflow.status = 'drafts_ready'
        
        db.commit()
        print(f"[TASK] Market research complete for topic {topic_id}")
        
        # Trigger vendor drafting
        asyncio.create_task(trigger_vendor_drafting(topic_id))

    except Exception as e:
        print(f"[TASK] Error in market research: {e}")
        db.rollback()
    finally:
        db.close()


async def trigger_vendor_drafting(topic_id: int):
    """
    Task 2: Triggered after market research completes.
    Calls vendor_matcher -> passes matched suppliers to rfq_agent.
    rfq_agent generates draft emails and saves to rfqs table with status = 'Draft'.
    """
    from config.database import SessionLocal
    from agents.vendor_matcher.matcher import match_vendors
    from database.models import ProcurementItem, RFQ
    
    db = SessionLocal()
    try:
        print(f"[TASK] Triggering vendor drafting for topic {topic_id}")
        
        # 1. Fetch procurement items for this topic
        items = db.query(ProcurementItem).filter(ProcurementItem.project_id == topic_id).all()
        items_list = [{"item_name": i.item_name, "category": i.category} for i in items]
        
        # 2. Call vendor_matcher
        matches = match_vendors(items_list)
        
        # 3. Save as DRAFT in rfqs table (mocking rfq_agent drafting logic)
        for match in matches:
            for supplier in match.get("matched_suppliers", []):
                new_rfq = RFQ(
                    rfq_number=f"RFQ-{topic_id}-{supplier['name'].replace(' ', '')}",
                    project_id=topic_id,
                    supplier_id=supplier.get("id"),
                    status="DRAFT",
                    email_subject=f"Request for Quote: {match['item']}",
                    email_body=f"Dear {supplier['name']},\n\nPlease provide a quote for {match['item']}.\n\nRegards,"
                )
                db.add(new_rfq)
                
        db.commit()
        print(f"[TASK] Vendor drafting complete for topic {topic_id}")
        
    except Exception as e:
        print(f"[TASK] Error in vendor drafting: {e}")
        db.rollback()
    finally:
        db.close()


# ── NEW: Smart Procurement Pipeline Task (v2.1) ─────────────────────────────
async def run_smart_procurement_pipeline(
    email_subject: str,
    email_body: str,
    sender_name: str,
    sender_email: str,
    thread_id: str,
    provider: str = "gmail"
):
    """
    Background task — triggered when a new email is synced.
    Runs CategoryExtractor → VendorDraftBuilder → MarketResearcher.
    Additive: does NOT replace run_market_research or trigger_vendor_drafting.
    """
    from config.database import SessionLocal
    from agents.procurement_pipeline.pipeline import run_procurement_pipeline

    db = SessionLocal()
    try:
        print(f"[SMART-PIPELINE] Starting for thread: {thread_id}")
        result = await run_procurement_pipeline(
            email_subject=email_subject,
            email_body=email_body,
            sender_name=sender_name,
            sender_email=sender_email,
            thread_id=thread_id,
            provider=provider,
            db=db
        )
        print(f"[SMART-PIPELINE] Done. Status: {result.get('status')} | "
              f"Drafts: {result.get('drafts_created', 0)} | "
              f"Report: {result.get('report_path', 'none')}")
    except Exception as e:
        print(f"[SMART-PIPELINE] Error: {e}")
    finally:
        db.close()
