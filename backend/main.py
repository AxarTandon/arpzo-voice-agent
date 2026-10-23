#!/usr/bin/env python3
"""
================================================================================
🚀 ARPZO BACKEND SERVER ENTRYPOINT
================================================================================
Author: Axar Tandon (3rd Year B.Tech CSE - AI/ML)
Launch: python backend/main.py
"""

import sys
import os

# Add parent directory to path so imports work smoothly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import uvicorn
from backend.app.config import HOST, PORT
from backend.app.api import app

if __name__ == "__main__":
    print(f"\n========================================================")
    print(f"  STARTING ARPZO REST & WEBSOCKET BACKEND SERVICE       ")
    print(f"  Author: Axar Tandon (3rd Year B.Tech CSE - AI/ML)      ")
    print(f"  Host: http://{HOST}:{PORT}                             ")
    print(f"  Swagger Docs: http://{HOST}:{PORT}/docs                ")
    print(f"  Frontend Web App: http://{HOST}:{PORT}/app/            ")
    print(f"========================================================\n")
    uvicorn.run("backend.app.api:app", host=HOST, port=PORT, reload=True)
