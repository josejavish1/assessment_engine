from assessment_engine.infrastructure.networkx_analyzer import NetworkXAnalyzer


def test_topological_sorting():
    # --- ARRANGE ---
    analyzer = NetworkXAnalyzer()

    # Define a simple strategic dependency
    # Project B depends on Project A
    # Project C depends on Project B
    triples = [
        {
            "subject": "PROJ_B",
            "predicate": "REQUIRES_PREREQUISITE",
            "object_val": "PROJ_A",
        },
        {
            "subject": "PROJ_C",
            "predicate": "REQUIRES_PREREQUISITE",
            "object_val": "PROJ_B",
        },
        {
            "subject": "PROJ_D",
            "predicate": "PROPOSES_INITIATIVE",
            "object_val": "Something else",
        },
    ]

    # --- ACT ---
    analyzer.build_graph_from_triples(triples)

    # Detect Cycles
    # --- ASSERT ---
    assert len(analyzer.detect_cycles()) == 0

    # Waves
    waves = analyzer.calculate_topological_waves()

    # PROJ_A should be in Wave 0 (no dependencies)
    # PROJ_B should be in Wave 1 (depends on A)
    # PROJ_C should be in Wave 2 (depends on B)

    print("Waves generated:", waves)

    # Check Wave 0
    wave0 = next(w for w in waves if "Wave 0" in w["wave"])
    assert "PROJ_A" in wave0["projects"]
    assert "PROJ_D" in wave0["projects"]  # D has no dependencies either

    # Check Wave 1
    wave1 = next(w for w in waves if "Wave 1" in w["wave"])
    assert "PROJ_B" in wave1["projects"]

    # Check Wave 2
    wave2 = next(w for w in waves if "Wave 2" in w["wave"])
    assert "PROJ_C" in wave2["projects"]


if __name__ == "__main__":
    test_topological_sorting()
    print("✅ NetworkXAnalyzer Topological Sorting test passed!")
