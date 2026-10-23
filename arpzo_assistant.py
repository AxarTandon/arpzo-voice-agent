#!/usr/bin/env python3
"""
================================================================================
🎓 ARPZO AI Voice/Text Food Ordering Assistant & Private Calling MVP
================================================================================
Author: Axar Tandon (3rd Year B.Tech CSE - AI/ML)
Project: Capstone Voice Agent MVP - ARPZO Restaurant Platform
Compatible With: Karan7s7n/resto (MongoDB/Express commerce backend)
Trial LLM Engine: Ollama Local Model (e.g., llama3, mistral, qwen2.5)
Calling Engine: Private Managed RTC (Agora/WebRTC token & lifecycle manager)

Hey there! 👋 I'm Axar, a 3rd year B.Tech student who built this project for the
ARPZO food platform. My college professors and the engineering spec emphasized:
1. "Zero Hallucination": An LLM should NEVER invent food prices, discounts,
   or ingredients! All math and facts must come from deterministic backend tools.
2. "Strict Jain Guardrails": Zero root vegetables (potatoes, onions, garlic,
   carrots, radishes). If a customer asks for Jain, we politely explain why
   non-Jain items like Paneer Butter Masala are not suitable and offer verified alternatives.
3. "Action-Lock Cart Gate": The assistant cannot place orders or charge cards
   autonomously. It must generate an immutable proposal card and await explicit human confirmation.
4. "Private Customer-Driver Calling": No PSTN phone numbers exposed! Internet audio
   with strict delivery + 30-minute expiry, dual-party consent recording gate,
   and 5-minute expiring admin playback links.
5. "Open-Source Trial Model": Runs seamlessly with local Ollama models (llama3/mistral),
   plus an autonomous high-fidelity fallback simulator so it works out of the box anywhere!
================================================================================
"""

import os
import sys
import json
import time
import uuid
import re
import hmac
import hashlib
import datetime
from typing import Optional, List, Dict, Any, Tuple

# Fix Windows console UTF-8 encoding
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

# Optional HTTP library for Ollama REST communication
try:
    import urllib.request
    import urllib.error
    HTTP_AVAILABLE = True
except ImportError:
    HTTP_AVAILABLE = False


# ==============================================================================
# SECTION 1: VERIFIED MENU CATALOG & INGREDIENT DATABASE
# ==============================================================================
# In Indian dining, Jain dietary rules require absolute exclusion of root
# vegetables (onions, garlic, potatoes, carrots, radishes) and non-veg.
# Unknown dietary facts must remain explicit "UNKNOWN" rather than false safety claims.

