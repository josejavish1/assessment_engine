import subprocess
import unittest
from unittest.mock import MagicMock, patch

from assessment_engine.scripts.lib.remediation_playbooks import (
    check_git_status,
    clean_workspace,
)


class TestRemediationPlaybooks(unittest.TestCase):

    @patch("subprocess.run")
    def test_check_git_status_clean(self, mock_run):
        mock_run.return_value = MagicMock(stdout="", returncode=0)
        result = check_git_status()
        self.assertTrue(result.success)
        self.assertEqual(result.message, "Worktree is clean.")

    @patch("subprocess.run")
    def test_check_git_status_dirty(self, mock_run):
        mock_run.return_value = MagicMock(stdout="M file.txt", returncode=0)
        result = check_git_status()
        self.assertFalse(result.success)
        self.assertIn("Worktree is dirty", result.message)

    @patch("subprocess.run")
    def test_clean_workspace_success(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        result = clean_workspace()
        self.assertTrue(result.success)
        self.assertEqual(result.message, "Workspace cleaned successfully.")

    @patch("subprocess.run")
    def test_clean_workspace_failure(self, mock_run):
        mock_run.side_effect = subprocess.CalledProcessError(1, "git reset", stderr="Error resetting")
        result = clean_workspace()
        self.assertFalse(result.success)
        self.assertIn("Cleanup failed", result.message)

if __name__ == "__main__":
    unittest.main()
