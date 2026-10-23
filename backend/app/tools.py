"""
================================================================================
🛠️ ARPZO DETERMINISTIC COMMERCE BACKEND TOOLS
================================================================================
Author: Axar Tandon (3rd Year B.Tech CSE - AI/ML)
Specification Reference: Section 4 (Tool contracts), Section 6 (Menu facts)
"""

import json
import uuid
import datetime
from typing import Dict, Any, List, Optional

from .catalog import MENU_CATALOG, COMPLETED_ORDERS_DB, USER_PREFERENCES_DB
from .config import RESTAURANT_GST_PERCENT, FLAT_PACKAGING_FEE, PROPOSAL_TTL_MINUTES


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
    
    Jain Rule: Strictly excludes root vegetables (onions, garlic, potatoes, carrots, radishes).
    Budget Rule: Returns items with base_price <= max_budget.
    Nutrition: Checks verified database facts; does not guess.
    """
    clean_q = (query or "").strip().lower()
    results = []

    for item in MENU_CATALOG.values():
        if is_jain and not item["is_jain"]:
            continue
        if is_veg and not item["is_veg"]:
            continue
        if max_budget is not None and max_budget > 0:
            if item["price"] > max_budget:
                continue

        nutr = item.get("nutrition")
        if min_protein_g is not None and nutr:
            if nutr.get("protein_g", 0) < min_protein_g:
                continue
        if max_calories is not None and nutr:
            if nutr.get("kcal", 9999) > max_calories:
                continue

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
    - Restaurant GST = round(subtotal * RESTAURANT_GST_PERCENT, 2)
    - Packaging & Delivery Fee = FLAT_PACKAGING_FEE
    - Grand Total = Subtotal + GST + Packaging
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

    gst = round(subtotal * RESTAURANT_GST_PERCENT, 2)
    packaging_fee = FLAT_PACKAGING_FEE
    grand_total = round(subtotal + gst + packaging_fee, 2)

    expires_at = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=PROPOSAL_TTL_MINUTES)).isoformat()

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
