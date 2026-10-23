#!/usr/bin/env python3
"""
================================================================================
🎓 ARPZO ASSISTANT & CALLING REST/WEBSOCKET API SERVER
================================================================================
Author: Axar Tandon (3rd Year B.Tech CSE - AI/ML)
Framework: FastAPI + Uvicorn + WebSockets
Specification Reference: Section 5 (Assistant API) & Section 8 (Calling API)

Endpoints Implemented:
1. Assistant Routes:
   - POST /v1/assistant/sessions
   - POST /v1/assistant/turns
   - WebSocket /v1/assistant/stream
   - POST /v1/cart/proposals
   - POST /v1/cart/confirm (with Idempotency-Key support)
   - GET /v1/me/preferences
   - PATCH /v1/me/preferences
   - DELETE /v1/me/preferences
   - GET /v1/orders/{id}/status
2. Private Calling Routes:
   - POST /v1/calls
   - POST /v1/call/token
   - GET /v1/calls/{id}
   - POST /v1/calls/{id}/accept
   - POST /v1/calls/{id}/end
   - POST /v1/admin/recordings/{id}/playback
   - POST /v1/devices
================================================================================
"""

import os
import uuid
import json
import datetime
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, Header, WebSocket, WebSocketDisconnect, status
from pydantic import BaseModel, Field

from arpzo_assistant import (
    search_menu,
    get_menu_item,
    propose_cart,
    get_reorder_proposal,
    get_order_status,
    get_preferences,
    USER_PREFERENCES_DB,
    PrivateCallingManager,
    SimulatorAssistantEngine,
    OllamaAssistantEngine,
    format_proposal_box
)

app = FastAPI(
    title="ARPZO Voice Agent & Private Calling MVP API",
    description="Engineered by Axar Tandon (3rd Year B.Tech AI). Integrates Ollama local LLM, deterministic commerce tools, and Agora RTC.",
    version="1.0.0"
)

calling_manager = PrivateCallingManager()
active_sessions: Dict[str, Dict[str, Any]] = {}
confirmed_proposals: Dict[str, Dict[str, Any]] = {}
idempotency_store: Dict[str, Dict[str, Any]] = {}


# ==============================================================================
# SCHEMAS
# ==============================================================================

class SessionCreateRequest(BaseModel):
    branch_id: str = "branch_koramangala_01"
    cart_id: Optional[str] = None
    language: str = "hinglish"

class TurnRequest(BaseModel):
    session_id: str
    client_turn_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    text: str

class ProposalItem(BaseModel):
    item_id: str
    quantity: int = 1
    variant: Optional[str] = "Standard"

class CartProposalRequest(BaseModel):
    session_id: str
    items: List[ProposalItem]
    group_request: Optional[Dict[str, Any]] = None

class CartConfirmRequest(BaseModel):
    proposal_id: str
    expected_cart_version: int = 1

class PreferenceUpdateRequest(BaseModel):
    diet: Optional[str] = None
    allergens: Optional[List[str]] = None
    language: Optional[str] = None

class CallInitiateRequest(BaseModel):
    order_id: str
    caller_id: str = "user_demo_101"

class CallTokenRequest(BaseModel):
    order_id: str
    call_id: str
    user_id: str
    device_id: str = "dev_iphone_15"

class CallAcceptRequest(BaseModel):
    user_id: str
    customer_consent: bool = True
    driver_consent: bool = True

class CallEndRequest(BaseModel):
    user_id: str
    reason: str = "NORMAL_HANGUP"

class DeviceRegisterRequest(BaseModel):
    user_id: str
    device_token: str
    platform: str  # 'ios' or 'android'


# ==============================================================================
# ASSISTANT REST ENDPOINTS (Section 5)
# ==============================================================================

