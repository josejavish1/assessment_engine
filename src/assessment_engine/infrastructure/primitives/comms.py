"""
Canonical Communications & Notification Engine — System 08 (Novu Pattern / SOTA 2026).
Consolidated multichannel delivery suite:
1. Meta WhatsApp Cloud API payload and Click-to-Chat dispatcher.
2. Transactional email dispatcher with HTML templating.
3. Stripe-style signed outgoing webhooks (X-Autonomuos-Signature).
4. Web Push VAPID notification payload builder (RFC 8292).
5. Immutable delivery audit tracking in app.db.
"""

from __future__ import annotations

from assessment_engine.infrastructure.primitives.communications_bus import (
    CommunicationsBusPrimitive,
    DispatchResult,
    communications_bus
)
from assessment_engine.infrastructure.primitives.web_push_vapid import WebPushVAPIDPrimitive, web_push_vapid

comms_engine = communications_bus
