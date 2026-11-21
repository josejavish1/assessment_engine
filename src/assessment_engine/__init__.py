"""Assessment Engine namespace package."""

import os
from pathlib import Path

# Centralized GCP Service Account key resolution, ensuring it is configured 
# immediately upon import of any module in the package to prevent OAuth expiration errors (RefreshError).
_SA_KEY_PATH = Path.home() / ".secrets" / "sa-key.json"
if _SA_KEY_PATH.exists():
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(_SA_KEY_PATH)
