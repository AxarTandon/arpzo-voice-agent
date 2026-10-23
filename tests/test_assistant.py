#!/usr/bin/env python3
"""
================================================================================
🤖 ARPZO ASSISTANT ACCEPTANCE TESTS (A01 - A15)
================================================================================
Author: Axar Tandon (3rd Year B.Tech CSE - AI/ML)
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.tools import (
    search_menu,
    get_menu_item,
    propose_cart,
    get_reorder_proposal,
    get_order_status,
    get_preferences
)
from backend.app.assistant import SimulatorAssistantEngine


class TestAssistantCapabilities(unittest.TestCase):

    def setUp(self):
        self.sim = SimulatorAssistantEngine()

    def test_a01_voice_text_multilingual(self):
        """A01: Supports English, Hindi, and Hinglish with transcript understanding."""
        r1 = self.sim.handle_message("Jain Dal Khichdi Full add kar do")
        self.assertIn("Khichdi", r1)
        self.sim.reset()
        r2 = self.sim.handle_message("Jain pizza add karo")
        self.assertTrue("Jain Special Capsicum & Corn Pizza" in r2 or "size" in r2)

    def test_a02_verified_menu_facts(self):
        """A02: Search returns verified branch items only; spice & creaminess from facts."""
        pbm = get_menu_item("PBM_01")
        self.assertEqual(pbm["creaminess"], "Rich & Creamy")
        self.assertEqual(pbm["spice_level"], "Medium")

    def test_a03_strict_jain_rules(self):
        """A03: Absolute exclusion of root vegetables (potato, onion, garlic, carrot, radish)."""
        jain_items = search_menu("all", is_jain=True)
        jain_ids = [i["item_id"] for i in jain_items]
        self.assertNotIn("PBM_01", jain_ids)
        self.assertNotIn("VCP_03", jain_ids)
        self.assertNotIn("CB_05", jain_ids)
        self.assertIn("JDK_02", jain_ids)
        self.assertIn("JCP_04", jain_ids)

        # Inquiring about non-Jain dish returns polite educational explanation
        r = self.sim.handle_message("Mujhe Jain Paneer Butter Masala chahiye")
        self.assertTrue("pyaz aur lehsun" in r or "onion" in r)

    def test_a04_allergen_unknown_protection(self):
        """A04: Unknown allergy or cross contact state cannot become safe claim."""
        vcp = get_menu_item("VCP_03")
        self.assertFalse(vcp["gluten_free"])

    def test_a05_nutrition_data(self):
        """A05: Protein and calories returned from verified database facts."""
        pbm = get_menu_item("PBM_01")
        self.assertEqual(pbm["nutrition"]["protein_g"], 18)

    def test_a06_preference_memory(self):
        """A06: Consented preferences loaded with consent timestamp."""
        prefs = get_preferences("user_demo_101")
        self.assertEqual(prefs["diet"], "VEG")
        self.assertIn("Nuts", prefs["allergens"])
        self.assertIsNotNone(prefs["consented_at"])

    def test_a07_cart_pricing_math(self):
        """A07: Subtotal, 5% GST, and packaging fee calculated exactly."""
        items = [
            {"item_id": "JCP_04", "quantity": 1, "variant": "Regular"},  # 399
            {"item_id": "JDK_02", "quantity": 1, "variant": "Full"}       # 220
        ]
        prop = propose_cart(items)
        self.assertEqual(prop["subtotal"], 619.00)
        self.assertEqual(prop["tax_gst_5pct"], 30.95)
        self.assertEqual(prop["packaging_delivery_charge"], 25.00)
        self.assertEqual(prop["grand_total"], 674.95)
        self.assertTrue(prop["requires_confirmation"])

    def test_a08_cart_version_and_expiry(self):
        """A08: Cart version is stamped and expires in 2 minutes."""
        items = [{"item_id": "JDK_02", "quantity": 1, "variant": "Full"}]
        prop = propose_cart(items)
        self.assertEqual(prop["cart_version"], 1)
        self.assertIn("expires_at", prop)

    def test_a09_group_ordering(self):
        """A09: Group allocation under budget with per-person breakdown."""
        req = {
            "budget": 1500,
            "allocation": {"Person 1": "JCP_04", "Person 2": "JDK_02"}
        }
        items = [
            {"item_id": "JCP_04", "quantity": 1, "variant": "Regular"},
            {"item_id": "JDK_02", "quantity": 1, "variant": "Full"}
        ]
        prop = propose_cart(items, group_request=req)
        self.assertLessEqual(prop["grand_total"], 1500)
        self.assertIsNotNone(prop["group_allocation"])

    def test_a10_reorder_validation(self):
        """A10: Re-order checks active menu prices and notes changes."""
        prop = get_reorder_proposal("user_demo_101", "ord_past_001")
        self.assertEqual(prop["reorder_from_order_id"], "ord_past_001")
        self.assertEqual(len(prop["items"]), 2)
        self.assertGreater(len(prop["price_adjustments_noted"]), 0)

    def test_a11_live_tracking(self):
        """A11: Returns canonical tracking status and call eligibility."""
        status = get_order_status("ord_live_789", "user_demo_101")
        self.assertEqual(status["status"], "OUT_FOR_DELIVERY")
        self.assertTrue(status["can_call_driver"])

    def test_a15_size_clarification(self):
        """A15: Assistant politely asks for missing size/variant."""
        self.sim.reset()
        reply = self.sim.handle_message("Add capsicum pizza")
        self.assertIn("Regular", reply)
        self.assertIn("Medium", reply)


if __name__ == "__main__":
    unittest.main()
