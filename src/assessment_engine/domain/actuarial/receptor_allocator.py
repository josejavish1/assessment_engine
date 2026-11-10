"""Actuarial Vector Allocator for Open FAIR Economic Receptors.

Enforces zero-drift mathematical residual closure across the three 
canonical loss vectors (Alpha, Beta, Gamma) for any given economic receptor.
"""

from __future__ import annotations

import math
from typing import NamedTuple


class ReceptorVectorSplit(NamedTuple):
    """Immutable representation of exact vector closure."""
    alpha_value: float
    beta_value: float
    gamma_value: float


class ActuarialVectorAllocator:
    """Enforces mathematical residual closure for 3-part Open FAIR vectors."""

    @classmethod
    def allocate(
        cls,
        total_ale: float,
        weight_alpha: float,
        weight_beta: float,
        weight_gamma: float,
    ) -> ReceptorVectorSplit:
        """
        Decomposes total_ale into alpha, beta, and gamma strictly respecting:
        alpha + beta + gamma == total_ale (rounded to nearest integer).
        Weights must sum exactly to 1.0.
        """
        if abs(weight_alpha + weight_beta + weight_gamma - 1.0) > 1e-5:
            raise ValueError(
                f"Weights must sum exactly to 1.0. Got: {weight_alpha + weight_beta + weight_gamma}"
            )

        if total_ale < 0:
            raise ValueError("total_ale cannot be negative.")

        total_int = int(round(total_ale))

        if total_int == 0:
            return ReceptorVectorSplit(0.0, 0.0, 0.0)

        raw_alloc = {
            "alpha": total_int * weight_alpha,
            "beta": total_int * weight_beta,
            "gamma": total_int * weight_gamma,
        }
        floors = {k: math.floor(v) for k, v in raw_alloc.items()}
        shortfall = total_int - sum(floors.values())

        remainders = sorted(
            raw_alloc.keys(),
            key=lambda k: raw_alloc[k] - floors[k],
            reverse=True,
        )
        for i in range(shortfall):
            floors[remainders[i]] += 1

        return ReceptorVectorSplit(
            alpha_value=float(floors["alpha"]),
            beta_value=float(floors["beta"]),
            gamma_value=float(floors["gamma"]),
        )
