"""
SRE Operational Constants & Fault-Tolerant Parameters (Tier-1 SOTA 2026).
Eliminates scattered raw magic numbers in sleeps, timeouts, jitter backoffs, and retries.
All parameters can be calibrated via environment variables for CI/CD, local, or production.
"""

from __future__ import annotations

import os

# Configure grace periods and startup delays.
DEFAULT_RETRY_BACKOFF_SEC: float = float(os.environ.get("SRE_RETRY_BACKOFF_SEC", "0.5"))
PROCESS_STARTUP_GRACE_SEC: float = float(os.environ.get("SRE_PROCESS_STARTUP_GRACE_SEC", "1.0"))
HEARTBEAT_INTERVAL_SEC: float = float(os.environ.get("SRE_HEARTBEAT_INTERVAL_SEC", "0.1"))
POLLING_INTERVAL_SEC: float = float(os.environ.get("SRE_POLLING_INTERVAL_SEC", "0.2"))

# Timeouts de red y peticiones HTTP
HTTP_GATEWAY_TIMEOUT_SEC: float = float(os.environ.get("SRE_HTTP_GATEWAY_TIMEOUT_SEC", "30.0"))
HTTP_MAX_RETRY_ATTEMPTS: int = int(os.environ.get("SRE_HTTP_MAX_RETRY_ATTEMPTS", "4"))
HEALTH_PROBE_TIMEOUT_SEC: float = float(os.environ.get("SRE_HEALTH_PROBE_TIMEOUT_SEC", "5.0"))

DEFAULT_CONTROL_PLANE_URL: str = os.environ.get("CONTROL_PLANE_URL", "http://127.0.0.1:8000")
DEFAULT_UX_CRITIC_URL: str = os.environ.get("UX_CRITIC_TARGET_URL", "http://127.0.0.1:8088")
DEFAULT_MEILI_URL: str = os.environ.get("MEILI_HTTP_URL", "http://127.0.0.1:7700")