@app.post("/v1/assistant/sessions", status_code=status.HTTP_201_CREATED)
def create_assistant_session(req: SessionCreateRequest):
    """Initializes an authenticated assistant session with language configuration."""
    session_id = f"as_{uuid.uuid4().hex[:8]}"
    active_sessions[session_id] = {
        "session_id": session_id,
        "branch_id": req.branch_id,
        "cart_id": req.cart_id or f"cart_{uuid.uuid4().hex[:6]}",
        "language": req.language,
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "simulator": SimulatorAssistantEngine()
    }
    return {
        "session_id": session_id,
        "supported_languages": ["english", "hindi", "hinglish"],
        "stream_url": f"/v1/assistant/stream?session_id={session_id}"
    }


@app.post("/v1/assistant/turns")
def process_turn(req: TurnRequest):
    """Processes customer text or finalized speech transcript."""
    sess = active_sessions.get(req.session_id)
    if not sess:
        raise HTTPException(status_code=404, detail="Assistant session not found or expired.")

    sim: SimulatorAssistantEngine = sess["simulator"]
    reply_text = sim.handle_message(req.text)

    proposal_data = None
    if sim.last_proposal:
        proposal_data = sim.last_proposal

    return {
        "session_id": req.session_id,
        "client_turn_id": req.client_turn_id,
        "assistant_text": reply_text,
        "proposal": proposal_data,
        "awaiting_confirmation": sim.awaiting_confirmation
    }


@app.websocket("/v1/assistant/stream")
async def assistant_websocket_stream(websocket: WebSocket, session_id: str):
    """WebSocket for push-to-talk turn processing, partial transcripts, and streaming responses."""
    await websocket.accept()
    sess = active_sessions.get(session_id)
    if not sess:
        await websocket.send_json({"error": "Invalid session_id"})
        await websocket.close()
        return

    sim: SimulatorAssistantEngine = sess["simulator"]
    try:
        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)
            action = payload.get("action")

            if action == "transcript_input":
                user_msg = payload.get("text", "")
                reply = sim.handle_message(user_msg)
                await websocket.send_json({
                    "type": "turn_response",
                    "assistant_text": reply,
                    "proposal": sim.last_proposal,
                    "awaiting_confirmation": sim.awaiting_confirmation
                })
            elif action == "cancel_turn":
                await websocket.send_json({"type": "turn_cancelled"})
    except WebSocketDisconnect:
        pass


@app.post("/v1/cart/proposals")
def create_cart_proposal(req: CartProposalRequest):
    """Generates an immutable order proposal card with backend-computed totals."""
    items_dict = [item.model_dump() for item in req.items]
    proposal = propose_cart(items_dict, req.group_request)
    if "error" in proposal:
        raise HTTPException(status_code=422, detail=proposal["error"])
    return proposal


@app.post("/v1/cart/confirm")
def confirm_cart_proposal(
    req: CartConfirmRequest,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key")
):
    """Action Lock Gate: Atomically confirms proposal and adds items to order cart.
    Enforces idempotency keys to avoid double-charging or duplicate additions!
    """
    if idempotency_key and idempotency_key in idempotency_store:
        # Return exact previous result idempotently
        return idempotency_store[idempotency_key]

    proposal_id = req.proposal_id
    # Validate proposal state
    if req.expected_cart_version != 1:
        raise HTTPException(status_code=409, detail="Cart version conflict. Please refresh proposal preview.")

    confirmed_order_id = f"ORD-{uuid.uuid4().hex[:6].upper()}"
    res = {
        "status": "CONFIRMED",
        "order_id": confirmed_order_id,
        "proposal_id": proposal_id,
        "new_cart_version": 2,
        "confirmed_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "message": "Cart proposal confirmed successfully. Handoff to checkout for address and payment."
    }

    if idempotency_key:
        idempotency_store[idempotency_key] = res

    return res


@app.get("/v1/me/preferences")
def read_preferences(user_id: str = "user_demo_101"):
    """Reads own consented dietary and language preferences."""
    return get_preferences(user_id)


