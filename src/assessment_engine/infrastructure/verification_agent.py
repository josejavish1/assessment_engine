from __future__ import annotations

import logging
from pathlib import Path
from typing import List

logger = logging.getLogger(__name__)


class VerificationAgent:
    """Abstract base class for agents that verify file modifications.

    This class provides a common interface for verification agents. Subclasses are
    expected to inherit from `VerificationAgent` and implement the `verify_changes`
    classmethod to provide specific validation logic, such as integrity checks,
    format validation, or semantic analysis.
    """

    @classmethod
    def verify_changes(cls, request_dir: Path, changed_files: List[str]) -> None:
        """Verifies modifications for a set of files within a request directory.

        This method serves as an interface and must be implemented by a subclass to
        contain specific validation logic.

        Args:
            request_dir (pathlib.Path): The path to the root directory containing the
                files to be verified.
            changed_files (List[str]): A list of file paths, relative to `request_dir`,
                that have been modified.

        Raises:
            ValueError: If any file modification fails the subclass's validation
                criteria.
        """
        pass
