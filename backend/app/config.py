"""
================================================================================
⚙️ ARPZO SYSTEM CONFIGURATION
================================================================================
Author: Axar Tandon (3rd Year B.Tech CSE - AI/ML)
"""

import os

# Server
HOST = os.environ.get("ARPZO_HOST", "0.0.0.0")
PORT = int(os.environ.get("ARPZO_PORT", 8000))

# Ollama LLM Settings
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3")

# Private Calling & RTC Settings
AGORA_APP_ID = os.environ.get("AGORA_APP_ID", "agora_arpzo_demo_app_id")
AGORA_APP_CERTIFICATE = os.environ.get("AGORA_APP_CERTIFICATE", "agora_secret_rtc_2026_arpzo")
CALL_TOKEN_TTL_SECONDS = 600  # 10 minutes max per token
POST_DELIVERY_EXPIRY_MINUTES = 30  # Delivery + 30 mins hard cutoff
CALL_RATE_LIMIT_MAX = 5  # Max 5 unique calls per order
CALL_RATE_LIMIT_WINDOW_SEC = 600  # 10 minutes rolling window

# Pricing & Taxes
RESTAURANT_GST_PERCENT = 0.05  # 5% Indian Restaurant GST
FLAT_PACKAGING_FEE = 25.00  # INR 25.00
PROPOSAL_TTL_MINUTES = 2  # Short-lived proposals prevent stale prices
