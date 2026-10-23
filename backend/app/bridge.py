"""
================================================================================
🎓 RESTO INTEGRATION BRIDGE & SCHEMA ENRICHMENT
================================================================================
Author: Axar Tandon (3rd Year B.Tech CSE - AI/ML)
Target: https://github.com/Karan7s7n/resto
"""

import os
from typing import Dict, Any, Optional

RESTO_FACT_ENRICHMENT = {
    "paneer butter masala": {
        "spice_level": "Medium",
        "creaminess": "Rich & Creamy",
        "allergens": ["Dairy", "Nuts (Cashews)"],
        "gluten_free": True,
        "is_jain_possible": False,
        "jain_exclusion_reason": "Cooked base gravy contains brown onions and garlic paste.",
        "nutrition": {"kcal": 420, "protein_g": 18, "serving_size": "350g"}
    },
    "jain dal khichdi": {
        "spice_level": "Mild",
        "creaminess": "Soft Porridge",
        "allergens": ["Dairy (Ghee)"],
        "gluten_free": True,
        "is_jain_possible": True,
        "jain_notes": "100% Verified Jain: Yellow moong dal, aged basmati rice, pure ghee, jeera, hing.",
        "nutrition": {"kcal": 340, "protein_g": 14, "serving_size": "400g"}
    },
    "veg cheese pizza": {
        "spice_level": "Mild",
        "creaminess": "Cheesy",
        "allergens": ["Gluten (Wheat)", "Dairy (Mozzarella)"],
        "gluten_free": False,
        "is_jain_possible": False,
        "jain_exclusion_reason": "Marinara sauce contains garlic and onion powder.",
        "nutrition": {"kcal": 580, "protein_g": 16, "serving_size": "Regular 8-inch"}
    },
    "jain special capsicum & corn pizza": {
        "spice_level": "Mild",
        "creaminess": "Cheesy",
        "allergens": ["Gluten (Wheat)", "Dairy (Mozzarella)"],
        "gluten_free": False,
        "is_jain_possible": True,
        "jain_notes": "100% Verified Jain: Root-free tomato sauce, capsicum, sweet corn, mozzarella.",
        "nutrition": {"kcal": 510, "protein_g": 15, "serving_size": "Regular 8-inch"}
    }
}


class RestoBridge:
    """Bridges Karan7s7n/resto backend to ARPZO Voice Assistant."""

    def __init__(self, mongo_uri: Optional[str] = None):
        self.mongo_uri = mongo_uri or os.environ.get("MONGO_URI", "mongodb://localhost:27017/resto")

    def enrich_menu_item(self, raw_item: Dict[str, Any]) -> Dict[str, Any]:
        """Enriches raw MongoDB MenuItem from resto with verified culinary and dietary facts."""
        name_lower = raw_item.get("name", "").strip().lower()
        enrichment = RESTO_FACT_ENRICHMENT.get(name_lower, {})

        enriched = dict(raw_item)
        enriched["spice_level"] = enrichment.get("spice_level", "Medium (Default)")
        enriched["creaminess"] = enrichment.get("creaminess", "Standard")
        enriched["allergens"] = enrichment.get("allergens", [])
        enriched["gluten_free"] = enrichment.get("gluten_free", None)
        enriched["nutrition"] = enrichment.get("nutrition", {"kcal": None, "protein_g": None})
        enriched["jain_notes"] = enrichment.get("jain_notes", "Standard preparation.")

        if enriched.get("isJain") is True and not enrichment.get("is_jain_possible", True):
            enriched["isJain"] = False
            enriched["jain_warning"] = "Database flag corrected: dish contains prohibited root vegetables."

        return enriched

    def map_resto_order_to_call_assignment(self, resto_order: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Maps an active Resto order to a PrivateCallingManager assignment."""
        rider_id = resto_order.get("riderId")
        if not rider_id or resto_order.get("status") in ["CANCELLED", "PENDING_PAYMENT"]:
            return None

        return {
            "order_id": str(resto_order.get("_id", resto_order.get("order_id"))),
            "customer_id": str(resto_order.get("userId")),
            "driver_id": str(rider_id),
            "status": resto_order.get("status"),
            "delivered_at": resto_order.get("deliveredAt"),
            "is_cancelled": resto_order.get("status") == "CANCELLED"
        }
