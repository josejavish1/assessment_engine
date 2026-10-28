"""
Canonical Scheduling & Booking Engine — System 05 (Cal.com Architecture / SOTA 2026).
Consolidated temporal scheduling suite:
1. Deterministic interval partitioning for slots (15, 30, 45, 60 minutes).
2. Split working shifts (morning and afternoon).
3. Pre- and post-booking buffer times (e.g. 15-minute sanitization).
4. Mathematical interval collision detection: max(s1, s2) < min(e1, e2).
5. RFC 5545 iCalendar (.ics) event export for Google, Apple, and Outlook.
"""

from __future__ import annotations

from assessment_engine.infrastructure.primitives.booking_slots import (
    BookingSlotsPrimitive,
    WorkingShift,
    ExistingBooking,
    AvailableSlot,
    booking_slots
)

booking_engine = booking_slots