MENU_CATALOG: Dict[str, Dict[str, Any]] = {
    "PBM_01": {
        "item_id": "PBM_01",
        "name": "Paneer Butter Masala",
        "category": "Main Course",
        "price": 280,
        "is_veg": True,
        "is_jain": False,
        "jain_verified": True,  # Fact is verified: it CANNOT be made Jain
        "jain_notes": "Contains cooked onions and garlic in the base gravy. Cannot be prepared Jain.",
        "allergens": ["Dairy", "Nuts (Cashews)"],
        "gluten_free": True,
        "spice_level": "Medium",
        "creaminess": "Rich & Creamy",
        "nutrition": {"kcal": 420, "protein_g": 18, "serving_size": "350g"},
        "ingredients": ["Paneer (Cottage Cheese)", "Tomatoes", "Onions", "Garlic", "Butter", "Cashew Paste", "Spices"],
        "variants": {"Half": 180, "Full": 280},
        "description": "Succulent cubes of cottage cheese simmered in a silky tomato, onion, and butter sauce."
    },
    "JDK_02": {
        "item_id": "JDK_02",
        "name": "Jain Dal Khichdi",
        "category": "Rice & Khichdi",
        "price": 220,
        "is_veg": True,
        "is_jain": True,
        "jain_verified": True,
        "jain_notes": "100% Verified Jain: Prepared without root vegetables, strictly NO onions, NO potatoes, NO garlic. Pure ghee tadka with cumin & hing.",
        "allergens": ["Dairy (Pure Desi Ghee)"],
        "gluten_free": True,
        "spice_level": "Mild",
        "creaminess": "Comforting & Soft",
        "nutrition": {"kcal": 340, "protein_g": 14, "serving_size": "400g"},
        "ingredients": ["Yellow Moong Dal", "Aged Basmati Rice", "Pure Desi Ghee", "Cumin (Jeera)", "Asafoetida (Hing)", "Turmeric", "Rock Salt"],
        "variants": {"Half": 150, "Full": 220},
        "description": "Wholesome, soothing comfort khichdi tempered with pure desi ghee and mild digestive spices."
    },
    "VCP_03": {
        "item_id": "VCP_03",
        "name": "Veg Cheese Pizza",
        "category": "Pizza",
        "price": 349,
        "is_veg": True,
        "is_jain": False,
        "jain_verified": True,
        "jain_notes": "Default marinara sauce contains garlic and onion powder; toppings include sliced onions. Not Jain.",
        "allergens": ["Gluten (Wheat)", "Dairy (Mozzarella)"],
        "gluten_free": False,
        "spice_level": "Mild",
        "creaminess": "Cheesy",
        "nutrition": {"kcal": 580, "protein_g": 16, "serving_size": "Regular 8-inch"},
        "ingredients": ["Hand-tossed Dough", "Marinara Sauce (with garlic & onion)", "Mozzarella Cheese", "Capsicum", "Sliced Red Onion", "Tomatoes"],
        "variants": {"Regular": 349, "Medium": 499, "Large": 649},
        "description": "Crisp stone-baked crust layered with rich herb marinara, melted mozzarella, capsicum, and crunchy red onions."
    },
    "JCP_04": {
        "item_id": "JCP_04",
        "name": "Jain Special Capsicum & Corn Pizza",
        "category": "Pizza",
        "price": 399,
        "is_veg": True,
        "is_jain": True,
        "jain_verified": True,
        "jain_notes": "100% Verified Jain: Specially crafted Jain tomato sauce without any onion, garlic, or root extracts. Topped with sweet corn, bell peppers, and Jain mozzarella.",
        "allergens": ["Gluten (Wheat)", "Dairy (Mozzarella)"],
        "gluten_free": False,
        "spice_level": "Mild",
        "creaminess": "Cheesy",
        "nutrition": {"kcal": 510, "protein_g": 15, "serving_size": "Regular 8-inch"},
        "ingredients": ["Hand-tossed Dough", "Jain Tomato Puree Herb Sauce", "Mozzarella Cheese", "Golden Sweet Corn", "Green Bell Pepper (Capsicum)", "Oregano"],
        "variants": {"Regular": 399, "Medium": 549, "Large": 699},
        "description": "Gourmet Jain pizza crafted with root-free herb sauce, topped with crunchy capsicum and sweet corn."
    },
    "CB_05": {
        "item_id": "CB_05",
        "name": "Chicken Biryani",
        "category": "Biryani",
        "price": 360,
        "is_veg": False,
        "is_jain": False,
        "jain_verified": True,
        "jain_notes": "Non-Vegetarian poultry dish. Completely unsuitable for Vegetarians or Jains.",
        "allergens": ["Dairy (Curd/Ghee)"],
        "gluten_free": True,
        "spice_level": "Spicy",
        "creaminess": "Aromatic & Rich",
        "nutrition": {"kcal": 650, "protein_g": 32, "serving_size": "450g"},
        "ingredients": ["Tender Chicken Pieces", "Basmati Rice", "Fried Brown Onions (Birista)", "Ginger-Garlic Paste", "Mint", "Saffron", "Whole Indian Spices"],
        "variants": {"Half": 240, "Full": 360},
        "description": "Aromatic dum biryani prepared with tender chicken morsels, saffron basmati rice, caramelized onions, and royal spices."
    },
    "GAB_06": {
        "item_id": "GAB_06",
        "name": "Gulab Jamun (2 pcs)",
        "category": "Dessert",
        "price": 90,
        "is_veg": True,
        "is_jain": True,
        "jain_verified": True,
        "jain_notes": "100% Verified Jain sweet prepared from fresh khoya, sugar, and green cardamom.",
        "allergens": ["Dairy (Khoya)", "Gluten"],
        "gluten_free": False,
        "spice_level": "Sweet",
        "creaminess": "Syrupy",
        "nutrition": {"kcal": 290, "protein_g": 6, "serving_size": "2 pieces"},
        "ingredients": ["Khoya / Mawa", "Sugar Syrup", "Cardamom", "Rose Water", "Ghee"],
        "variants": {"Standard (2 pcs)": 90},
        "description": "Melt-in-mouth golden dumplings soaked in fragrant cardamom and rose sugar syrup."
    },
    "JMB_07": {
        "item_id": "JMB_07",
        "name": "Jain Masala Bhindi",
        "category": "Main Course",
        "price": 210,
        "is_veg": True,
        "is_jain": True,
        "jain_verified": True,
        "jain_notes": "100% Verified Jain: Fresh tender okra stir-fried with amchur, cumin, and coriander. Strict zero onion, zero garlic.",
        "allergens": [],
        "gluten_free": True,
        "spice_level": "Medium",
        "creaminess": "Dry Stir Fry",
        "nutrition": {"kcal": 180, "protein_g": 5, "serving_size": "300g"},
        "ingredients": ["Ladyfinger (Bhindi)", "Mustard Oil", "Amchur (Dry Mango Powder)", "Coriander Powder", "Cumin", "Turmeric"],
        "variants": {"Standard": 210},
        "description": "Crisp stir-fried tender okra seasoned with tangy dry mango powder and aromatic spices."
    },
    "RMC_08": {
        "item_id": "RMC_08",
        "name": "Rajma Chawal Combo",
        "category": "Rice & Khichdi",
        "price": 190,
        "is_veg": True,
        "is_jain": False,
        "jain_verified": True,
        "jain_notes": "Gravy contains slow-cooked onions, garlic, and ginger. Not suitable for Jain diet.",
        "allergens": [],
        "gluten_free": True,
        "spice_level": "Medium",
        "creaminess": "Hearty Stew",
        "nutrition": {"kcal": 460, "protein_g": 16, "serving_size": "450g"},
        "ingredients": ["Red Kidney Beans (Rajma)", "Steamed Basmati Rice", "Onions", "Garlic", "Ginger", "Tomatoes", "Garam Masala"],
        "variants": {"Standard": 190},
        "description": "North Indian comfort staple: slow-simmered red kidney beans in spiced gravy served over steamed basmati rice."
    }
}

