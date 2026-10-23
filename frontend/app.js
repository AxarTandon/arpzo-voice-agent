/**
 * ARPZO Voice Assistant & Private Calling Frontend Client
 * Author: Axar Tandon (3rd Year B.Tech CSE - AI/ML)
 */

const API_BASE = window.location.origin;

// State
let sessionId = null;
let currentLanguage = "hinglish";
let currentProposal = null;
let isListening = false;
let callTimerInterval = null;
let callSeconds = 0;
let currentCallId = null;

// DOM Elements
const messagesContainer = document.getElementById("messagesContainer");
const userInput = document.getElementById("userInput");
const sendBtn = document.getElementById("sendBtn");
const micBtn = document.getElementById("micBtn");
const proposalBody = document.getElementById("proposalBody");
const proposalFooter = document.getElementById("proposalFooter");
const proposalStatusBadge = document.getElementById("proposalStatusBadge");
const confirmOrderBtn = document.getElementById("confirmOrderBtn");
const clearChatBtn = document.getElementById("clearChatBtn");
const startCallBtn = document.getElementById("startCallBtn");
const callModal = document.getElementById("callModal");
const hangupBtn = document.getElementById("hangupBtn");
const callTimer = document.getElementById("callTimer");
const callStateText = document.getElementById("callStateText");
const consentCheckbox = document.getElementById("consentCheckbox");

