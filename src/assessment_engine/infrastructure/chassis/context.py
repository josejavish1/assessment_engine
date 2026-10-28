"""
Provide W3C Trace Context support (RFC 9458 / W3C Recommendation).
Implement deterministic, zero-dependency distributed context propagation.
"""
from __future__ import annotations

import contextvars
import re
import secrets
from dataclasses import dataclass

W3C_TRACEPARENT_REGEX = re.compile(
    r"^00-([0-9a-f]{32})-([0-9a-f]{16})-([0-9a-f]{2})$"
)

_current_trace_context: contextvars.ContextVar[TraceContext | None] = contextvars.ContextVar(
    "current_trace_context", default=None
)


@dataclass(frozen=True)
class TraceContext:
    trace_id: str
    span_id: str
    parent_span_id: str | None = None
    sampled: bool = True

    @classmethod
    def generate_new(cls, sampled: bool = True) -> TraceContext:
        """Generate a new deterministic W3C context with a 128-bit trace_id and a 64-bit span_id."""
        trace_id = secrets.token_hex(16)  # 32 caracteres hex (128 bits)
        span_id = secrets.token_hex(8)     # 16 caracteres hex (64 bits)
        return cls(trace_id=trace_id, span_id=span_id, parent_span_id=None, sampled=sampled)

    def new_child_span(self) -> TraceContext:
        """Create a child span while retaining the same trace_id."""
        child_span_id = secrets.token_hex(8)
        return TraceContext(
            trace_id=self.trace_id,
            span_id=child_span_id,
            parent_span_id=self.span_id,
            sampled=self.sampled
        )

    def to_w3c_header(self) -> str:
        """Serialize to a canonical W3C traceparent header."""
        flags = "01" if self.sampled else "00"
        return f"00-{self.trace_id}-{self.span_id}-{flags}"


def parse_w3c_traceparent(header_val: str | None) -> TraceContext | None:
    """Parse a strict W3C traceparent HTTP header. Return None if invalid."""
    if not header_val:
        return None
    header_val = header_val.strip()
    match = W3C_TRACEPARENT_REGEX.match(header_val)
    if not match:
        return None

    trace_id, span_id, flags_hex = match.groups()

    if trace_id == "0" * 32 or span_id == "0" * 16:
        return None

    flags_int = int(flags_hex, 16)
    sampled = bool(flags_int & 1)

    return TraceContext(trace_id=trace_id, span_id=span_id, sampled=sampled)


def set_current_trace_context(ctx: TraceContext | None) -> contextvars.Token:
    """Set the active trace context in the current coroutine."""
    return _current_trace_context.set(ctx)


def get_current_trace_context() -> TraceContext | None:
    """Get the active trace context in the current coroutine."""
    return _current_trace_context.get()


def get_current_trace_id() -> str:
    """Return the active trace_id or a deterministic static fallback if no context exists."""
    ctx = get_current_trace_context()
    return ctx.trace_id if ctx else "00000000000000000000000000000000"


def get_current_span_id() -> str:
    """Return the active span_id or a deterministic static fallback if no context exists."""
    ctx = get_current_trace_context()
    return ctx.span_id if ctx else "0000000000000000"
