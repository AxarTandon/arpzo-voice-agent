#!/usr/bin/env python3
"""
================================================================================
🚀 ARPZO UNIFIED LAUNCHER & ORCHESTRATOR
================================================================================
Author: Axar Tandon (3rd Year B.Tech CSE - AI/ML)

Usage:
  python run.py --server    Start FastAPI Backend & Web App (http://localhost:8000/app/)
  python run.py --cli       Interactive Terminal Voice/Text Assistant
  python run.py --test      Run Complete Acceptance & Security Suite (63+ tests)
  python run.py --security  Run Dedicated Threat & Security Audit
================================================================================
"""

import sys
import os
import argparse
import subprocess

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

def main():
    parser = argparse.ArgumentParser(description="ARPZO Voice Agent MVP Unified Launcher")
    parser.add_argument("--server", action="store_true", help="Start FastAPI Backend and Web Application")
    parser.add_argument("--cli", action="store_true", help="Run interactive terminal assistant")
    parser.add_argument("--test", action="store_true", help="Run all automated acceptance & security tests")
    parser.add_argument("--security", action="store_true", help="Run security audit suite only")
    args = parser.parse_args()

    # Default to --test if no argument provided
    if not (args.server or args.cli or args.test or args.security):
        print("\nNo argument specified. Running comprehensive test suite by default.")
        print("Use: python run.py --server | --cli | --test | --security\n")
        args.test = True

    if args.security:
        print("\n🛡️ Executing ARPZO Security Audit Suite...")
        cmd = [sys.executable, os.path.join("tests", "test_security.py")]
        res = subprocess.run(cmd)
        sys.exit(res.returncode)

    if args.test:
        print("\n🧪 Executing Full Acceptance Test Suite (A01-A15, C01-C17, N01-N04)...")
        cmd_all = [sys.executable, "test_suite.py"]
        res1 = subprocess.run(cmd_all)
        if res1.returncode != 0:
            sys.exit(res1.returncode)

        print("\n🛡️ Executing Security Audit Suite...")
        cmd_sec = [sys.executable, os.path.join("tests", "test_security.py")]
        res2 = subprocess.run(cmd_sec)
        if res2.returncode != 0:
            sys.exit(res2.returncode)

        print("\n🌐 Executing API Endpoint Tests...")
        cmd_api = [sys.executable, os.path.join("tests", "test_api.py")]
        res3 = subprocess.run(cmd_api)
        sys.exit(res3.returncode)

    if args.cli:
        print("\n🎙️ Starting Interactive Terminal Session...")
        cmd_cli = [sys.executable, "arpzo_assistant.py"]
        subprocess.run(cmd_cli)
        return

    if args.server:
        print("\n🌐 Starting ARPZO Backend & Web Application...")
        cmd_server = [sys.executable, os.path.join("backend", "main.py")]
        subprocess.run(cmd_server)
        return

if __name__ == "__main__":
    main()
