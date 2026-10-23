"""
================================================================================
🍽️ ARPZO VERIFIED MENU & NUTRITION CATALOG
================================================================================
Author: Axar Tandon (3rd Year B.Tech CSE - AI/ML)
"""

from typing import Dict, Any

MENU_CATALOG: Dict[str, Dict[str, Any]] = {
    "PBM_01": {
        "item_id": "PBM_01",
        "name": "Paneer Butter Masala",
        "category": "Main Course",
        "price": 280,
        "is_veg": True,
        "is_jain": False,
        "jain_verified": True,
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
