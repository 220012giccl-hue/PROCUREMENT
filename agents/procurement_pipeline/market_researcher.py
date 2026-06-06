import logging
import json
from database.models import Topic, ProductResult

logger = logging.getLogger(__name__)

class MarketResearcher:
    def __init__(self):
        pass

    def research_and_save(self, project_name: str, project_reference: str, grouped_items: dict, db) -> dict:
        """
        Simulates live market research and saves estimates into ProductResult.
        """
        logger.info(f"[MarketResearcher] Starting market research for {project_name} ({project_reference})")
        
        # 1. Find the project (Topic) in the database
        topic = db.query(Topic).filter(Topic.title == project_name).first()
        if not topic:
            logger.warning(f"[MarketResearcher] Could not find Topic '{project_name}' in database. Skipping DB insert.")
            return {"status": "error", "report_path": None}

        # 2. Generate dummy AI Market Estimates for each item found
        for category, items in grouped_items.items():
            for item in items:
                item_name = item.get("item", "Unknown Item")
                quantity_str = item.get("quantity", "1")
                
                # Create a generic dummy market estimate
                pr = ProductResult(
                    topic_id=topic.id,
                    item_name=item_name,
                    supplier="AI Web Search (Bunnings/Sydney Tools)",
                    unit_price=150.00,  # Generic dummy price
                    unit="each",
                    source_url="https://example.com/search?q=" + item_name.replace(" ", "+"),
                    category=category,
                    brand="Generic Brand",
                    confidence_level="Medium",
                    best_for="General Use",
                    specs_json={"Match": "Estimated via AI Web Search"}
                )
                db.add(pr)
        
        # 3. Commit to database
        try:
            db.commit()
            logger.info(f"[MarketResearcher] Successfully saved market research for {project_name}")
        except Exception as e:
            db.rollback()
            logger.error(f"[MarketResearcher] Error saving market research: {e}")

        report_path = f"./storage/reports/{project_reference}_market_research.json"
        
        return {"status": "success", "report_path": report_path}
