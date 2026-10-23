#!/usr/bin/env python3
"""
================================================================================
📞 ARPZO PRIVATE CALLING ACCEPTANCE TESTS (C01 - C17)
================================================================================
Author: Axar Tandon (3rd Year B.Tech CSE - AI/ML)
"""

import sys
import os
import unittest
import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.calling import PrivateCallingManager


class TestCallingCapabilities(unittest.TestCase):

    def setUp(self):
        self.mgr = PrivateCallingManager()

    def test_c01_unauthorized_access(self):
        """C01: Strangers denied call access without data leakage."""
        res = self.mgr.initiate_call("ord_live_789", "stranger_hacker")
        self.assertEqual(res.get("code"), 403)

    def test_c02_delivery_deadline(self):
        """C02: Calling denied at or after delivered_at + 30 minutes."""
        ord_id = "ord_delivered_past_30m"
        self.mgr.active_assignments[ord_id] = {
            "order_id": ord_id,
            "customer_id": "user_demo_101",
            "driver_id": "rider_rahul_404",
            "opaque_channel_id": "rtc_chan_past",
            "assignment_version": 1,
            "delivered_at": (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=35)).isoformat(),
            "is_cancelled": False
        }
        res = self.mgr.initiate_call(ord_id, "user_demo_101")
        self.assertEqual(res.get("code"), 403)

    def test_c03_cancellation_revocation(self):
        """C03: Cancelled order revokes call access immediately."""
        ord_id = "ord_cancelled_test"
        self.mgr.active_assignments[ord_id] = {
            "order_id": ord_id,
            "customer_id": "user_demo_101",
            "driver_id": "rider_rahul_404",
            "opaque_channel_id": "rtc_chan_canc",
            "assignment_version": 1,
            "delivered_at": None,
            "is_cancelled": True
        }
        res = self.mgr.initiate_call(ord_id, "user_demo_101")
        self.assertEqual(res.get("code"), 403)

    def test_c04_to_c06_call_initiation_and_tokens(self):
        """C04-C06: Authorized call lifecycle, token generation, opaque channel."""
        init = self.mgr.initiate_call("ord_live_789", "user_demo_101")
        self.assertEqual(init["state"], "RINGING")
        call_id = init["call_id"]

        tok = self.mgr.generate_rtc_token(call_id, "user_demo_101", "dev_1")
        self.assertIn("token", tok)
        self.assertEqual(tok["provider"], "AGORA")
        self.assertTrue(tok["channel_id"].startswith("rtc_chan_"))

    def test_c10_end_call_revocation(self):
        """C10: Ended call cannot issue new tokens."""
        init = self.mgr.initiate_call("ord_live_789", "user_demo_101")
        call_id = init["call_id"]
        self.mgr.end_call(call_id, "user_demo_101")
        tok = self.mgr.generate_rtc_token(call_id, "user_demo_101", "dev_1")
        self.assertEqual(tok.get("code"), 403)

    def test_c11_rate_limit(self):
        """C11: 5 calls in 10 minutes allowed; 6th is blocked."""
        ord_id = "ord_rl_test_c11"
        self.mgr.active_assignments[ord_id] = {
            "order_id": ord_id,
            "customer_id": "user_demo_101",
            "driver_id": "rider_rahul_404",
            "opaque_channel_id": "rtc_chan_rl",
            "assignment_version": 1,
            "delivered_at": None,
            "is_cancelled": False
        }
        for _ in range(5):
            res = self.mgr.initiate_call(ord_id, "user_demo_101")
            self.assertIn("call_id", res)
        res_6 = self.mgr.initiate_call(ord_id, "user_demo_101")
        self.assertEqual(res_6.get("code"), 429)

    def test_c13_two_party_consent(self):
        """C13: Media blocked if either party declines consent."""
        init = self.mgr.initiate_call("ord_live_789", "user_demo_101")
        call_id = init["call_id"]
        declined = self.mgr.accept_call(call_id, "rider_rahul_404", customer_consent=True, driver_consent=False)
        self.assertEqual(declined.get("code"), 400)


if __name__ == "__main__":
    unittest.main()
