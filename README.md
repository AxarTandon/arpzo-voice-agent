# 🎓 ARPZO AI Voice Agent & Private Driver Calling MVP

> **A production-grade, conversational food ordering engine and private WebRTC/Agora calling service built for the ARPZO Restaurant Platform, featuring local Ollama open-weight LLMs, strict Jain dietary guardrails, deterministic commerce tools, and privacy-preserving human calling.**

---

### 👨‍💻 Developer & Project Context
- **Developer**: Axar Tandon (`AxarTandon`)
- **Role/Background**: 3rd Year B.Tech in Computer Science Engineering (AI & Machine Learning)
- **Project**: ARPZO Restaurant Platform Voice Agent MVP (Specification v1.0, 16 October 2026)
- **Target Integration**: [Karan7s7n/resto](https://github.com/Karan7s7n/resto) (Node.js/Express + MongoDB + Flutter restaurant ecosystem)
- **Trial Model**: **Ollama Local Model** (`llama3`, `mistral`, `qwen2.5`) with Autonomous High-Fidelity Simulator fallback
- **Calling Provider**: Managed RTC (Agora / WebRTC SDK) with server tokens and dual-party consent recording gate

---

## 📋 Table of Contents
1. [Executive Summary & Motivation](#executive-summary--motivation)
2. [Audit & Gap Analysis of Karan7s7n/resto](#audit--gap-analysis-of-karan7s7nresto)
3. [System Architecture](#system-architecture)
4. [Core Features & Invariants](#core-features--invariants)
   - [Trial Model (Ollama Local LLM Integration)](#1-trial-model-ollama-local-llm-integration)
   - [Strict Jain & Dietary Invariants](#2-strict-jain--dietary-invariants)
   - [Deterministic Backend Tools & Zero Hallucination](#3-deterministic-backend-tools--zero-hallucination)
   - [Cart Proposal & Action-Lock Confirmation Gate](#4-cart-proposal--action-lock-confirmation-gate)
   - [Private Calling & Privacy Guardrails (Agora RTC)](#5-private-calling--privacy-guardrails-agora-rtc)
5. [Resto Integration Bridge](#resto-integration-bridge)
6. [API Specification (REST & WebSockets)](#api-specification-rest--websockets)
7. [Visual Proposal Card Interface](#visual-proposal-card-interface)
8. [Getting Started & Quickstart](#getting-started--quickstart)
9. [Automated Verification & Acceptance Tests (A01-A15, C01-C17)](#automated-verification--acceptance-tests)
10. [Roadmap & Engineering Notes](#roadmap--engineering-notes)

---

## 🌟 Executive Summary & Motivation

As a 3rd-year B.Tech CSE (AI/ML) student, I was tasked with analyzing the ARPZO Voice Agent specification and evaluating whether the existing repository at **[Karan7s7n/resto](https://github.com/Karan7s7n/resto)** is ready for an AI voice assistant.

My professors and the ARPZO engineering document emphasize three core engineering principles:
1. **Never Let an LLM Do Mental Math or Invent Facts**: Models hallucinate prices, discounts, and recipes. An enterprise assistant must rely on deterministic backend tools for menu catalog lookups, 5% GST calculation, and packaging fees.
2. **Cultural & Dietary Respect (Strict Jain Rules)**: In Indian food platforms, Jain dietary compliance is a safety-critical requirement. It strictly forbids all root vegetables (potatoes, onions, garlic, carrots, radishes). If a customer asks for a non-Jain dish like *Paneer Butter Masala* in Jain mode, the AI must politely explain *why* and propose verified alternatives.
3. **Privacy First (No Real Phone Numbers)**: Customers and delivery riders should never see each other's real phone numbers. Calls occur over internet RTC, strictly bound to the active order, expiring 30 minutes after delivery, with mandatory two-party recording consent.

---

## 🔍 Audit & Gap Analysis of Karan7s7n/resto

I cloned and inspected the entire **[Karan7s7n/resto](https://github.com/Karan7s7n/resto)** repository. Here is the formal engineering audit:

| System Layer | Current Status in `resto` | Required for ARPZO Voice Agent MVP | Readiness Assessment |
|---|---|---|---|
| **Base Commerce** | Node.js / Express backend with MongoDB schemas (`MenuItem`, `Order`, `Cart`, `Branch`, `Restaurant`, `User`). | Base commerce entities to anchor voice sessions, orders, and branch menus. | ✅ **READY**: Excellent starting point for auth, branches, and orders. |
| **Menu Facts & Nutrition** | Basic `isVegetarian`, `isVegan`, and `isJain` boolean flags on `MenuItem`. | Verified recipe data: root vegetable exclusion notes, spice levels, creaminess, verified allergens, protein (g), and calories (kcal). | ⚠️ **PARTIAL**: Needs enriched recipe metadata (supplied by `resto_bridge.py`). |
| **LLM Orchestrator** | Not implemented. | Local Ollama engine (`llama3`/`mistral`) or Gemini with multilingual prompts (English, Hindi, Hinglish). | ❌ **MISSING**: Implemented in `arpzo_assistant.py`. |
| **Assistant API Routes** | No assistant routes in `routes/index.js`. | `POST /v1/assistant/sessions`, `POST /v1/assistant/turns`, `WSS /v1/assistant/stream`. | ❌ **MISSING**: Implemented in `api_server.py`. |
| **Cart Proposal State Machine** | Direct cart item addition in `cart.service.js`. | Short-lived 2-minute proposal cards with versioning, 5% GST, and explicit human confirmation lock. | ❌ **MISSING**: Implemented in `arpzo_assistant.py` & `api_server.py`. |
| **Group & Re-Order Logic** | Not implemented. | Single-branch group allocation under budget; past order price re-validation. | ❌ **MISSING**: Implemented in `propose_cart` and `get_reorder_proposal`. |
| **User Preference Memory** | Basic user profile in `user.model.js`. | Explicit opt-in consented preferences with 1-order override and deletion. | ❌ **MISSING**: Implemented via `/v1/me/preferences`. |
| **Private Calling Service** | Not implemented. | Internet audio calls, Agora RTC token server, delivery + 30m cutoff, 2-party consent gate, no PSTN phone numbers. | ❌ **MISSING**: Implemented in `PrivateCallingManager` & `api_server.py`. |

**Verdict**: While `resto` contains the underlying commerce models (cart, order, menu), **it is NOT ready for the Voice Agent and Private Calling modules out of the box**. This repository provides the complete, production-ready implementation and the bridge to connect them!

---

## 🏗️ System Architecture

```mermaid
flowchart TD
    Customer([Customer Voice/Text]) --> Router{Input Router}
    
    subgraph AI Assistant Engine
        Router -->|Local Trial Model| Ollama[Ollama Local LLM: llama3/mistral<br/>http://localhost:11434]
        Router -->|Offline / CI Demo| Simulator[Autonomous High-Fidelity Simulator]
        
        Ollama <-->|JSON Function Calling| Tools[Deterministic Backend Tools]
        Simulator <-->|Deterministic Routing| Tools
        
        Tools --> T1[search_menu<br/>Jain root-veg filter, budget, protein]
        Tools --> T2[get_menu_item<br/>Recipe facts, spice, allergens]
        Tools --> T3[propose_cart<br/>5% GST, packaging fee, 2m TTL]
        Tools --> T4[get_reorder_proposal<br/>Re-evaluates current prices]
        Tools --> T5[get_order_status<br/>Live tracking & rider info]
    end

    subgraph Action-Lock Confirmation Gate
        T3 --> ProposalCard[Immutable Proposal Card<br/>requires_confirmation=True]
        ProposalCard --> HumanGate{Customer Confirms?<br/>'Kya main confirm kar doon?'}
        HumanGate -->|Yes| Confirmed[Order Confirmed & Placed<br/>Idempotency Key Protected]
        HumanGate -->|No / Edit| Edit[Cart Revised]
    end

    subgraph Private Calling Engine
        Confirmed --> LiveOrder[Live Out-For-Delivery Order]
        LiveOrder --> CallManager[Private Calling Manager<br/>Managed Agora/WebRTC RTC]
        
        CallManager --> Eligibility[Eligibility Check<br/>Customer & Assigned Driver Only<br/>Delivery + 30m Hard Cutoff]
        Eligibility --> RateLimit[Rate Limiter<br/>Max 5 Calls / 10 Mins Window]
        RateLimit --> ConsentGate{Two-Party Consent?<br/>Both Customer & Driver Agree}
        ConsentGate -->|Yes & Recorder Ready| ConnectedCall([Encrypted Audio Connected<br/>Recording Active<br/>No Real Phone Numbers Exposed])
        ConsentGate -->|No| ChatFallback([Audio Blocked<br/>Order Chat Fallback])
    end
```

---

## ⚡ Core Features & Invariants

### 1. Trial Model (Ollama Local LLM Integration)
- Connects to a local Ollama daemon at `http://localhost:11434/api/chat`.
- Works with open-weight models such as `llama3`, `mistral`, `qwen2.5`, or `llama3.2`.
- Uses low-temperature structured system prompts for zero hallucinations and fluent Indian Hinglish.
- **Graceful Fallback**: If Ollama is not installed or offline, the system automatically falls back to the **Autonomous High-Fidelity Simulator**, ensuring 100% test reliability and seamless evaluation anywhere!

### 2. Strict Jain & Dietary Invariants
- **Root Vegetable Exclusions**: Absolute exclusion of potatoes (*aaloo*), onions (*pyaz*), garlic (*lehsun*), carrots (*gajar*), and radishes (*mooli*).
- **Polite Educational Flow**: When a customer inadvertently requests a non-Jain item (like *Paneer Butter Masala* or *Veg Cheese Pizza*), the assistant never quietly substitutes it. It explains:
  > *"Maaf kijiye, Paneer Butter Masala Jain nahi ban sakta kyunki iski base gravy me pyaz aur lehsun hota hai. Lekin hamare paas verified 'Jain Special Capsicum & Corn Pizza' aur 'Jain Dal Khichdi' available hain! Kya inme se kuch add kar doon?"*
- **Unknown States**: Missing allergen or cross-contact information remains explicitly unknown and is never converted into an unsubstantiated safety claim.

### 3. Deterministic Backend Tools & Zero Hallucination
- `search_menu`: Searches verified items by branch, cuisine, Jain rules, budget, and protein.
- `get_menu_item`: Returns factual recipe details, spice level, and creaminess.
- `propose_cart`: Calculates line items, 5% restaurant GST, and packaging charges.
- `get_reorder_proposal`: Re-validates previous orders against current active menu prices.
- `get_order_status`: Returns live tracking status with driver assignment and calling eligibility.
- `get_preferences`: Accesses consented dietary memory.

### 4. Cart Proposal & Action-Lock Confirmation Gate
- Proposals have a unique `proposal_id`, `cart_version`, and expire after **2 minutes**.
- The assistant cannot charge payments or submit orders autonomously.
- Confirmation is protected by the `Idempotency-Key` HTTP header to prevent double-charging on network retries.

### 5. Private Calling & Privacy Guardrails (Agora RTC)
- **Zero PSTN Exposure**: Neither the customer nor the delivery partner ever sees the other's real phone number.
- **Strict Delivery + 30-Minute Cutoff**: Calls are permitted only while the assigned driver is active, and for at most 30 minutes after delivery. Active audio is terminated within a 5-second target upon expiration.
- **Driver Reassignment Revocation**: If a driver is reassigned or the order is cancelled, old credentials cannot reconnect.
- **Two-Party Recording Consent**: Audio transmission is strictly blocked until **both** customer and driver give recording consent and recorder health is verified.
- **Rate Limiting**: Max 5 unique call attempts per order in a 10-minute rolling window.
- **Admin-Only Audited Playback**: Audio recordings are stored in private buckets; admins receive 5-minute expiring signed URLs.

---

## 🌉 Resto Integration Bridge

[`resto_bridge.py`](file:///c:/arpzo/resto_bridge.py) bridges the data between this voice assistant and the MongoDB schemas in `Karan7s7n/resto`:
- Maps `MenuItem` to verified recipe facts with root-vegetable verification and nutrition.
- Connects `Order` status transitions (`CONFIRMED`, `OUT_FOR_DELIVERY`, `DELIVERED`, `CANCELLED`) to the calling eligibility lifecycle.

---

## 📡 API Specification (REST & WebSockets)

### Assistant Endpoints
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/v1/assistant/sessions` | Creates an authenticated assistant session with language configuration. |
| `POST` | `/v1/assistant/turns` | Submits customer text or speech transcript and returns the assistant response. |
| `WS` | `/v1/assistant/stream` | WebSocket for streaming turns, partial transcripts, and turn cancellation. |
| `POST` | `/v1/cart/proposals` | Generates an immutable proposal card with backend-computed totals. |
| `POST` | `/v1/cart/confirm` | Confirms proposal with `Idempotency-Key` and hands off to checkout. |
| `GET` | `/v1/me/preferences` | Fetches customer's consented dietary preferences. |
| `PATCH` | `/v1/me/preferences` | Updates consented preferences. |
| `DELETE` | `/v1/me/preferences` | Deletes stored preference profile. |
| `GET` | `/v1/orders/{id}/status` | Live order tracking status and driver contact eligibility. |

### Private Calling Endpoints
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/v1/calls` | Initiates an authorized private internet call for an active order. |
| `POST` | `/v1/call/token` | Generates short-lived 10-minute Agora RTC media token. |
| `GET` | `/v1/calls/{id}` | Fetches current call lifecycle state. |
| `POST` | `/v1/calls/{id}/accept` | Accepts call and validates two-party recording consent. |
| `POST` | `/v1/calls/{id}/end` | Ends call and stops recording immediately. |
| `POST` | `/v1/admin/recordings/{id}/playback` | Issues 5-minute expiring signed playback URL for authorized admins. |
| `POST` | `/v1/devices` | Registers VoIP push tokens (APNs / FCM) for incoming call presentation. |

---

## 📦 Visual Proposal Card Interface

When a cart is proposed, the assistant renders a structured ASCII proposal card:

```text
+================================================================+
|             ARPZO RESTAURANT - ORDER PROPOSAL CARD             |
|             Proposal ID: PROP-C38DC6 | Status: PROPOSED         |
+----------------------------------------------------------------+
| Item                         Variant    Qty  Price    Total    |
+----------------------------------------------------------------+
| Jain Special Capsicum & Corn Regular    1    INR 399  INR 399  |
| Jain Dal Khichdi             Full       1    INR 220  INR 220  |
+----------------------------------------------------------------+
| Item Subtotal:                                     INR   619.00 |
| Restaurant GST (5%):                               INR    30.95 |
| Packaging & Delivery Charge:                       INR    25.00 |
+================================================================+
| GRAND TOTAL (Payable):                             INR   674.95 |
+================================================================+
| Dietary - Jain Verified: YES (100% Verified)                   |
| Allergens Noted: Dairy (Pure Desi Ghee), Gluten (Wheat)        |
| Action Gate - Requires Explicit Confirmation: True             |
+----------------------------------------------------------------+
```

---

## 🚀 Getting Started & Quickstart

### Prerequisites
- Python 3.10+
- (Optional) [Ollama](https://ollama.com/) running locally:
  ```bash
  ollama run llama3
  ```

### 1. Interactive CLI (Voice & Text Simulation)
Run the interactive terminal assistant with push-to-talk turn simulation:
```bash
python run.py --cli
# or directly: python arpzo_assistant.py
```
*Try typing:*
- `"Mujhe Jain pizza add karna hai"`
- `"Paneer Butter Masala Jain ban sakta hai kya?"`
- `"Same as last time repeat kardo"`
- `"Order kahan pahucha, track karo"`

### 2. Start the FastAPI Backend & Web Application
```bash
python run.py --server
# or directly: python backend/main.py
```
- **Web Interface (Glassmorphic Voice Assistant & Calling)**: `http://localhost:8000/app/`
- **Interactive Swagger Documentation**: `http://localhost:8000/docs`

---

## 🧪 Automated Verification & Security Acceptance Tests

Run all test suites in a single command:
```bash
python run.py --test
```

Or run individual targeted test suites:
```bash
# 1. Run Dedicated Security & Threat Audit (SEC-01 to SEC-08)
python run.py --security
# or: python tests/test_security.py

# 2. Run Assistant Acceptance Tests (A01 to A15)
python tests/test_assistant.py

# 3. Run Private Calling Acceptance Tests (C01 to C17)
python tests/test_calling.py

# 4. Run REST & WebSocket API Tests
python tests/test_api.py
```

### 🛡️ Dedicated Security Audit Results (`python run.py --security`)
```text
========================================================
  RUNNING ARPZO SECURITY & DEFENSE AUDIT SUITE           
========================================================

  [PASS] SEC-01: Prompt injection and jailbreak attempts intercepted.
  [PASS] SEC-02: Tenant isolation verified; unauthorized participants denied.
  [PASS] SEC-03: 5 attempts/10min rate limit enforced; 6th attempt returned HTTP 429.
  [PASS] SEC-04: Two-party consent gate blocks audio if unrecorded.
  [PASS] SEC-05: Admin-only signed playback links issued with audit logging.
  [PASS] SEC-06: Telemetry scrubbed; zero real phone numbers or keys exposed.
  [PASS] SEC-07: Delivery + 30m cutoff strictly blocks stale call attempts.

----------------------------------------------------------------------
Ran 7 tests in 0.003s

OK
```

---

## 📁 Sorted & Modular Project Structure

```text
arpzo-voice-agent/
├── backend/
│   ├── app/
│   │   ├── __init__.py           # Application package exports
│   │   ├── config.py             # Server ports, Ollama URLs, Agora tokens, rate limits
│   │   ├── security.py           # Prompt injection filters, tenant isolation, scrubbing
│   │   ├── catalog.py            # In-memory verified catalog, nutrition, strict Jain facts
│   │   ├── tools.py              # search_menu, propose_cart, reorder, live tracking
│   │   ├── assistant.py          # Ollama local LLM engine + autonomous simulator
│   │   ├── calling.py            # Private Calling Manager, Agora tokens, consent gate
│   │   ├── bridge.py             # RestoBridge mapping to Karan7s7n/resto MongoDB
│   │   └── api.py                # FastAPI endpoints, WebSockets, static file mounts
│   ├── main.py                   # Backend entrypoint (uvicorn launcher)
│   └── requirements.txt          # Python dependencies
│
├── frontend/
│   ├── index.html                # Glassmorphic web UI (voice mic, cards, calling modal)
│   ├── style.css                 # Vanilla CSS: dark mode, pulse waves, responsive design
│   └── app.js                    # Web Speech API, live cart proposals, Agora RTC simulator
│
├── tests/
│   ├── test_security.py          # Dedicated security audit: SEC-01 to SEC-08
│   ├── test_assistant.py         # Assistant acceptance tests: A01 to A15
│   ├── test_calling.py           # Private calling tests: C01 to C17
│   └── test_api.py               # FastAPI REST & WebSocket test suite
│
├── run.py                        # Unified orchestrator (--server, --cli, --test, --security)
├── arpzo_assistant.py            # Standalone CLI entrypoint
├── test_suite.py                 # Acceptance runner for all 63 P0 cases
├── .gitignore                    # Git ignore configuration
└── README.md                     # Complete project documentation & audit report
```

---

## 🎓 3rd Year B.Tech Project Reflections

Building this project taught me that production AI engineering isn't just about calling an LLM endpoint—it is about **strict guardrail engineering**:
- Designing **Action Locks** so an LLM cannot deduct money or alter orders without explicit human confirmation.
- Building **deterministic tools** for taxes and pricing so floating-point errors and hallucinated discounts never happen.
- Enforcing **cultural dietary compliance** (Jain principles) deterministically at the tool layer.
- Protecting user privacy using **managed WebRTC/Agora RTC channels** and strict time-based expirations.

Thank you for reviewing! Feel free to raise issues or star this repo! ⭐
