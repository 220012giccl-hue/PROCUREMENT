import json
import os
from ..config.settings import DATA_DIR

class ProcurementLogic:
    def __init__(self):
        self.config_path = DATA_DIR / "config.json"
        self.config = self._load_config()

    def _load_config(self):
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except:
            return {"product_categories": {}}

    @staticmethod
    def compare_prices(quotes):
        if not quotes: return []
        # Sort and recommend logic here
        return quotes

    def filter_products_for_vendor(self, vendor_category, products):
        # Filtering logic based on categories
        return products
