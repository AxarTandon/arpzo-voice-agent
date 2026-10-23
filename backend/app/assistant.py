"""
================================================================================
🤖 ARPZO VOICE ASSISTANT ENGINE (OLLAMA + SIMULATOR)
================================================================================
Author: Axar Tandon (3rd Year B.Tech CSE - AI/ML)
Specification Reference: Section 3 (Customer journeys), Section 4 (Architecture)
"""

import os
import json
import re
import urllib.request
import urllib.error
from typing import Dict, Any, List, Optional

from .config import OLLAMA_BASE_URL, OLLAMA_MODEL
from .tools import (
    search_menu,
    get_menu_item,
    propose_cart,
    get_reorder_proposal,
    get_order_status,
    get_preferences,
    format_proposal_box
)
from .security import SecurityGuard

ARPZO_OLLAMA_SYSTEM_PROMPT = """
You are the AI Voice & Text Food Ordering Assistant for the ARPZO Restaurant Platform.
Created by Axar Tandon (3rd Year B.Tech CSE - AI/ML).
You speak friendly, polite, natural Hinglish (fluent English-Hindi blend) and English.

CRITICAL INSTRUCTIONS & GUARDRAILS:
1. NEVER guess or hallucinate menu items or prices! All prices and taxes are calculated by backend tools.
2. JAIN FOOD RULE: Absolutely NO root vegetables (no onions, no garlic, no potatoes, no carrots, no radishes).
   - If a customer requests a non-Jain dish like Paneer Butter Masala in Jain mode, politely explain:
     "Paneer Butter Masala Jain nahi ban sakta kyunki iski gravy me pyaz aur lehsun (onion & garlic) hota hai. Hamare paas Jain Special Capsicum & Corn Pizza (Rs 399) aur Jain Dal Khichdi (Rs 220) available hain!"
3. CLARIFY SIZES: If size/variant is missing (e.g. Regular vs Medium, Half vs Full), politely ask before adding.
4. CONFIRMATION GATE: Before placing an order, show the proposal card with grand total and ask:
   "Kya main ye order confirm kar doon?" Never finalize without explicit confirmation.
5. PUSH-TO-TALK & EDITABLE TRANSCRIPT: Always acknowledge what you heard accurately.
"""


class OllamaAssistantEngine:
    """Connects to a locally running Ollama instance (e.g. `ollama run llama3` or `mistral`)."""

    def __init__(self, base_url: str = OLLAMA_BASE_URL, model: str = OLLAMA_MODEL):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.chat_history: List[Dict[str, str]] = [
            {"role": "system", "content": ARPZO_OLLAMA_SYSTEM_PROMPT}
        ]

    def is_available(self) -> bool:
        """Checks if local Ollama daemon is reachable."""
        try:
            req = urllib.request.Request(f"{self.base_url}/api/tags")
            with urllib.request.urlopen(req, timeout=1.5) as resp:
                return resp.status == 200
        except Exception:
            return False

    def generate_response(self, user_text: str) -> str:
        """Sends user message to Ollama API with security sanitization."""
        # Security sanitization
        is_safe, clean_text, warning = SecurityGuard.sanitize_user_input(user_text)
        if not is_safe:
            return f"⚠️ Security Alert: {warning}"

        self.chat_history.append({"role": "user", "content": clean_text})
        payload = json.dumps({
            "model": self.model,
            "messages": self.chat_history,
            "stream": False,
            "options": {"temperature": 0.2}
        }).encode("utf-8")

        req = urllib.request.Request(
            f"{self.base_url}/api/chat",
            data=payload,
            headers={"Content-Type": "application/json"}
        )

        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            reply = data.get("message", {}).get("content", "")
            self.chat_history.append({"role": "assistant", "content": reply})
            return reply