// 1. Initialize Assistant Session
async function initSession() {
  try {
    const res = await fetch(`${API_BASE}/v1/assistant/sessions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ branch_id: "branch_koramangala_01", language: currentLanguage })
    });
    if (res.ok) {
      const data = await res.json();
      sessionId = data.session_id;
      console.log("Initialized ARPZO Voice Session:", sessionId);
    }
  } catch (err) {
    console.warn("Could not reach backend API directly; running in local simulator mode.");
  }
}

// 2. Append Chat Message
function appendMessage(sender, text, rawProposal = null) {
  const msgDiv = document.createElement("div");
  msgDiv.className = `message ${sender}`;

  const avatar = document.createElement("div");
  avatar.className = "msg-avatar";
  avatar.textContent = sender === "user" ? "👤" : "🤖";

  const bubble = document.createElement("div");
  bubble.className = "msg-bubble";

  // Check if text has ascii box
  if (text.includes("+===") || text.includes("+---")) {
    const parts = text.split("+===");
    const regularText = parts[0];
    const p = document.createElement("p");
    p.textContent = regularText;
    bubble.appendChild(p);

    const pre = document.createElement("pre");
    pre.textContent = "+===" + parts.slice(1).join("+===");
    bubble.appendChild(pre);
  } else {
    const p = document.createElement("p");
    p.textContent = text;
    bubble.appendChild(p);
  }

  msgDiv.appendChild(avatar);
  msgDiv.appendChild(bubble);
  messagesContainer.appendChild(msgDiv);
  messagesContainer.scrollTop = messagesContainer.scrollHeight;

  if (rawProposal) {
    renderProposalCard(rawProposal);
  }
}

// 3. Render Proposal Card in Sidebar
function renderProposalCard(proposal) {
  currentProposal = proposal;
  proposalStatusBadge.textContent = proposal.status || "PROPOSED";
  proposalStatusBadge.className = "badge badge-success";

  const itemsHtml = proposal.items.map(i => `
    <tr>
      <td>${i.name} <small>(${i.variant})</small></td>
      <td>${i.quantity}</td>
      <td>₹${i.unit_price}</td>
      <td>₹${i.line_total}</td>
    </tr>
  `).join("");

  const dietTag = proposal.dietary_summary.all_jain_verified 
    ? '<span class="diet-tag">✅ 100% Verified Jain</span>' 
    : '<span class="diet-tag" style="background:rgba(239,68,68,0.15);color:#f87171;">Non-Jain Items Present</span>';

  proposalBody.innerHTML = `
    <div class="proposal-card-render">
      <table class="proposal-items-table">
        <thead>
          <tr><th>Item</th><th>Qty</th><th>Price</th><th>Total</th></tr>
        </thead>
        <tbody>
          ${itemsHtml}
        </tbody>
      </table>

      <div class="proposal-calc-row">
        <span>Item Subtotal:</span>
        <span>₹${proposal.subtotal.toFixed(2)}</span>
      </div>
      <div class="proposal-calc-row">
        <span>Restaurant GST (5%):</span>
        <span>₹${proposal.tax_gst_5pct.toFixed(2)}</span>
      </div>
      <div class="proposal-calc-row">
        <span>Packaging & Delivery:</span>
        <span>₹${proposal.packaging_delivery_charge.toFixed(2)}</span>
      </div>

      <div class="proposal-grand-total">
        <span>Payable Total:</span>
        <span>₹${proposal.grand_total.toFixed(2)}</span>
      </div>

      <div class="dietary-badge-row">
        ${dietTag}
      </div>
    </div>
  `;

  proposalFooter.style.display = "flex";
}

// 4. Send Message to Backend
async function handleUserSend(text) {
  const query = (text || userInput.value || "").trim();
  if (!query) return;

  userInput.value = "";
  appendMessage("user", query);

  if (!sessionId) {
    await initSession();
  }

  try {
    const res = await fetch(`${API_BASE}/v1/assistant/turns`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, text: query })
    });

    if (res.ok) {
      const data = await res.json();
      appendMessage("assistant", data.assistant_text, data.proposal);
    } else {
      appendMessage("assistant", "Maaf kijiye, temporary server issue hai. Kripya dobara try karein.");
    }
  } catch (err) {
    appendMessage("assistant", "Connecting to local ARPZO engine: Processing your query...");
  }
}

// 5. Confirm Order Action Gate
confirmOrderBtn.addEventListener("click", async () => {
  if (!currentProposal) return;
  const idempotencyKey = "key_web_" + Math.random().toString(36).substring(2, 9);

  try {
    const res = await fetch(`${API_BASE}/v1/cart/confirm`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Idempotency-Key": idempotencyKey
      },
      body: JSON.stringify({
        proposal_id: currentProposal.proposal_id,
        expected_cart_version: currentProposal.cart_version || 1
      })
    });

    if (res.ok) {
      const data = await res.json();
      appendMessage("assistant", `🎉 Dhanyawaad! Aapka order successfully place ho gaya hai! (Order ID: ${data.order_id}). Kitchen is preparing your food!`);
      proposalBody.innerHTML = `<div class="empty-state"><span class="empty-icon">✅</span><p>Order <strong>${data.order_id}</strong> is Confirmed! Track it using the Calling card.</p></div>`;
      proposalFooter.style.display = "none";
      currentProposal = null;
    }
  } catch (err) {
    alert("Could not confirm order. Please try again.");
  }
});

// 6. Speech Recognition (Web Speech API)
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
if (SpeechRecognition) {
  const recognition = new SpeechRecognition();
  recognition.continuous = false;
  recognition.interimResults = false;
  recognition.lang = currentLanguage === "hindi" ? "hi-IN" : "en-IN";

  micBtn.addEventListener("click", () => {
    if (!isListening) {
      recognition.start();
      isListening = true;
      micBtn.classList.add("listening");
    } else {
      recognition.stop();
      isListening = false;
      micBtn.classList.remove("listening");
    }
  });

  recognition.onresult = (e) => {
    const transcript = e.results[0][0].transcript;
    userInput.value = transcript;
    isListening = false;
    micBtn.classList.remove("listening");
    handleUserSend(transcript);
  };

  recognition.onerror = () => {
    isListening = false;
    micBtn.classList.remove("listening");
  };
} else {
  micBtn.addEventListener("click", () => {
    alert("Speech Recognition is supported in Chrome/Edge. You can type in English, Hindi, or Hinglish below!");
  });
}

// 7. Event Listeners
sendBtn.addEventListener("click", () => handleUserSend());
userInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter") handleUserSend();
});

document.querySelectorAll(".chip").forEach(chip => {
  chip.addEventListener("click", () => {
    const text = chip.getAttribute("data-prompt");
    handleUserSend(text);
  });
});

clearChatBtn.addEventListener("click", () => {
  messagesContainer.innerHTML = `
    <div class="message assistant">
      <div class="msg-avatar">🤖</div>
      <div class="msg-bubble">
        <p>Aapka session reset kar diya gaya hai. Batayein, aaj kya order karenge?</p>
      </div>
    </div>
  `;
  initSession();
});

// Language Buttons
document.querySelectorAll(".lang-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".lang-btn").forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    currentLanguage = btn.getAttribute("data-lang");
    console.log("Language changed to:", currentLanguage);
  });
});

// 8. Private Calling Flow Simulator
startCallBtn.addEventListener("click", async () => {
  callModal.style.display = "flex";
  callStateText.textContent = "Initiating encrypted call channel (POST /v1/calls)...";
  callSeconds = 0;
  callTimer.textContent = "00:00";

  try {
    const res = await fetch(`${API_BASE}/v1/calls`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ order_id: "ord_live_789", caller_id: "user_demo_101" })
    });
    const callData = await res.json();
    currentCallId = callData.call_id;

    callStateText.textContent = "Ringing driver's device (30s window)...";

    // Simulate driver acceptance after 2 seconds
    setTimeout(async () => {
      const consentGiven = consentCheckbox.checked;
      const accRes = await fetch(`${API_BASE}/v1/calls/${currentCallId}/accept`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: "rider_rahul_404", customer_consent: consentGiven, driver_consent: true })
      });

      if (accRes.ok) {
        callStateText.textContent = "Connected • Recording Active • Audio Flowing";
        callTimerInterval = setInterval(() => {
          callSeconds++;
          const mins = String(Math.floor(callSeconds / 60)).padStart(2, "0");
          const secs = String(callSeconds % 60).padStart(2, "0");
          callTimer.textContent = `${mins}:${secs}`;
        }, 1000);
      } else {
        const err = await accRes.json();
        callStateText.textContent = `Call Rejected: ${err.detail || err.error}`;
      }
    }, 2000);

  } catch (err) {
    callStateText.textContent = "Simulated internet call connected via Agora RTC.";
  }
});

hangupBtn.addEventListener("click", async () => {
  if (callTimerInterval) clearInterval(callTimerInterval);
  if (currentCallId) {
    await fetch(`${API_BASE}/v1/calls/${currentCallId}/end`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: "user_demo_101", reason: "NORMAL_HANGUP" })
    }).catch(() => {});
  }
  callModal.style.display = "none";
});

// Init on load
initSession();
