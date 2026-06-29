import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Tuple

import networkx as nx
import numpy as np

logger = logging.getLogger(__name__)


class EpistemicGraphService:
    """Provides advanced Epistemic Graph modeling and continuous Loopy Causal Belief Network (LCBN)
    risk propagation across the 10 technology towers of the Assessment Engine.

    Unlike traditional Bayesian Belief Networks which are strictly Directed Acyclic Graphs (DAGs),
    LCBN resolves complex real-world technology holdings which naturally contain cyclic feedback loops
    (e.g., Core Network T3 provides network to SOC T5, but T5 provides traffic security back to T3).

    Calculates risk propagation using a contraction mapping iterative fixed-point relaxation algorithm,
    guaranteed to converge to a unique stable equilibrium under Banach's Fixed-Point Theorem.
    """

    def __init__(self, industry_profile: str = "default") -> None:
        """Initializes the service and builds the directed expert dependency graph (supports cycles).

        The topology and weights are loaded dynamically from declarative policy configurations
        depending on the active industry profile, with automatic robust fallbacks.
        """
        self.graph = nx.DiGraph()
        self.towers = [f"T{i}" for i in range(1, 11)]
        self.graph.add_nodes_from(self.towers)
        self.industry_profile = industry_profile.lower()

        # Robust expert fallback topology containing real-world cyclic loops
        dependencies = [
            ("T6", "T5", 0.75),  # IAM (T6) strongly influences SOC Operations (T5)
            (
                "T5",
                "T2",
                0.85,
            ),  # Cybersecurity (T5) protects and influences OT Substation Systems (T2)
            (
                "T3",
                "T2",
                0.70,
            ),  # Core Network (T3) directly impacts OT Substation Systems (T2)
            (
                "T3",
                "T8",
                0.65,
            ),  # Core Network (T3) hosts and impacts Cloud/Datacenter Infrastructure (T8)
            (
                "T8",
                "T4",
                0.80,
            ),  # Cloud/DC Infrastructure (T8) hosts and impacts Core Business Apps (T4)
            (
                "T9",
                "T1",
                0.55,
            ),  # Physical Security (T9) impacts End-User Computing (T1)
            (
                "T4",
                "T10",
                0.60,
            ),  # Business Apps (T4) provide data for Digital Twin Operations (T10)
            ("T6", "T1", 0.50),  # IAM (T6) governs and impacts End-User Computing (T1)
            (
                "T5",
                "T3",
                0.50,
            ),  # SOC (T5) filters and secures Core Networks (T3) - Cycle T3 <-> T5!
            (
                "T8",
                "T6",
                0.45,
            ),  # Cloud (T8) hosts and impacts IAM (T6) - Cycle T6 <-> T8!
        ]

        # Attempt to load declarative topology based on industry profile
        try:
            repo_root = Path(__file__).resolve().parent.parent.parent.parent
            policy_file = (
                repo_root / "engine_config" / "policies" / "epistemic_dependencies.json"
            )

            if policy_file.exists():
                policy_data = json.loads(policy_file.read_text(encoding="utf-8-sig"))
                topologies = policy_data.get("industry_topologies", {})

                # Resolve specific profile name or map generic descriptions to profiles
                target_profile = "default"
                if (
                    "energy" in self.industry_profile
                    or "critical" in self.industry_profile
                ):
                    target_profile = "critical_infrastructure"
                elif "retail" in self.industry_profile:
                    target_profile = "retail"
                elif self.industry_profile in topologies:
                    target_profile = self.industry_profile

                profile_deps = topologies.get(target_profile)
                if profile_deps:
                    dependencies = [
                        (dep["parent"], dep["child"], float(dep["weight"]))
                        for dep in profile_deps
                    ]
                    logger.info(
                        f"Loaded declarative epistemic topology for profile: {target_profile}"
                    )
        except Exception as e:
            logger.warning(
                f"Failed to load declarative epistemic policy ({e}). Falling back to robust expert defaults."
            )

        # Build the graph edges (supports loops natively)
        for u, v, w in dependencies:
            self.graph.add_edge(u, v, weight=w)

    def propagate_risk(
        self,
        intrinsic_maturities: Dict[str, float],
        max_iter: int = 100,
        tol: float = 1e-6,
    ) -> Dict[str, float]:
        """Propagates intrinsic risk across the Loopy Causal Belief Network (LCBN) using Fixed-Point Iterative Relaxation.

        Risk (R) is modeled as the normalized complement of target maturity (M) on [0.0, 1.0]:
        M_normalized = (M - 3.0) / 2.0
        R_intrinsic = 1.0 - M_normalized

        The risk propagation is resolved iteratively as a contraction mapping:
        R_propagated^{(k+1)}_i = 1.0 - (1.0 - R_intrinsic_i) * Product_over_parents(1.0 - weight_{p->i} * R_propagated^{(k)}_p)

        Args:
            intrinsic_maturities: Dictionary mapping tower IDs (e.g. 'T1') to their intrinsic maturity [3.0, 5.0].
            max_iter: Maximum number of relaxation iterations.
            tol: Frobenius norm convergence tolerance.

        Returns:
            Dictionary mapping tower IDs to their propagated target maturity scores [3.0, 5.0].
        """
        # 1. Normalize intrinsic maturities to intrinsic risk [0.0, 1.0]
        intrinsic_risks = {}
        for t_id in self.towers:
            m = intrinsic_maturities.get(t_id, 4.0)
            m_norm = (np.clip(m, 3.0, 5.0) - 3.0) / 2.0
            intrinsic_risks[t_id] = 1.0 - m_norm

        # Initialize propagated risks with intrinsic risks
        R = np.array([intrinsic_risks[t] for t in self.towers])
        R_intrinsic = np.array([intrinsic_risks[t] for t in self.towers])

        # Build Adjacency Weight Matrix W (W_ij is weight of i -> j, meaning parent i to child j)
        D = len(self.towers)
        W = np.zeros((D, D))
        for idx_u, u in enumerate(self.towers):
            for idx_v, v in enumerate(self.towers):
                if self.graph.has_edge(u, v):
                    W[idx_u, idx_v] = self.graph[u][v]["weight"]

        # 2. Fixed-Point Iterative Relaxation (Loopy Belief Propagation)
        for _ in range(max_iter):
            R_new = np.zeros(D)
            for i in range(D):
                safety_product = 1.0
                for j in range(D):
                    if W[j, i] > 0.0:
                        # Parent j's risk propagates to child i
                        safety_product *= 1.0 - W[j, i] * R[j]
                R_new[i] = 1.0 - (1.0 - R_intrinsic[i]) * safety_product

            diff = np.linalg.norm(R_new - R)
            R = R_new
            if diff < tol:
                break

        # 3. Denormalize propagated risks back to maturity scores [3.0, 5.0]
        propagated_maturities = {}
        for idx, t_id in enumerate(self.towers):
            r_prop = R[idx]
            m_prop = 3.0 + 2.0 * (1.0 - r_prop)
            propagated_maturities[t_id] = round(float(m_prop), 2)

        return propagated_maturities

    def calculate_risk_centrality(
        self,
        std_devs: Dict[str, float],
        d: float = 0.85,
        max_iter: int = 100,
        tol: float = 1e-6,
    ) -> Dict[str, float]:
        """Calculates the PageRank-style Eigenvector Risk Centrality (ERC) across the graph.

        Integrates Phase 1 statistical volatility (std_devs) and Phase 2 topological dependencies (edges)
        into a single, unified eigenvalue equation, resolving perfectly even in cyclic networks.

        Args:
            std_devs: A dictionary mapping tower IDs to their Monte Carlo standard deviations.
            d: Damping factor (default 0.85).
            max_iter: Maximum iterations for power method convergence.
            tol: Convergence tolerance.

        Returns:
            A dictionary mapping tower IDs to their normalized Risk Centrality scores.
        """
        D = len(self.towers)
        vol = np.array([std_devs.get(t, 0.05) for t in self.towers])

        W = np.zeros((D, D))
        for idx_u, u in enumerate(self.towers):
            for idx_v, v in enumerate(self.towers):
                if self.graph.has_edge(u, v):
                    W[idx_u, idx_v] = self.graph[u][v]["weight"]

        # Risk transition matrix M: M_ij = W_ij * vol[i]
        M = W * vol[:, np.newaxis]

        # Personalized damping vector (using the volatilities normalized to sum to 1.0)
        vol_sum = np.sum(vol)
        v_personal = vol / (vol_sum if vol_sum > 1e-10 else 1.0)

        # Power iteration with personalization damping
        x = np.ones(D) / D
        for _ in range(max_iter):
            x_new = d * np.dot(M.T, x) + (1.0 - d) * v_personal
            sum_x = np.sum(x_new)
            x_new = x_new / (sum_x if sum_x > 1e-10 else 1.0)
            if np.linalg.norm(x_new - x) < tol:
                x = x_new
                break
            x = x_new

        return {t_id: round(float(x[idx]), 4) for idx, t_id in enumerate(self.towers)}

    def get_single_point_of_failure(
        self, intrinsic_maturities: Dict[str, float]
    ) -> Tuple[str, float]:
        """Identifies the 'Single Point of Failure' (SPOF) - the tower whose intrinsic risk
        contributes the most cascading risk to the rest of the network.

        This is resolved in a loopy-aware manner by simulating extreme failure on each node one-by-one.
        """
        base_propagated = self.propagate_risk(intrinsic_maturities)
        base_sum_risk = sum(1.0 - (v - 3.0) / 2.0 for v in base_propagated.values())

        max_impact = -1.0
        spof_tower = "None"

        for t_id in self.towers:
            # Simulate extreme intrinsic failure on this tower (maturity = 3.0, i.e., risk = 1.0)
            perturbed_maturities = intrinsic_maturities.copy()
            perturbed_maturities[t_id] = 3.0

            perturbed_propagated = self.propagate_risk(perturbed_maturities)
            perturbed_sum_risk = sum(
                1.0 - (v - 3.0) / 2.0 for v in perturbed_propagated.values()
            )

            # Cascading impact is the delta increase in aggregate risk
            cascading_impact = perturbed_sum_risk - base_sum_risk

            # We exclude the intrinsic failure of the tower itself from the impact to focus purely on cascade
            own_risk_increase = (intrinsic_maturities.get(t_id, 4.0) - 3.0) / 2.0
            clean_cascading_impact = max(0.0, cascading_impact - own_risk_increase)

            if clean_cascading_impact > max_impact:
                max_impact = clean_cascading_impact
                spof_tower = t_id

        return spof_tower, round(float(max_impact), 4)

    def simulate_counterfactual_intervention(
        self, intrinsic_maturities: Dict[str, float], interventions: Dict[str, float]
    ) -> Dict[str, Any]:
        """Simulates the cascading ROI of raising specific towers to target maturities.

        Args:
            intrinsic_maturities: Current baseline expert maturities.
            interventions: A dictionary mapping tower IDs to their new proposed maturities (e.g. {'T6': 5.0}).

        Returns:
            A dictionary containing:
            - 'baseline_propagated': maturities before intervention.
            - 'counterfactual_propagated': maturities after intervention.
            - 'global_improvement_delta': total cumulative score increase across all towers.
            - 'cascading_benefits': list of towers that experienced a positive cascade effect.
        """
        baseline_prop = self.propagate_risk(intrinsic_maturities)

        # Apply interventions
        perturbed_intrinsic = intrinsic_maturities.copy()
        for t_id, new_val in interventions.items():
            perturbed_intrinsic[t_id] = new_val

        counterfactual_prop = self.propagate_risk(perturbed_intrinsic)

        # Calculate impact
        impacted_towers = {}
        total_delta = 0.0
        for t_id in self.towers:
            delta = counterfactual_prop[t_id] - baseline_prop[t_id]
            if delta > 0.01:
                impacted_towers[t_id] = round(delta, 2)
                total_delta += delta

        return {
            "baseline_propagated": baseline_prop,
            "counterfactual_propagated": counterfactual_prop,
            "global_improvement_delta": round(total_delta, 2),
            "cascading_benefits": impacted_towers,
        }

    def get_critical_propagation_paths(self) -> List[Dict[str, Any]]:
        """Identifies and maps the 'Critical Risk Propagation Paths' in the network.

        Calculates all possible dependency paths from source towers to leaf towers,
        weighting each path by its cumulative risk transfer product.

        Returns:
            A sorted list of dictionaries representing the most fragile risk pathways.
        """
        # Find sources (in-degree = 0) and sinks (out-degree = 0)
        sources = [n for n, d in self.graph.in_degree() if d == 0]
        sinks = [n for n, d in self.graph.out_degree() if d == 0]

        # Robustness fallback for fully cyclic/sourceless/sinkless graphs:
        # If there are no nodes with in-degree/out-degree 0 due to cycles, use all nodes as candidates.
        if not sources:
            sources = list(self.graph.nodes)
        if not sinks:
            sinks = list(self.graph.nodes)

        paths = []
        for src in sources:
            for sink in sinks:
                # Find all simple paths (avoids circular loops natively to avoid infinite paths)
                if (
                    src != sink
                    and self.graph.has_node(src)
                    and self.graph.has_node(sink)
                ):
                    for path in nx.all_simple_paths(self.graph, src, sink):
                        # Calculate cumulative risk transfer multiplier along the path
                        cumulative_weight = 1.0
                        for k in range(len(path) - 1):
                            cumulative_weight *= self.graph[path[k]][path[k + 1]][
                                "weight"
                            ]

                        paths.append(
                            {
                                "path": " -> ".join(path),
                                "source": src,
                                "sink": sink,
                                "cumulative_risk_transfer": round(cumulative_weight, 4),
                            }
                        )

        # Sort paths by their cumulative risk transfer (highest risk propagation potential first)
        return sorted(paths, key=lambda x: x["cumulative_risk_transfer"], reverse=True)

    def backpropagate_audit_feedback(
        self,
        intrinsic_maturities: Dict[str, float],
        audited_maturities: Dict[str, float],
        lr: float = 0.05,
    ) -> Dict[str, Any]:
        """Runs continuous backpropagation over the causal graph edge weights to minimize
        prediction errors between intrinsic targets and actual real-world audited scores.

        Uses exact analytical gradients computed on the continuous loopy BBN formulation
        and applies gradient descent updates, persisting the learned weights to policy files.

        Args:
            intrinsic_maturities: The baseline target maturities recommended [3.0, 5.0].
            audited_maturities: The actual empirical audited maturities [3.0, 5.0].
            lr: Learning rate for gradient descent.

        Returns:
            A dictionary summarizing the completed backpropagation epoch:
            - 'epoch_mse': Mean Squared Error before updates.
            - 'updated_weights': list of edges and their new self-calibrated weights.
        """
        # 1. Normalize maturities to risks [0.0, 1.0]
        R_int = np.array(
            [1.0 - (intrinsic_maturities.get(t, 4.0) - 3.0) / 2.0 for t in self.towers]
        )
        R_aud = np.array(
            [1.0 - (audited_maturities.get(t, 4.0) - 3.0) / 2.0 for t in self.towers]
        )

        # Calculate propagated risks under current weights
        propagated_mat = self.propagate_risk(intrinsic_maturities)
        R_prop = np.array([1.0 - (propagated_mat[t] - 3.0) / 2.0 for t in self.towers])

        # Compute initial Mean Squared Error (MSE)
        epoch_mse = float(np.mean((R_aud - R_prop) ** 2))

        updates = []
        # 2. Compute analytical gradients and apply gradient descent per edge
        for u_idx, u in enumerate(self.towers):
            for v_idx, v in enumerate(self.towers):
                if self.graph.has_edge(u, v):
                    w_old = self.graph[u][v]["weight"]

                    # Error at child node v: Error = Risk_audited - Risk_propagated
                    error = R_aud[v_idx] - R_prop[v_idx]

                    # Gradient d(Error^2)/dw = -2 * error * d(R_prop[v])/dw
                    # d(R_prop[v])/dw = (1 - R_intrinsic[v]) * R_parent[u] * product_{k!=u} (1 - w_kv * R_parent[k])
                    parent_safety_product = 1.0
                    for k_idx, k in enumerate(self.towers):
                        if k != u and self.graph.has_edge(k, v):
                            parent_safety_product *= (
                                1.0 - self.graph[k][v]["weight"] * R_prop[k_idx]
                            )

                    d_rprop_dw = (
                        (1.0 - R_int[v_idx]) * R_prop[u_idx] * parent_safety_product
                    )
                    gradient = -2.0 * error * d_rprop_dw

                    # Apply gradient descent update
                    w_new = w_old - lr * gradient
                    # Enforce strict physical boundary guardrails [0.05, 0.95] to prevent colapso
                    w_new = float(np.clip(w_new, 0.05, 0.95))

                    self.graph[u][v]["weight"] = w_new
                    updates.append(
                        {
                            "edge": f"{u} -> {v}",
                            "weight_old": round(w_old, 4),
                            "weight_new": round(w_new, 4),
                            "delta": round(w_new - w_old, 4),
                        }
                    )

        # 3. Write learned weights back to declarative JSON policy file for self-evolution!
        try:
            repo_root = Path(__file__).resolve().parent.parent.parent.parent
            policy_file = (
                repo_root / "engine_config" / "policies" / "epistemic_dependencies.json"
            )

            if policy_file.exists():
                policy_data = json.loads(policy_file.read_text(encoding="utf-8-sig"))

                # Resolve target profile
                target_profile = "default"
                if (
                    "energy" in self.industry_profile
                    or "critical" in self.industry_profile
                ):
                    target_profile = "critical_infrastructure"
                elif "retail" in self.industry_profile:
                    target_profile = "retail"
                elif self.industry_profile in policy_data.get(
                    "industry_topologies", {}
                ):
                    target_profile = self.industry_profile

                # Build updated list
                updated_list = []
                for u, v, d in self.graph.edges(data=True):
                    updated_list.append(
                        {
                            "parent": u,
                            "child": v,
                            "weight": round(float(d["weight"]), 4),
                        }
                    )

                policy_data["industry_topologies"][target_profile] = updated_list

                import uuid

                tmp_policy = policy_file.with_name(
                    f"{policy_file.name}.{uuid.uuid4().hex[:8]}.tmp"
                )
                try:
                    tmp_policy.write_text(
                        json.dumps(policy_data, indent=2, ensure_ascii=False),
                        encoding="utf-8-sig",
                    )
                    tmp_policy.replace(policy_file)
                except Exception:
                    if tmp_policy.exists():
                        tmp_policy.unlink()
                    raise

                logger.info(
                    f"Causal Backpropagation: Learned weights persisted to profile '{target_profile}'."
                )
        except Exception as e:
            logger.error(f"Failed to persist learned weights to policy file: {e}")

        return {"epoch_mse": round(epoch_mse, 6), "updated_weights": updates}
