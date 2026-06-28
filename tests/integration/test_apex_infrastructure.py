import shutil

# --- ARRANGE ---
import unittest
from pathlib import Path

from assessment_engine.infrastructure.apex_sentinel import ApexSentinel


class TestApexInfrastructure(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path("working/test_apex_infra")
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
        self.test_dir.mkdir(parents=True)

    def tearDown(self):
        if hasattr(self, "test_dir") and self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_ledger_persistence_and_recovery(self):
        """Verify that the Sentinel logs transactions and recovers state after a restart."""
        sentinel = ApexSentinel(self.test_dir, budget_limit=10.0)
        sentinel.log_transaction("TASK-1", "started", {"info": "test"})
        sentinel.log_transaction("TASK-1", "success", {}, cost=1.50)

        # Simulate system restart by creating a new Sentinel over the same directory
        new_sentinel = ApexSentinel(self.test_dir, budget_limit=10.0)

        self.assertEqual(new_sentinel.total_cost, 1.50)
        self.assertEqual(new_sentinel.get_task_status("TASK-1"), "success")
        self.assertIsNone(new_sentinel.get_task_status("TASK-NON-EXISTENT"))

    def test_get_task_status_missing_ledger(self):
        """Verify that get_task_status returns None when the ledger file does not exist."""
        sentinel = ApexSentinel(self.test_dir, budget_limit=10.0)
        if sentinel.ledger_path.exists():
            sentinel.ledger_path.unlink()
        self.assertIsNone(sentinel.get_task_status("TASK-1"))

    def test_circuit_breaker(self):
        """Verify that the Sentinel halts execution if the budget is exceeded."""
        sentinel = ApexSentinel(self.test_dir, budget_limit=1.0)

        # Transaction within the budget limit
        sentinel.log_transaction("T1", "event", {}, cost=0.5)

        # This transaction must trigger the Circuit Breaker
        with self.assertRaises(RuntimeError) as cm:
            sentinel.log_transaction("T2", "event", {}, cost=0.6)

        self.assertIn("CIRCUIT BREAKER", str(cm.exception))

    def test_corrupted_ledger_recovery(self):
        """Verify that the Sentinel successfully loads state even if the ledger is corrupted."""
        sentinel = ApexSentinel(self.test_dir, budget_limit=10.0)
        sentinel.log_transaction("TASK-1", "started", {}, cost=1.0)

        # Corrupt the ledger by appending a malformed line
        with sentinel.ledger_path.open("a", encoding="utf-8") as f:
            f.write("{\n")  # Unclosed JSON
            f.write('{"task_id": "TASK-2", "event": "success", "cost_usd": 2.5}\n')

        # Re-initialize sentinel to load the corrupted ledger
        new_sentinel = ApexSentinel(self.test_dir, budget_limit=10.0)
        self.assertEqual(new_sentinel.total_cost, 3.5)

    def test_get_task_status_corrupted_ledger(self):
        """Verify that get_task_status ignores malformed JSON or keys-missing lines."""
        sentinel = ApexSentinel(self.test_dir, budget_limit=10.0)
        sentinel.log_transaction("TASK-1", "started", {}, cost=1.0)

        # Append malformed JSON and missing-key JSON lines
        with sentinel.ledger_path.open("a", encoding="utf-8") as f:
            f.write("MALFORMED_JSON_LINE\n")
            f.write('{"something_else": "test"}\n')  # Missing task_id
            f.write('{"task_id": "TASK-1", "event": "completed", "cost_usd": 2.0}\n')

        status = sentinel.get_task_status("TASK-1")
        self.assertEqual(status, "completed")


if __name__ == "__main__":
    unittest.main()
