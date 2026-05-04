import unittest
import json
import shutil
from pathlib import Path
from assessment_engine.scripts.lib.apex_sentinel import ApexSentinel

class TestApexInfrastructure(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path("working/test_apex_infra")
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
        self.test_dir.mkdir(parents=True)

    def test_ledger_persistence_and_recovery(self):
        """Verifica que el Sentinel guarda transacciones y recupera el estado tras un reinicio."""
        sentinel = ApexSentinel(self.test_dir, budget_limit=10.0)
        sentinel.log_transaction("TASK-1", "started", {"info": "test"})
        sentinel.log_transaction("TASK-1", "success", {}, cost=1.50)
        
        # Simular reinicio del sistema creando un nuevo Sentinel sobre el mismo directorio
        new_sentinel = ApexSentinel(self.test_dir, budget_limit=10.0)
        
        self.assertEqual(new_sentinel.total_cost, 1.50)
        self.assertEqual(new_sentinel.get_task_status("TASK-1"), "success")
        self.assertIsNone(new_sentinel.get_task_status("TASK-NON-EXISTENT"))

    def test_circuit_breaker(self):
        """Verifica que el Sentinel detiene la ejecución si se supera el presupuesto."""
        sentinel = ApexSentinel(self.test_dir, budget_limit=1.0)
        
        # Transacción dentro del límite
        sentinel.log_transaction("T1", "event", {}, cost=0.5)
        
        # Esta transacción debe disparar el Circuit Breaker
        with self.assertRaises(RuntimeError) as cm:
            sentinel.log_transaction("T2", "event", {}, cost=0.6)
        
        self.assertIn("CIRCUIT BREAKER", str(cm.exception))

if __name__ == "__main__":
    unittest.main()
