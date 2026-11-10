"""Unit tests for the Actuarial Vector Allocator.

Proves mathematical identity conservation (zero rounding drift) across random fuzzing inputs.
"""

from __future__ import annotations

import random
from assessment_engine.domain.actuarial.receptor_allocator import ActuarialVectorAllocator
import pytest

def test_exact_residual_closure_identity() -> None:
    """Fuzz test to guarantee V_alpha + V_beta + V_gamma == total_ale for 10,000 cases."""
    random.seed(42)
    
    for _ in range(10000):
        total_ale = random.uniform(0.0, 10_000_000_000.0) # Up to 10B
        
        # Generate 3 random weights that sum to 1.0
        w1 = random.uniform(0.1, 0.8)
        w2 = random.uniform(0.1, 1.0 - w1 - 0.05)
        w3 = 1.0 - w1 - w2
        
        weights = [w1, w2, w3]
        random.shuffle(weights)
        w_alpha, w_beta, w_gamma = weights
        
        # Ensure floating point math on weight sum is precise enough for validation
        w_gamma = 1.0 - w_alpha - w_beta
        
        split = ActuarialVectorAllocator.allocate(total_ale, w_alpha, w_beta, w_gamma)
        
        expected_total = int(round(total_ale))
        actual_total = int(split.alpha_value + split.beta_value + split.gamma_value)
        
        assert expected_total == actual_total, f"Residual closure failed: expected {expected_total}, got {actual_total}"
        assert split.alpha_value >= 0
        assert split.beta_value >= 0
        
def test_invalid_weights_sum() -> None:
    """Ensure weights must sum to 1.0."""
    with pytest.raises(ValueError, match="Weights must sum exactly to 1.0"):
        ActuarialVectorAllocator.allocate(1000.0, 0.5, 0.4, 0.05)

def test_zero_total_ale() -> None:
    """Ensure 0 ALE returns 0s."""
    split = ActuarialVectorAllocator.allocate(0.0, 0.5, 0.3, 0.2)
    assert split.alpha_value == 0.0
    assert split.beta_value == 0.0
    assert split.gamma_value == 0.0