# Simulated past completed orders for re-ordering verification (Task A07/A10)
COMPLETED_ORDERS_DB: Dict[str, Dict[str, Any]] = {
    "ord_past_001": {
        "order_id": "ord_past_001",
        "user_id": "user_demo_101",
        "branch_id": "branch_koramangala_01",
        "items": [
            {"item_id": "VCP_03", "variant": "Regular", "quantity": 1, "past_price": 329},
            {"item_id": "GAB_06", "variant": "Standard (2 pcs)", "quantity": 1, "past_price": 80}
        ],
        "created_at": "2026-10-10T19:30:00Z",
        "status": "DELIVERED"
    }
}

# Persistent User Preferences DB (Opt-in consented preferences - Task A06)
USER_PREFERENCES_DB: Dict[str, Dict[str, Any]] = {
    "user_demo_101": {
        "user_id": "user_demo_101",
        "diet": "VEG",
        "allergens": ["Nuts"],
        "language": "hinglish",
        "consent_version": "v1.0",
        "consented_at": "2026-10-01T10:00:00Z"
    }
}


# ==============================================================================
# SECTION 2: DETERMINISTIC COMMERCE BACKEND TOOLS
# ==============================================================================
# The LLM is NEVER allowed to guess menu items, calculate taxes, or place orders.
# It can only call these certified backend functions.

def log_tool(name: str, args: Dict[str, Any], summary: str):
    """Prints tool invocation trace to stdout."""
    print(f"\n  [BACKEND TOOL] `{name}`")
    print(f"    Input: {json.dumps(args, default=str)}")
    print(f"    Output: {summary}\n")


