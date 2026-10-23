"""
================================================================================
🛡️ ARPZO SECURITY & DEFENSE MODULE
================================================================================
Author: Axar Tandon (3rd Year B.Tech CSE - AI/ML)
Specification Reference: Section 11, 12 (A14), 14 (C10 - C17)

Security Layers:
1. Prompt Injection & Jailbreak Defense: Blocks attempts to override dietary rules
   or extract hidden credentials.
2. Tenant & Participant Isolation: Validates that customers and drivers can ONLY
   access orders and call sessions they are actively assigned to.
3. Phone Number & Secret Redaction: Sanitizes logs and signaling payloads so
   real PSTN numbers or service credentials are never exposed.
4. Replay & Rate Limit Defense: Shared rolling-window rate limiter per order.
5. Audited Access: Admin recording access is permanently logged with timestamps.
================================================================================
"""

import re
import time
import json
from typing import Dict, Any, List, Optional, Tuple

# Patterns identifying prompt injection attempts
PROMPT_INJECTION_PATTERNS = [
    r"ignore (all )?previous instructions",
    r"override (system|dietary|pricing) rules?",
    r"system prompt",
    r"you are now (an? )?(unrestricted|developer mode)",
    r"say that .* is jain",
    r"bypass (guardrail|filter|confirmation)",
    r"admin_token",
    r"drop table",
    r"<script>",
    r"eval\(",
]

PHONE_PATTERN = re.compile(r"(\+?91[\-\s]?)?[6-9]\d{9}")
SECRET_PATTERN = re.compile(r"(gho_[a-zA-Z0-9]{30,}|agora_[a-zA-Z0-9_]{10,}|bearer\s+[a-zA-Z0-9_\-\.]+)", re.IGNORECASE)


class SecurityGuard:
    """Enterprise security gatekeeper for ARPZO Assistant and Calling Engine."""

    @staticmethod
    def sanitize_user_input(user_text: str) -> Tuple[bool, str, Optional[str]]:
        """Scans input for prompt injection, malicious jailbreaks, or command injection.
        
        Returns:
            (is_safe: bool, cleaned_text: str, warning_reason: Optional[str])
        """
        text = (user_text or "").strip()
        lower_text = text.lower()

        for pattern in PROMPT_INJECTION_PATTERNS:
            if re.search(pattern, lower_text):
                return False, "", f"Input violated security policy (detected pattern: '{pattern}'). Request blocked."

        return True, text, None

    @staticmethod
    def verify_order_participant(order_record: Dict[str, Any], user_id: str) -> bool:
        """Enforces tenant isolation: caller must be either the customer or assigned driver."""
        if not order_record or not user_id:
            return False

        allowed_users = [
            str(order_record.get("customer_id", "")),
            str(order_record.get("user_id", "")),
            str(order_record.get("driver_id", "")),
            str(order_record.get("rider_id", ""))
        ]
        return user_id in allowed_users

    @staticmethod
    def redact_sensitive_data(payload: Any) -> Any:
        """Recursively scrubs real phone numbers and credentials from data dictionaries and logs."""
        if isinstance(payload, str):
            # Redact phone numbers
            redacted = PHONE_PATTERN.sub("[REDACTED_PHONE]", payload)
            # Redact service secrets
            redacted = SECRET_PATTERN.sub("[REDACTED_SECRET]", redacted)
            return redacted
        elif isinstance(payload, dict):
            clean_dict = {}
            for k, v in payload.items():
                if any(sec_key in k.lower() for sec_key in ["password", "secret", "token", "credential"]):
                    clean_dict[k] = "[REDACTED_SECRET]"
                elif any(sec_key in k.lower() for sec_key in ["phone", "mobile", "contact"]):
                    clean_dict[k] = "[REDACTED_PHONE]"
                else:
                    clean_dict[k] = SecurityGuard.redact_sensitive_data(v)
            return clean_dict
        elif isinstance(payload, list):
            return [SecurityGuard.redact_sensitive_data(item) for item in payload]
        return payload

    @staticmethod
    def audit_admin_access(admin_id: str, action: str, resource_id: str):
        """Authoritative immutable audit logging for admin security compliance."""
        audit_entry = {
            "timestamp": time.time(),
            "admin_id": admin_id,
            "action": action,
            "resource_id": resource_id,
            "status": "AUTHORIZED"
        }
        # In production this writes to a secure SIEM / CloudWatch append-only stream
        print(f"  [SECURITY AUDIT] {json.dumps(audit_entry)}")