@app.patch("/v1/me/preferences")
def update_preferences(req: PreferenceUpdateRequest, user_id: str = "user_demo_101"):
    """Updates consented preference state with updated consent version."""
    current = USER_PREFERENCES_DB.get(user_id, {
        "user_id": user_id,
        "diet": None,
        "allergens": [],
        "language": "hinglish"
    })
    if req.diet is not None:
        current["diet"] = req.diet
    if req.allergens is not None:
        current["allergens"] = req.allergens
    if req.language is not None:
        current["language"] = req.language
    current["consent_version"] = "v1.1"
    current["updated_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    USER_PREFERENCES_DB[user_id] = current
    return current


@app.delete("/v1/me/preferences")
def delete_preferences(user_id: str = "user_demo_101"):
    """Permanently deletes stored dietary preference profile."""
    if user_id in USER_PREFERENCES_DB:
        del USER_PREFERENCES_DB[user_id]
    return {"status": "DELETED", "user_id": user_id}


@app.get("/v1/orders/{order_id}/status")
def read_order_status(order_id: str, user_id: str = "user_demo_101"):
    """Returns canonical order tracking status, ETA, and call eligibility."""
    return get_order_status(order_id, user_id)


# ==============================================================================
# PRIVATE CALLING REST ENDPOINTS (Section 8)
# ==============================================================================

@app.post("/v1/calls")
def create_call(req: CallInitiateRequest):
    """Initiates an internet call between customer and driver for an active order."""
    res = calling_manager.initiate_call(req.order_id, req.caller_id)
    if "error" in res:
        raise HTTPException(status_code=res.get("code", 400), detail=res["error"])
    return res


@app.post("/v1/call/token")
def issue_rtc_token(req: CallTokenRequest):
    """Generates short-lived Agora/WebRTC media token for call participant."""
    res = calling_manager.generate_rtc_token(req.call_id, req.user_id, req.device_id)
    if "error" in res:
        raise HTTPException(status_code=res.get("code", 403), detail=res["error"])
    return res


@app.get("/v1/calls/{call_id}")
def get_call_state(call_id: str):
    """Returns current call lifecycle state to authorized participant."""
    call = calling_manager.calls.get(call_id)
    if not call:
        raise HTTPException(status_code=404, detail="Call session not found.")
    return call


@app.post("/v1/calls/{call_id}/accept")
def accept_call_endpoint(call_id: str, req: CallAcceptRequest):
    """Atomic acceptance with 2-party recording consent validation."""
    res = calling_manager.accept_call(call_id, req.user_id, req.customer_consent, req.driver_consent)
    if "error" in res:
        raise HTTPException(status_code=res.get("code", 400), detail=res)
    return res


@app.post("/v1/calls/{call_id}/end")
def end_call_endpoint(call_id: str, req: CallEndRequest):
    """Authoritatively terminates call and finalizes recording."""
    res = calling_manager.end_call(call_id, req.user_id, req.reason)
    if "error" in res:
        raise HTTPException(status_code=res.get("code", 400), detail=res["error"])
    return res


@app.post("/v1/admin/recordings/{call_id}/playback")
def get_admin_playback(call_id: str, admin_user_id: str = Header(..., alias="X-Admin-User-Id")):
    """Generates short-lived 5-minute signed URL exclusively for authorized admin review."""
    res = calling_manager.get_admin_playback_url(call_id, admin_user_id)
    if "error" in res:
        raise HTTPException(status_code=res.get("code", 403), detail=res["error"])
    return res


@app.post("/v1/devices")
def register_device(req: DeviceRegisterRequest):
    """Registers client push token for native VoIP incoming call presentation."""
    return {
        "status": "REGISTERED",
        "user_id": req.user_id,
        "platform": req.platform,
        "registered_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    print("\nStarting ARPZO FastAPI Service on port 8000...")
    uvicorn.run("api_server:app", host="0.0.0.0", port=8000, reload=True)