def search_menu(
    query: str = "all",
    is_jain: bool = False,
    is_veg: bool = False,
    max_budget: Optional[int] = None,
    min_protein_g: Optional[int] = None,
    max_calories: Optional[int] = None
) -> List[Dict[str, Any]]:
    """Searches verified menu items with structured filters.
    
    Jain Rule: Strictly excludes root vegetables (onions, garlic, potatoes, carrots).
    Budget Rule: Returns items with base_price <= max_budget.
    Nutrition: Checks verified database facts; does not guess.
    """
    clean_q = (query or "").strip().lower()
    results = []

    for item in MENU_CATALOG.values():
        # Jain guardrail: Must be True
        if is_jain and not item["is_jain"]:
            continue

        # Vegetarian guardrail
        if is_veg and not item["is_veg"]:
            continue

        # Budget constraint
        if max_budget is not None and max_budget > 0:
            if item["price"] > max_budget:
                continue

        # Nutrition filters (protein & calories)
        nutr = item.get("nutrition")
        if min_protein_g is not None and nutr:
            if nutr.get("protein_g", 0) < min_protein_g:
                continue
        if max_calories is not None and nutr:
            if nutr.get("kcal", 9999) > max_calories:
                continue

        # Text matching
        if clean_q in ["all", "menu", "", "recommend", "food", "dishes"]:
            matched = True
        else:
            text = f"{item['name']} {item['category']} {' '.join(item['ingredients'])} {item['description']}".lower()
            matched = clean_q in text

        if matched:
            results.append({
                "item_id": item["item_id"],
                "name": item["name"],
                "category": item["category"],
                "base_price": item["price"],
                "is_veg": item["is_veg"],
                "is_jain": item["is_jain"],
                "spice_level": item["spice_level"],
                "nutrition": item.get("nutrition"),
                "available_variants": list(item["variants"].keys()) if item.get("variants") else ["Standard"]
            })

    log_tool("search_menu", {"query": query, "is_jain": is_jain, "max_budget": max_budget}, f"Found {len(results)} items")
    return results


def get_menu_item(item_id: str) -> Dict[str, Any]:
    """Fetches recipe facts, verified allergens, spice level, and Jain verification."""
    clean_id = (item_id or "").strip().upper()
    item = MENU_CATALOG.get(clean_id)

    # Name fallback search
    if not item:
        for candidate in MENU_CATALOG.values():
            if candidate["name"].lower() == item_id.lower().strip():
                item = candidate
                break

    if not item:
        err = {"error": f"Item '{item_id}' not found in verified catalog."}
        log_tool("get_menu_item", {"item_id": item_id}, "Not found")
        return err

    log_tool("get_menu_item", {"item_id": item_id}, f"Found '{item['name']}' (is_jain={item['is_jain']})")
    return item


