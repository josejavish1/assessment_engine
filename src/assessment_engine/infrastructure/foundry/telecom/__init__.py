"""
Provide telecommunications and B2B messaging adapters. Decoupled from communications_bus.py following the Strangler Fig pattern. Provides:
- meta_whatsapp: Official Meta WhatsApp Cloud API connector (Graph API v20.0).
- twilio_sms: Outbound SMS connector with B2B routing and alphanumeric sender ID.
"""
