#!/usr/bin/env python3
"""
REST & WebSocket API verification for api_server.py
"""
import sys
from fastapi.testclient import TestClient
from api_server import app

client = TestClient(app)

def test_api():
    print("Testing REST Endpoints...")
    
    # 1. Create Session
    s_resp = client.post("/v1/assistant/sessions", json={"branch_id": "branch_koramangala_01", "language": "hinglish"})
    assert s_resp.status_code == 201, f"Expected 201, got {s_resp.status_code}"
    session_id = s_resp.json()["session_id"]
    print(f"  [PASS] POST /v1/assistant/sessions -> session_id: {session_id}")

    # 2. Process Turn
    t_resp = client.post("/v1/assistant/turns", json={"session_id": session_id, "text": "Jain Dal Khichdi add kar do"})
    assert t_resp.status_code == 200, f"Expected 200, got {t_resp.status_code}"
    print(f"  [PASS] POST /v1/assistant/turns -> {t_resp.json()['assistant_text'][:60]}...")

    # 3. Create Proposal
    p_resp = client.post("/v1/cart/proposals", json={
        "session_id": session_id,
        "items": [{"item_id": "JDK_02", "quantity": 1, "variant": "Full"}]
    })
    assert p_resp.status_code == 200, f"Expected 200, got {p_resp.status_code}"
    proposal_id = p_resp.json()["proposal_id"]
    print(f"  [PASS] POST /v1/cart/proposals -> proposal_id: {proposal_id}")

    # 4. Confirm Proposal with Idempotency Key
    c_resp = client.post("/v1/cart/confirm", json={"proposal_id": proposal_id, "expected_cart_version": 1}, headers={"Idempotency-Key": "key_demo_test_001"})
    assert c_resp.status_code == 200, f"Expected 200, got {c_resp.status_code}"
    order_id = c_resp.json()["order_id"]
    print(f"  [PASS] POST /v1/cart/confirm -> order_id: {order_id}")

    # 5. Idempotent repeat
    c_repeat = client.post("/v1/cart/confirm", json={"proposal_id": proposal_id, "expected_cart_version": 1}, headers={"Idempotency-Key": "key_demo_test_001"})
    assert c_repeat.status_code == 200
    assert c_repeat.json()["order_id"] == order_id, "Idempotent repeat returned different order_id"
    print(f"  [PASS] POST /v1/cart/confirm (Idempotent Repeat) -> returns identical order_id")

    # 6. Read Preferences
    pref_resp = client.get("/v1/me/preferences?user_id=user_demo_101")
    assert pref_resp.status_code == 200
    print(f"  [PASS] GET /v1/me/preferences -> {pref_resp.json()['diet']}")

    # 7. Calling initiate
    call_resp = client.post("/v1/calls", json={"order_id": "ord_live_789", "caller_id": "user_demo_101"})
    assert call_resp.status_code == 200
    call_id = call_resp.json()["call_id"]
    print(f"  [PASS] POST /v1/calls -> call_id: {call_id}")

    # 8. Token issue
    tok_resp = client.post("/v1/call/token", json={"order_id": "ord_live_789", "call_id": call_id, "user_id": "user_demo_101"})
    assert tok_resp.status_code == 200
    print(f"  [PASS] POST /v1/call/token -> provider: {tok_resp.json()['provider']}")

    # 9. Accept with two-party consent
    acc_resp = client.post(f"/v1/calls/{call_id}/accept", json={"user_id": "rider_rahul_404", "customer_consent": True, "driver_consent": True})
    assert acc_resp.status_code == 200
    print(f"  [PASS] POST /v1/calls/{call_id}/accept -> recording_active: {acc_resp.json()['recording_active']}")

    # 10. End Call
    end_resp = client.post(f"/v1/calls/{call_id}/end", json={"user_id": "user_demo_101", "reason": "DELIVERY_COMPLETED"})
    assert end_resp.status_code == 200
    print(f"  [PASS] POST /v1/calls/{call_id}/end -> status: {end_resp.json()['status']}")

    print("\nALL FASTAPI REST ENDPOINTS PASSED!\nVERDICT: PASS")

if __name__ == "__main__":
    test_api()