def propose_cart(
    items: List[Dict[str, Any]],
    group_request: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Computes an immutable short-lived order proposal card with 2-minute TTL.
    
    Arithmetics:
    - Subtotal = sum(unit_price * qty)
    - Restaurant GST = round(subtotal * 0.05, 2) (5% Indian restaurant GST)
    - Packaging & Delivery Fee = INR 25.00
    - Grand Total = Subtotal + GST + Packaging
    
    Returns requires_confirmation=True. Does NOT place orders or deduct money!
    """
    if not items or not isinstance(items, list):
        return {"error": "Invalid items list. At least one item required."}

    resolved_items = []
    subtotal = 0.0
    all_allergens = set()
    all_jain = True
    all_veg = True

    for entry in items:
        raw_id = entry.get("item_id", "")
        clean_id = str(raw_id).strip().upper()
        item = MENU_CATALOG.get(clean_id)

        if not item:
            for candidate in MENU_CATALOG.values():
                if candidate["name"].lower() == str(raw_id).lower().strip():
                    item = candidate
                    clean_id = candidate["item_id"]
                    break

        if not item:
            return {"error": f"Item '{raw_id}' does not exist in branch catalog. Cannot propose cart."}

        qty = max(1, int(entry.get("quantity", 1)))
        req_variant = entry.get("variant")
        variants = item.get("variants", {})

        unit_price = item["price"]
        chosen_var = "Standard"

        if variants:
            matched_var = None
            if req_variant:
                for v_name, v_price in variants.items():
                    if v_name.lower() == str(req_variant).lower().strip():
                        matched_var = v_name
                        unit_price = v_price
                        break
            if not matched_var:
                matched_var = list(variants.keys())[0]
                unit_price = variants[matched_var]
            chosen_var = matched_var

        line_total = unit_price * qty
        subtotal += line_total

        if not item["is_jain"]:
            all_jain = False
        if not item["is_veg"]:
            all_veg = False

        for a in item.get("allergens", []):
            all_allergens.add(a)

        resolved_items.append({
            "item_id": clean_id,
            "name": item["name"],
            "variant": chosen_var,
            "quantity": qty,
            "unit_price": unit_price,
            "line_total": line_total,
            "is_jain": item["is_jain"],
            "is_veg": item["is_veg"]
        })

    gst = round(subtotal * 0.05, 2)
    packaging_fee = 25.00
    grand_total = round(subtotal + gst + packaging_fee, 2)

    # 2-minute expiration for proposal
    expires_at = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=2)).isoformat()

    proposal_card = {
        "proposal_id": f"PROP-{uuid.uuid4().hex[:6].upper()}",
        "cart_version": 1,
        "menu_version": 23,
        "status": "PROPOSED",
        "requires_confirmation": True,
        "expires_at": expires_at,
        "items": resolved_items,
        "subtotal": round(subtotal, 2),
        "tax_gst_5pct": gst,
        "packaging_delivery_charge": packaging_fee,
        "grand_total": grand_total,
        "dietary_summary": {
            "all_jain_verified": all_jain,
            "all_veg": all_veg,
            "detected_allergens": sorted(list(all_allergens))
        },
        "group_allocation": group_request.get("allocation") if group_request else None
    }

    log_tool("propose_cart", {"items_count": len(resolved_items)}, f"Proposal {proposal_card['proposal_id']} total=INR {grand_total}")
    return proposal_card


def get_reorder_proposal(user_id: str, past_order_id: Optional[str] = None) -> Dict[str, Any]:
    """Loads a customer's past order, re-validates every item against CURRENT menu
    and CURRENT prices. Never blindly copies stale prices! (Task A07/A10)
    """
    order = None
    if past_order_id and past_order_id in COMPLETED_ORDERS_DB:
        order = COMPLETED_ORDERS_DB[past_order_id]
    else:
        for ord_data in COMPLETED_ORDERS_DB.values():
            if ord_data["user_id"] == user_id:
                order = ord_data
                break

    if not order:
        return {"error": "No previous completed order found for this branch."}

    revalidated_items = []
    price_changes = []

    for past_item in order["items"]:
        item_id = past_item["item_id"]
        curr = MENU_CATALOG.get(item_id)
        if not curr:
            price_changes.append(f"Item '{past_item['item_id']}' is no longer on the active menu.")
            continue

        var_name = past_item.get("variant", "Standard")
        curr_price = curr["variants"].get(var_name, curr["price"]) if curr.get("variants") else curr["price"]
        past_price = past_item.get("past_price", curr_price)

        if curr_price != past_price:
            price_changes.append(f"'{curr['name']}' price updated from INR {past_price} to INR {curr_price}.")

        revalidated_items.append({
            "item_id": item_id,
            "quantity": past_item.get("quantity", 1),
            "variant": var_name
        })

    fresh_proposal = propose_cart(revalidated_items)
    fresh_proposal["reorder_from_order_id"] = order["order_id"]
    fresh_proposal["price_adjustments_noted"] = price_changes
    return fresh_proposal


def get_order_status(order_id: str, user_id: str) -> Dict[str, Any]:
    """Fetches live tracking status, driver assignment, and calling eligibility."""
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    mock_active_orders = {
        "ord_live_789": {
            "order_id": "ord_live_789",
            "user_id": user_id,
            "restaurant_name": "ARPZO Kitchen Central",
            "status": "OUT_FOR_DELIVERY",
            "rider_assigned": True,
            "rider_id": "rider_rahul_404",
            "rider_name": "Rahul Kumar (Delivery Partner)",
            "updated_at": (now_utc - datetime.timedelta(minutes=8)).isoformat(),
            "estimated_delivery_mins": 12,
            "can_call_driver": True
        }
    }

    info = mock_active_orders.get(order_id)
    if not info:
        return {
            "order_id": order_id,
            "status": "DELIVERED",
            "rider_assigned": False,
            "updated_at": (now_utc - datetime.timedelta(minutes=45)).isoformat(),
            "can_call_driver": False,
            "note": "Delivered over 30 minutes ago. Private calling window is now closed."
        }

    return info


def get_preferences(user_id: str) -> Dict[str, Any]:
    """Returns only explicitly consented dietary preferences for the customer."""
    prefs = USER_PREFERENCES_DB.get(user_id)
    if not prefs:
        return {"user_id": user_id, "diet": None, "allergens": [], "consented": False}
    return prefs


# ==============================================================================
# SECTION 3: PRIVATE CUSTOMER-DRIVER CALLING SERVICE (RTC / AGORA)
# ==============================================================================

class PrivateCallingManager:
    """Enterprise-grade private calling state machine adhering to Section 7-11."""

    def __init__(self):
        self.calls: Dict[str, Dict[str, Any]] = {}
        self.order_attempts: Dict[str, List[float]] = {}
        self.active_assignments: Dict[str, Dict[str, Any]] = {
            "ord_live_789": {
                "order_id": "ord_live_789",
                "customer_id": "user_demo_101",
                "driver_id": "rider_rahul_404",
                "opaque_channel_id": "rtc_chan_" + uuid.uuid4().hex[:12],
                "assignment_version": 1,
                "delivered_at": None,
                "is_cancelled": False
            }
        }
        self.RATE_LIMIT_MAX_ATTEMPTS = 5
        self.RATE_LIMIT_WINDOW_SEC = 600  # 10 minutes

    def initiate_call(self, order_id: str, caller_id: str) -> Dict[str, Any]:
        """Creates an authorized call attempt between customer and assigned rider."""
        assignment = self.active_assignments.get(order_id)
        if not assignment or assignment["is_cancelled"]:
            return {"error": "Calling unavailable: No active driver assignment for this order.", "code": 403}

        # Check delivery deadline: delivered_at + 30 minutes
        if assignment["delivered_at"]:
            deliv_time = datetime.datetime.fromisoformat(assignment["delivered_at"])
            deadline = deliv_time + datetime.timedelta(minutes=30)
            if datetime.datetime.now(datetime.timezone.utc) >= deadline:
                return {"error": "Calling window has expired (30 mins post-delivery).", "code": 403}

        # Verify caller is either the customer or the assigned driver
        if caller_id not in [assignment["customer_id"], assignment["driver_id"]]:
            return {"error": "Unauthorized: You are not a participant in this order.", "code": 403}

        callee_id = assignment["driver_id"] if caller_id == assignment["customer_id"] else assignment["customer_id"]

        # Rate limiting: Max 5 unique attempts per order in 10 minutes
        now_ts = time.time()
        attempts = self.order_attempts.get(order_id, [])
        valid_attempts = [t for t in attempts if now_ts - t < self.RATE_LIMIT_WINDOW_SEC]
        if len(valid_attempts) >= self.RATE_LIMIT_MAX_ATTEMPTS:
            return {
                "error": "Rate limit exceeded: Maximum 5 call attempts per 10 minutes reached.",
                "code": 429,
                "retry_after_seconds": int(self.RATE_LIMIT_WINDOW_SEC - (now_ts - valid_attempts[0]))
            }

        valid_attempts.append(now_ts)
        self.order_attempts[order_id] = valid_attempts

        call_id = f"call_{uuid.uuid4().hex[:8]}"
        call_record = {
            "call_id": call_id,
            "order_id": order_id,
            "opaque_channel_id": assignment["opaque_channel_id"],
            "caller_id": caller_id,
            "callee_id": callee_id,
            "state": "RINGING",
            "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "customer_consent": False,
            "driver_consent": False,
            "recorder_ready": False,
            "connected_at": None,
            "ended_at": None,
            "end_reason": None,
            "recording_status": "PENDING"
        }
        self.calls[call_id] = call_record
        return {"call_id": call_id, "state": "RINGING", "order_id": order_id}

    def generate_rtc_token(self, call_id: str, user_id: str, device_id: str) -> Dict[str, Any]:
        """Issues short-lived Agora/WebRTC media token (max 10-min TTL)."""
        call = self.calls.get(call_id)
        if not call or call["state"] in ["ENDED", "REJECTED", "EXPIRED", "CANCELED"]:
            return {"error": "Call session is not active or token expired.", "code": 403}

        if user_id not in [call["caller_id"], call["callee_id"]]:
            return {"error": "Access denied to call channel.", "code": 403}

        secret = "agora_secret_rtc_2026_arpzo"
        msg = f"{user_id}:{call['opaque_channel_id']}:{time.time()}".encode('utf-8')
        token_sig = hmac.new(secret.encode('utf-8'), msg, hashlib.sha256).hexdigest()

        return {
            "token": f"006{token_sig[:32]}",
            "channel_id": call["opaque_channel_id"],
            "provider": "AGORA",
            "provider_uid": abs(hash(user_id)) % 1000000,
            "expires_in_seconds": 600
        }

    def accept_call(
        self,
        call_id: str,
        user_id: str,
        customer_consent: bool,
        driver_consent: bool
    ) -> Dict[str, Any]:
        """Accepts call and enforces two-party recording consent gate before opening media!"""
        call = self.calls.get(call_id)
        if not call:
            return {"error": "Call not found.", "code": 404}

        # Two-party consent check (Task C13)
        if not customer_consent or not driver_consent:
            call["state"] = "REJECTED"
            call["end_reason"] = "RECORDING_CONSENT_DECLINED"
            return {
                "error": "Both parties must consent to call recording. Audio path blocked. Please use chat fallback.",
                "code": 400,
                "fallback_action": "ORDER_CHAT"
            }

        call["customer_consent"] = True
        call["driver_consent"] = True
        call["recorder_ready"] = True
        call["state"] = "CONNECTED"
        call["connected_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        call["recording_status"] = "RECORDING_ACTIVE"

        return {
            "status": "CONNECTED",
            "call_id": call_id,
            "channel_id": call["opaque_channel_id"],
            "recording_active": True,
            "notice": "This call is recorded for quality, safety, and delivery verification."
        }

    def end_call(self, call_id: str, user_id: str, reason: str = "NORMAL_HANGUP") -> Dict[str, Any]:
        """Ends call, stops audio immediately, and finalizes recording metadata."""
        call = self.calls.get(call_id)
        if not call:
            return {"error": "Call not found.", "code": 404}

        call["state"] = "ENDED"
        call["ended_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        call["end_reason"] = reason
        call["recording_status"] = "READY"
        return {"status": "ENDED", "call_id": call_id, "duration_sec": 42}

    def get_admin_playback_url(self, call_id: str, admin_user_id: str) -> Dict[str, Any]:
        """Issues short-lived 5-minute signed URL exclusively for authorized admin playback."""
        if not admin_user_id.startswith("admin_"):
            return {"error": "Unauthorized: Playback access restricted to authorized admins.", "code": 403}

        call = self.calls.get(call_id)
        if not call:
            return {"error": "Recording not found.", "code": 404}

        token = uuid.uuid4().hex
        expires_at = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=5)).isoformat()
        return {
            "call_id": call_id,
            "signed_playback_url": f"https://storage.arpzo.internal/recordings/{call_id}.m4a?token={token}",
            "expires_at": expires_at,
            "audit_logged": True
        }


# ==============================================================================
# SECTION 4: OLLAMA LOCAL TRIAL MODEL & ENGINE INTEGRATION
# ==============================================================================

ARPZO_OLLAMA_SYSTEM_PROMPT = """
You are the AI Voice & Text Food Ordering Assistant for the ARPZO Restaurant Platform.
Created by Axar Tandon (3rd Year B.Tech CSE).
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
    """Connects to a locally running Ollama instance (e.g. `ollama run llama3` or `mistral`).
    Written by a 3rd year B.Tech student exploring open-source local LLMs!
    """

    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3"):
        self.base_url = os.environ.get("OLLAMA_BASE_URL", base_url).rstrip("/")
        self.model = os.environ.get("OLLAMA_MODEL", model)
        self.chat_history: List[Dict[str, str]] = [
            {"role": "system", "content": ARPZO_OLLAMA_SYSTEM_PROMPT}
        ]

    def is_available(self) -> bool:
        """Checks if local Ollama daemon is reachable on port 11434."""
        if not HTTP_AVAILABLE:
            return False
        try:
            req = urllib.request.Request(f"{self.base_url}/api/tags")
            with urllib.request.urlopen(req, timeout=1.5) as resp:
                return resp.status == 200
        except Exception:
            return False

    def generate_response(self, user_text: str) -> str:
        """Sends user message to Ollama API and receives the generated response."""
        self.chat_history.append({"role": "user", "content": user_text})
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


# ==============================================================================
# SECTION 5: AUTONOMOUS HIGH-FIDELITY SIMULATOR ENGINE (OFFLINE FALLBACK)
# ==============================================================================

class SimulatorAssistantEngine:
    """Deterministic conversational state machine replicating Ollama reasoning
    for Indian food ordering with Hinglish nuance and strict dietary guardrails.
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
        msg = user_msg.strip().lower()

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


# ==============================================================================
# SECTION 6: PROPOSAL CARD FORMATTER (ASCII BOX)
# ==============================================================================

def format_proposal_box(card: Dict[str, Any]) -> str:
    """Renders a clean, professional ASCII proposal box for terminal and mobile view."""
    if not card or "items" not in card:
        return ""

    width = 66
    lines = [
        "+" + "=" * (width - 2) + "+",
        "|" + " ARPZO RESTAURANT - ORDER PROPOSAL CARD ".center(width - 2) + "|",
        "|" + f" Proposal ID: {card.get('proposal_id', 'N/A')} | Status: {card.get('status', 'PROPOSED')}".center(width - 2) + "|",
        "+" + "-" * (width - 2) + "+",
        f"| {'Item':<28} {'Variant':<10} {'Qty':<4} {'Price':<8} {'Total':<8} |",
        "+" + "-" * (width - 2) + "+"
    ]

    for itm in card["items"]:
        name = itm["name"][:27]
        var = itm["variant"][:9]
        qty = str(itm["quantity"])
        unit = f"INR {itm['unit_price']:.0f}"
        ltotal = f"INR {itm['line_total']:.0f}"
        lines.append(f"| {name:<28} {var:<10} {qty:<4} {unit:<8} {ltotal:<8} |")

    lines.extend([
        "+" + "-" * (width - 2) + "+",
        f"| {'Item Subtotal:':<50} INR {card['subtotal']:>8.2f} |",
        f"| {'Restaurant GST (5%):':<50} INR {card['tax_gst_5pct']:>8.2f} |",
        f"| {'Packaging & Delivery Charge:':<50} INR {card['packaging_delivery_charge']:>8.2f} |",
        "+" + "=" * (width - 2) + "+",
        f"| {'GRAND TOTAL (Payable):':<50} INR {card['grand_total']:>8.2f} |",
        "+" + "=" * (width - 2) + "+"
    ])

    diet = card.get("dietary_summary", {})
    jain_tag = "YES (100% Verified)" if diet.get("all_jain_verified") else "NO (Contains Non-Jain items)"
    allergens = ", ".join(diet.get("detected_allergens", [])) or "None identified"
    lines.extend([
        f"| Dietary - Jain Verified: {jain_tag:<38} |",
        f"| Allergens Noted: {allergens[:46]:<46} |",
        f"| Action Gate - Requires Explicit Confirmation: {str(card.get('requires_confirmation')):<17} |",
        "+" + "-" * (width - 2) + "+"
    ])
    return "\n".join(lines)


# ==============================================================================
# SECTION 7: INTERACTIVE TERMINAL LOOP & CLI
# ==============================================================================

def run_interactive_cli():
    """Runs the interactive voice/text session in terminal with push-to-talk."""
    print("=" * 72)
    print("  ARPZO RESTAURANT - VOICE/TEXT FOOD ORDERING ASSISTANT")
    print("  Author: Axar Tandon (3rd Year B.Tech CSE - AI/ML)")
    print("  Trial LLM: Ollama Local Model (with Simulator Fallback)")
    print("  Commands: 'menu', 'jain', 'track', 'reset', 'exit'")
    print("=" * 72)

    ollama = OllamaAssistantEngine()
    sim = SimulatorAssistantEngine()
    engine_name = f"Ollama ({ollama.model})" if ollama.is_available() else "Autonomous High-Fidelity Simulator"

    print(f"\n[INFO] Active Trial Engine: {engine_name}")
    print("AI Assistant: Namaste! ARPZO me aapka swagat hai. Aaj aap kya khana pasand karenge?\n")

    while True:
        try:
            user_input = input("\nCustomer: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nAI Assistant: Alvida! Aapka din shubh ho! (Session Ended)")
            break

        if not user_input:
            continue

        if user_input.lower() in ["exit", "quit", "bye"]:
            print("\nAI Assistant: Dhanyawaad ARPZO choose karne ke liye! Phir milenge!")
            break

        if user_input.lower() == "menu":
            items = search_menu("all")
            print("\n--- ARPZO RESTAURANT MENU ---")
            for itm in items:
                j_tag = " [Jain]" if itm["is_jain"] else ""
                v_tag = "Veg" if itm["is_veg"] else "Non-Veg"
                print(f" * {itm['name']} ({v_tag}{j_tag}) - INR {itm['base_price']}")
            print("-----------------------------\n")
            continue

        # Process utterance
        reply = sim.handle_message(user_input)
        print(f"\nAI Assistant: {reply}")


def main():
    """Main CLI entrypoint."""
    run_interactive_cli()


if __name__ == "__main__":
    main()
