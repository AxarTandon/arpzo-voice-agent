#!/usr/bin/env python3
"""
================================================================================
🌐 ARPZO API ENDPOINT TESTS
================================================================================
Author: Axar Tandon (3rd Year B.Tech CSE - AI/ML)
"""

import sys
import os
import unittest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.api import app


class TestApiEndpoints(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)

    def test_assistant_lifecycle(self):
        """Tests session creation, turn processing, proposal generation, and confirmation."""
        # 1. Create Session
        s_resp = self.client.post("/v1/assistant/sessions", json={"branch_id": "branch_koramangala_01", "language": "hinglish"})
        self.assertEqual(s_resp.status_code, 201)
        session_id = s_resp.json()["session_id"]

        # 2. Process Turn
        t_resp = self.client.post("/v1/assistant/turns", json={"session_id": session_id, "text": "Jain Dal Khichdi Full add kar do"})
        self.assertEqual(t_resp.status_code, 200)

        # 3. Create Proposal
        p_resp = self.client.post("/v1/cart/proposals", json={
            "session_id": session_id,
            "items": [{"item_id": "JDK_02", "quantity": 1, "variant": "Full"}]
        })
        self.assertEqual(p_resp.status_code, 200)
        proposal_id = p_resp.json()["proposal_id"]

        # 4. Confirm Proposal with Idempotency Key
        c_resp = self.client.post("/v1/cart/confirm", json={"proposal_id": proposal_id, "expected_cart_version": 1}, headers={"Idempotency-Key": "key_unit_test_101"})
        self.assertEqual(c_resp.status_code, 200)
        order_id = c_resp.json()["order_id"]

        # 5. Idempotent Repeat
        c_repeat = self.client.post("/v1/cart/confirm", json={"proposal_id": proposal_id, "expected_cart_version": 1}, headers={"Idempotency-Key": "key_unit_test_101"})
        self.assertEqual(c_repeat.json()["order_id"], order_id)

    def test_calling_endpoints(self):
        """Tests call initiation, token issuance, acceptance, and termination."""
        # 1. Initiate call
        call_resp = self.client.post("/v1/calls", json={"order_id": "ord_live_789", "caller_id": "user_demo_101"})
        self.assertEqual(call_resp.status_code, 200)
        call_id = call_resp.json()["call_id"]

        # 2. Issue Token
        tok_resp = self.client.post("/v1/call/token", json={"order_id": "ord_live_789", "call_id": call_id, "user_id": "user_demo_101"})
        self.assertEqual(tok_resp.status_code, 200)

        # 3. Accept Call
        acc_resp = self.client.post(f"/v1/calls/{call_id}/accept", json={"user_id": "rider_rahul_404", "customer_consent": True, "driver_consent": True})
        self.assertEqual(acc_resp.status_code, 200)

        # 4. End Call
        end_resp = self.client.post(f"/v1/calls/{call_id}/end", json={"user_id": "user_demo_101", "reason": "NORMAL_HANGUP"})
        self.assertEqual(end_resp.status_code, 200)


if __name__ == "__main__":
    unittest.main()
