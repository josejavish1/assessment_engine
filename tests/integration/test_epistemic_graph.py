import shutil
from pathlib import Path

from assessment_engine.infrastructure.epistemic_graph import EpistemicGraph


def test_epistemic_graph_persistence_and_cqrs():
    # --- ARRANGE ---
    client_id = "test_client_v3"
    working_dir = Path(f"working/{client_id}")
    if working_dir.exists():
        shutil.rmtree(working_dir)

    # 1. First run: inject triples
    graph = EpistemicGraph(client_id=client_id)
    # --- ACT ---
    graph.inject_triple("AWS", "PROVIDER_TYPE", "CLOUD", "TEST", 1.0)

    truth = graph.resolve_truth()
    # --- ASSERT ---
    assert "AWS" in truth
    assert truth["AWS"]["PROVIDER_TYPE"]["value"] == "CLOUD"

    # 2. Check ledger file exists
    assert graph.ledger_path.exists()

    # 3. Second run: reconstruct from ledger
    graph2 = EpistemicGraph(client_id=client_id)
    truth2 = graph2.resolve_truth()
    # --- ASSERT ---
    assert "AWS" in truth2
    assert truth2["AWS"]["PROVIDER_TYPE"]["value"] == "CLOUD"

    # 4. Time travel check (not very deep, but basic)
    # Inject an update
    import time

    time.sleep(0.01)
    graph2.inject_triple("AWS", "PROVIDER_TYPE", "HYBRID", "TEST_UPDATE", 1.0)
    truth_now = graph2.resolve_truth()
    assert truth_now["AWS"]["PROVIDER_TYPE"]["value"] == "HYBRID"

    # Clean up
    if working_dir.exists():
        shutil.rmtree(working_dir)


if __name__ == "__main__":
    test_epistemic_graph_persistence_and_cqrs()
    print("✅ EpistemicGraph V3 test passed!")