class SimulatorAssistantEngine:
    """Deterministic conversational state machine replicating Ollama reasoning
    with Hinglish nuance, strict dietary guardrails, and security filtering.
    """

    def __init__(self):
        self.pending_items: List[Dict[str, Any]] = []
        self.last_proposal: Optional[Dict[str, Any]] = None
        self.awaiting_variant_item: Optional[Dict[str, Any]] = None
        self.awaiting_confirmation: bool = False

    def reset(self):
        self.pending_items.clear()
        self.last_proposal = None
        self.awaiting_variant_item = None
        self.awaiting_confirmation = False

    def handle_message(self, user_msg: str) -> str:
        # 0. Security Guardrail Check (Prompt Injection Defense)
        is_safe, clean_msg, warning = SecurityGuard.sanitize_user_input(user_msg)
        if not is_safe:
            return f"⚠️ Security Notice: {warning}"

        msg = clean_msg.strip().lower()

        # 1. Reset command
        if msg in ["reset", "clear", "nayi shuruat", "start over"]:
            self.reset()
            return "Cart reset ho gaya hai! Batayein, aaj kya order karna chahenge?"

        # 2. Confirmation gate handling
        if self.awaiting_confirmation and self.last_proposal:
            if any(w in msg for w in ["haan", "yes", "confirm", "theek hai", "kardo", "kar do", "proceed", "done", "order kar do"]):
                p_id = self.last_proposal["proposal_id"]
                tot = self.last_proposal["grand_total"]
                self.awaiting_confirmation = False
                self.pending_items.clear()
                return (
                    f"Dhanyawaad! Aapka order successfully confirm ho gaya hai!\n"
                    f"Order ID: {p_id}\n"
                    f"Payable Total: INR {tot:.2f} (including 5% GST & packaging)\n"
                    f"Kitchen khana prepare kar raha hai. Rider live tracking active ho chuki hai! "
                    f"Dhanyawaad ARPZO choose karne ke liye!"
                )
            elif any(w in msg for w in ["nahi", "no", "cancel", "change", "badlo", "mat karo"]):
                self.awaiting_confirmation = False
                return "Koi baat nahi! Order confirm nahi kiya gaya hai. Kya aap kuch change ya add karna chahenge?"

        # 3. Variant / Size clarification response
        if self.awaiting_variant_item:
            target = self.awaiting_variant_item
            self.awaiting_variant_item = None
            chosen_var = "Regular"
            if "medium" in msg:
                chosen_var = "Medium"
            elif "large" in msg:
                chosen_var = "Large"
            elif "full" in msg:
                chosen_var = "Full"
            elif "half" in msg:
                chosen_var = "Half"

            qty_match = re.search(r'\b(\d+)\b', msg)
            quantity = int(qty_match.group(1)) if qty_match else 1

            self.pending_items.append({
                "item_id": target["item_id"],
                "quantity": quantity,
                "variant": chosen_var
            })

            proposal = propose_cart(self.pending_items)
            self.last_proposal = proposal
            self.awaiting_confirmation = True

            return (
                f"Maine {quantity} {target['name']} ({chosen_var}) aapke cart me add kar diya hai.\n\n"
                f"{format_proposal_box(proposal)}\n\n"
                f"Total amount INR {proposal['grand_total']:.2f} hai. Kya main ye order confirm kar doon?"
            )

        # 4. Paneer Butter Masala (Strict Jain Rule check)
        if "paneer" in msg:
            if "jain" in msg:
                return (
                    "Maaf kijiye, Paneer Butter Masala Jain nahi ban sakta kyunki iski base gravy me "
                    "pyaz aur lehsun (onion & garlic) use hota hai. Lekin hamare paas verified "
                    "'Jain Special Capsicum & Corn Pizza' (Rs. 399) aur 'Jain Dal Khichdi' (Rs. 220) available hain! "
                    "Inme se kya try karna chahenge?"
                )
            item = get_menu_item("PBM_01")
            if not any(v in msg for v in ["half", "full"]):
                self.awaiting_variant_item = item
                return "Paneer Butter Masala ke liye konsa portion chahiye aapko? Half (Rs. 180) ya Full (Rs. 280)?"
            chosen = "Half" if "half" in msg else "Full"
            self.pending_items.append({"item_id": "PBM_01", "quantity": 1, "variant": chosen})
            prop = propose_cart(self.pending_items)
            self.last_proposal = prop
            self.awaiting_confirmation = True
            return f"Paneer Butter Masala ({chosen}) add ho gaya!\n\n{format_proposal_box(prop)}\n\nKya main ye confirm kar doon?"

        # 5. Pizza & Capsicum handling
        if "pizza" in msg or "capsicum" in msg:
            if "veg cheese" in msg and "jain" in msg:
                return (
                    "Hamara standard Veg Cheese Pizza Jain nahi hai kyunki iske marinara sauce me garlic/onion hota hai. "
                    "Aap hamara 100% verified 'Jain Special Capsicum & Corn Pizza' choose kar sakte hain! Kya main wo add kar doon?"
                )
            target_id = "JCP_04" if "jain" in msg else "VCP_03"
            item = get_menu_item(target_id)
            if not any(sz in msg for sz in ["regular", "medium", "large"]):
                self.awaiting_variant_item = item
                return (
                    f"{item['name']} ke liye konsa size chahiye? Regular (Rs. {item['variants']['Regular']}), "
                    f"Medium (Rs. {item['variants']['Medium']}) ya Large (Rs. {item['variants']['Large']})?"
                )
            chosen_sz = "Regular"
            if "medium" in msg:
                chosen_sz = "Medium"
            elif "large" in msg:
                chosen_sz = "Large"
            self.pending_items.append({"item_id": target_id, "quantity": 1, "variant": chosen_sz})
            prop = propose_cart(self.pending_items)
            self.last_proposal = prop
            self.awaiting_confirmation = True
            return f"Maine {item['name']} ({chosen_sz}) add kar diya hai.\n\n{format_proposal_box(prop)}\n\nKya main ye confirm kar doon?"

        # 6. Jain Khichdi
        if "khichdi" in msg:
            self.pending_items.append({"item_id": "JDK_02", "quantity": 1, "variant": "Full"})
            prop = propose_cart(self.pending_items)
            self.last_proposal = prop
            self.awaiting_confirmation = True
            return f"Jain Dal Khichdi (Full) add kar di gayi hai.\n\n{format_proposal_box(prop)}\n\nKya main ye order confirm kar doon?"

        # 7. Repeat / Re-order request (Task A07/A10)
        if any(w in msg for w in ["repeat", "same as last time", "pichla order", "reorder"]):
            prop = get_reorder_proposal("user_demo_101")
            if "error" in prop:
                return f"Maaf kijiye: {prop['error']}"
            self.last_proposal = prop
            self.awaiting_confirmation = True
            note = f" (Price updates: {', '.join(prop['price_adjustments_noted'])})" if prop.get('price_adjustments_noted') else ""
            return f"Aapka pichla order verify kar liya gaya hai{note}:\n\n{format_proposal_box(prop)}\n\nKya main isse confirm kar doon?"

        # 8. Live tracking status
        if any(w in msg for w in ["track", "status", "kahan pahucha", "delivery status", "rider"]):
            status = get_order_status("ord_live_789", "user_demo_101")
            return (
                f"Order Status: {status['status']}\n"
                f"Rider Assigned: {status['rider_name']}\n"
                f"Estimated Arrival: ~{status.get('estimated_delivery_mins', 15)} mins.\n"
                f"Private calling active hai. Driver se call connect karne ke liye 'call driver' bole."
            )

        # 9. General menu or Jain food search
        if "jain" in msg or "kya hai" in msg or "menu" in msg:
            is_jain_filter = "jain" in msg
            items = search_menu("all", is_jain=is_jain_filter)
            names = [f"{i['name']} (Rs. {i['base_price']})" for i in items]
            tag = "Verified Jain" if is_jain_filter else "Popular"
            return f"ARPZO me ye {tag} options available hain:\n- " + "\n- ".join(names) + "\n\nAapko kya add karwana hai?"

        return "Namaste! Main ARPZO AI Voice Assistant hoon. Aap kya order karna chahenge? (e.g., 'Jain Dal Khichdi add kardo', 'Pizza chahiye', ya 'track order')"
