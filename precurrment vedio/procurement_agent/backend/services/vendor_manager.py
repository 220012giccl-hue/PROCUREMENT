import json
import os
from ..config.settings import VENDORS_FILE

class VendorManager:
    def __init__(self):
        self.vendors_file = VENDORS_FILE
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        if not os.path.exists(self.vendors_file):
            os.makedirs(os.path.dirname(self.vendors_file), exist_ok=True)
            with open(self.vendors_file, "w") as f:
                json.dump([], f)

    def get_all_vendors(self):
        with open(self.vendors_file, "r") as f:
            return json.load(f)

    def add_vendor(self, name, email, category, region="", description=""):
        vendors = self.get_all_vendors()
        new_vendor = {
            "name": name,
            "email": email,
            "category": category,
            "region": region,
            "description": description
        }
        vendors.append(new_vendor)
        with open(self.vendors_file, "w") as f:
            json.dump(vendors, f, indent=4)
        return new_vendor

    def get_vendors_by_category(self, category):
        vendors = self.get_all_vendors()
        # Simple keyword matching for categories
        return [v for v in vendors if category.lower() in v['category'].lower()]

    def delete_vendor(self, email):
        vendors = self.get_all_vendors()
        vendors = [v for v in vendors if v['email'] != email]
        with open(self.vendors_file, "w") as f:
            json.dump(vendors, f, indent=4)
