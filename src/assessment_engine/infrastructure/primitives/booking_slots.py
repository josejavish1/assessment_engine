"""
Temporal & Booking Slots Primitive — GEMA 05 / Radar Primitive 5 (Cal.com Architecture / SOTA 2026).
Engine for deterministic slot partitioning, split shifts, buffer times, and collision detection.
Exports RFC 5545 compliant iCalendar (.ics) files for Apple, Google, and Outlook calendars.
Domain-agnostic: manages scheduling for surgery rooms, padel courts, legal consultations, or restaurant tables.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, time, timedelta
from typing import Any

logger = logging.getLogger("assessment_engine.infrastructure.primitives.booking_slots")


@dataclass(frozen=True)
class WorkingShift:
    start_hour: int
    start_minute: int
    end_hour: int
    end_minute: int


@dataclass(frozen=True)
class ExistingBooking:
    id: str
    start_dt: datetime
    end_dt: datetime
    resource_id: str = "default"


@dataclass
class FeedEvent:
    uid: str
    summary: str
    description: str
    start_dt: datetime
    end_dt: datetime
    location: str = "Centro Profesional"
    status: str = "CONFIRMED"  # "CONFIRMED" | "CANCELLED"
    sequence: int = 0
    organizer_email: str = "citas@autonomuos.app"
    attendee_email: str | None = None
    url: str | None = None
    is_utc: bool = True


@dataclass
class AvailableSlot:
    start_iso: str
    end_iso: str
    duration_minutes: int
    resource_id: str
    formatted_time: str  # "09:30 - 10:00"


def _is_slot_conflicting(
    slot_start: datetime,
    slot_end: datetime,
    bookings: list[ExistingBooking],
    resource_id: str,
    buffer_delta: timedelta,
) -> bool:
    """Check whether candidate slot conflicts with any existing booking for the resource."""
    for b in bookings:
        if b.resource_id != resource_id and b.resource_id != "all":
            continue
        b_buffered_start = b.start_dt - buffer_delta
        b_buffered_end = b.end_dt + buffer_delta
        if max(slot_start, b_buffered_start) < min(slot_end, b_buffered_end):
            return True
    return False


class BookingSlotsPrimitive:
    """
    Compute canonical availability and booking slots using the Cal.com pattern.
    """

    def generate_slots_for_day(
        self,
        target_date: datetime | str,
        shifts: list[WorkingShift],
        duration_minutes: int = 30,
        buffer_minutes: int = 0,
        existing_bookings: list[ExistingBooking] | None = None,
        resource_id: str = "default"
    ) -> list[AvailableSlot]:
        """
        Partition work shifts into free slots, excluding overlaps and buffer times.
        """
        if isinstance(target_date, str):
            dt = datetime.fromisoformat(target_date.split("T")[0])
        else:
            dt = target_date

        base_date = dt.date()
        bookings = existing_bookings or []
        available_slots: list[AvailableSlot] = []

        slot_delta = timedelta(minutes=duration_minutes)
        buffer_delta = timedelta(minutes=buffer_minutes)

        for shift in shifts:
            shift_start = datetime.combine(base_date, time(shift.start_hour, shift.start_minute))
            shift_end = datetime.combine(base_date, time(shift.end_hour, shift.end_minute))

            current_cursor = shift_start
            while current_cursor + slot_delta <= shift_end:
                slot_start = current_cursor
                slot_end = current_cursor + slot_delta

                if not _is_slot_conflicting(slot_start, slot_end, bookings, resource_id, buffer_delta):
                    available_slots.append(AvailableSlot(
                        start_iso=slot_start.isoformat(),
                        end_iso=slot_end.isoformat(),
                        duration_minutes=duration_minutes,
                        resource_id=resource_id,
                        formatted_time=f"{slot_start.strftime('%H:%M')} - {slot_end.strftime('%H:%M')}"
                    ))

                current_cursor += slot_delta + buffer_delta

        logger.debug(f"[BookingSlots] Calculados {len(available_slots)} slots libres para {base_date} en recurso '{resource_id}'")
        return available_slots

    def check_collision(
        self,
        new_start: datetime,
        new_end: datetime,
        existing_bookings: list[ExistingBooking],
        resource_id: str = "default",
        buffer_minutes: int = 0
    ) -> tuple[bool, str | None]:
        """Check whether a booking attempt conflicts with another appointment in the same room or resource."""
        buf = timedelta(minutes=buffer_minutes)

        for b in existing_bookings:
            if b.resource_id != resource_id and b.resource_id != "all":
                continue

            b_start = b.start_dt - buf
            b_end = b.end_dt + buf

            if max(new_start, b_start) < min(new_end, b_end):
                reason = f"Conflicto de horario con la reserva #{b.id} ({b.start_dt.strftime('%H:%M')} - {b.end_dt.strftime('%H:%M')})"
                return True, reason

        return False, None

    def generate_ics_calendar_event(
        self,
        summary: str,
        description: str,
        start_dt: datetime,
        end_dt: datetime,
        location: str = "Centro Profesional",
        organizer_email: str = "citas@autonomuos.app",
        is_utc: bool = False
    ) -> str:
        """Generate RFC 5545-compliant .ics file content for mobile calendars."""
        uid = f"evt_{uuid.uuid4().hex}@autonomuos.app"
        now_stamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        suffix = "Z" if is_utc else ""
        start_stamp = start_dt.strftime("%Y%m%dT%H%M%S") + suffix
        end_stamp = end_dt.strftime("%Y%m%dT%H%M%S") + suffix

        clean_summary = summary.replace("\n", " ").strip()
        clean_desc = description.replace("\n", "\\n").strip()

        return f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Autonomuos SOTA 2026//Booking Slots Engine//ES
CALSCALE:GREGORIAN
METHOD:REQUEST
BEGIN:VEVENT
UID:{uid}
DTSTAMP:{now_stamp}
DTSTART:{start_stamp}
DTEND:{end_stamp}
SUMMARY:{clean_summary}
DESCRIPTION:{clean_desc}
LOCATION:{location}
ORGANIZER;CN=Servicio Oficial:mailto:{organizer_email}
STATUS:CONFIRMED
TRANSP:OPAQUE
SEQUENCE:0
END:VEVENT
END:VCALENDAR"""

    def generate_google_calendar_url(
        self,
        summary: str,
        description: str,
        start_dt: datetime,
        end_dt: datetime,
        location: str = "Centro Profesional",
        is_utc: bool = True
    ) -> str:
        """Generate the Google Calendar web intent URL to add the appointment."""
        import urllib.parse
        suffix = "Z" if is_utc else ""
        start_stamp = start_dt.strftime("%Y%m%dT%H%M%S") + suffix
        end_stamp = end_dt.strftime("%Y%m%dT%H%M%S") + suffix
        params = {
            "action": "TEMPLATE",
            "text": summary,
            "details": description,
            "location": location,
            "dates": f"{start_stamp}/{end_stamp}"
        }
        return f"https://calendar.google.com/calendar/render?{urllib.parse.urlencode(params)}"

    def generate_webcal_feed(
        self,
        calendar_name: str,
        events: list[FeedEvent],
        calendar_description: str = "Suscripción oficial de citas",
        refresh_interval_minutes: int = 15,
        timezone_str: str = "UTC"
    ) -> str:
        """Generate an RFC 5545-compliant live subscription feed for Apple Calendar, Google Calendar, and Outlook. Support SEQUENCE versioning for rescheduling, CONFIRMED/CANCELLED statuses, and VALARM alarms."""
        now_stamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        lines = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//Autonomuos Platform 2026//Live Webcal Engine//ES",
            "CALSCALE:GREGORIAN",
            "METHOD:PUBLISH",
            f"X-WR-CALNAME:{calendar_name.replace(chr(10), ' ').strip()}",
            f"X-WR-CALDESC:{calendar_description.replace(chr(10), ' ').strip()}",
            f"X-WR-TIMEZONE:{timezone_str}",
            f"REFRESH-INTERVAL;VALUE=DURATION:PT{refresh_interval_minutes}M",
            f"X-PUBLISHED-TTL:PT{refresh_interval_minutes}M",
        ]

        for ev in events:
            suffix = "Z" if ev.is_utc else ""
            start_stamp = ev.start_dt.strftime("%Y%m%dT%H%M%S") + suffix
            end_stamp = ev.end_dt.strftime("%Y%m%dT%H%M%S") + suffix
            clean_summary = ev.summary.replace("\n", " ").strip()
            clean_desc = ev.description.replace("\r", "").replace("\n", "\\n").strip()
            clean_loc = ev.location.replace("\n", " ").strip()

            lines.extend([
                "BEGIN:VEVENT",
                f"UID:{ev.uid}",
                f"DTSTAMP:{now_stamp}",
                f"DTSTART:{start_stamp}",
                f"DTEND:{end_stamp}",
                f"SUMMARY:{clean_summary}",
                f"DESCRIPTION:{clean_desc}",
                f"LOCATION:{clean_loc}",
                f"ORGANIZER;CN=Soverik Platform:mailto:{ev.organizer_email}",
                f"STATUS:{ev.status.upper()}",
                f"SEQUENCE:{ev.sequence}",
                "TRANSP:OPAQUE" if ev.status.upper() == "CONFIRMED" else "TRANSP:TRANSPARENT",
            ])

            if ev.attendee_email:
                lines.append(f"ATTENDEE;ROLE=REQ-PARTICIPANT;PARTSTAT=ACCEPTED:mailto:{ev.attendee_email}")

            if ev.url:
                lines.append(f"URL:{ev.url.strip()}")

            if ev.status.upper() == "CONFIRMED":
                lines.extend([
                    "BEGIN:VALARM",
                    "TRIGGER:-PT1H",
                    "ACTION:DISPLAY",
                    f"DESCRIPTION:Recordatorio de Cita: {clean_summary}",
                    "END:VALARM",
                    "BEGIN:VALARM",
                    "TRIGGER:-PT15M",
                    "ACTION:DISPLAY",
                    f"DESCRIPTION:Aviso Inminente (15m): {clean_summary}",
                    "END:VALARM",
                ])

            lines.append("END:VEVENT")

        lines.append("END:VCALENDAR")
        return "\r\n".join(lines) + "\r\n"

    @staticmethod
    def _parse_ics_datetime(val: str) -> datetime | None:
        import re
        val = val.strip()
        if re.match(r"^\d{8}T\d{6}Z$", val):
            return datetime.strptime(val, "%Y%m%dT%H%M%SZ")
        if re.match(r"^\d{8}T\d{6}$", val):
            return datetime.strptime(val, "%Y%m%dT%H%M%S")
        if re.match(r"^\d{8}$", val):
            return datetime.strptime(val, "%Y%m%d")
        return None

    @classmethod
    def _build_booking_from_event(cls, current_event: dict[str, str], resource_id: str) -> ExistingBooking | None:
        status = current_event.get("STATUS", "CONFIRMED").upper()
        dtstart_raw = current_event.get("DTSTART")
        dtend_raw = current_event.get("DTEND")
        if status == "CANCELLED" or not dtstart_raw:
            return None

        start_dt = cls._parse_ics_datetime(dtstart_raw)
        if not start_dt:
            return None

        if dtend_raw:
            end_dt = cls._parse_ics_datetime(dtend_raw) or (start_dt + timedelta(minutes=60))
        else:
            end_dt = start_dt + timedelta(minutes=60)

        uid = current_event.get("UID", f"ext_{uuid.uuid4().hex[:8]}")
        return ExistingBooking(id=uid, start_dt=start_dt, end_dt=end_dt, resource_id=resource_id)

    def parse_ics_feed(
        self,
        ics_content: str,
        resource_id: str = "default"
    ) -> list[ExistingBooking]:
        """Parse and ingest an external RFC 5545 .ics feed or file, converting its VEVENT components into ExistingBooking objects to block availability in the engine. Support line unfolding, UTC, and local dates with TZID."""
        import re
        if not ics_content or "BEGIN:VCALENDAR" not in ics_content:
            return []

        normalized = re.sub(r"\r?\n[ \t]", "", ics_content)
        raw_lines = [l.strip() for l in normalized.splitlines() if l.strip()]

        bookings: list[ExistingBooking] = []
        in_vevent = False
        current_event: dict[str, str] = {}

        for line in raw_lines:
            if line == "BEGIN:VEVENT":
                in_vevent = True
                current_event = {}
                continue
            if line == "END:VEVENT":
                in_vevent = False
                bk = self._build_booking_from_event(current_event, resource_id)
                if bk:
                    bookings.append(bk)
                current_event = {}
                continue

            if in_vevent and ":" in line:
                key_part, val_part = line.split(":", 1)
                prop_name = key_part.split(";")[0].strip().upper()
                current_event[prop_name] = val_part.strip()

        return bookings


booking_slots = BookingSlotsPrimitive()
