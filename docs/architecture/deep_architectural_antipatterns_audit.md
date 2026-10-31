# DEEP ARCHITECTURAL ANTI-PATTERNS AUDIT: ENTERPRISE ENGINE INTEGRITY

**Document Classification:** Internal Engineering Audit — Tier-1 Systems Architecture  
**Target System:** Enterprise Regulatory & Technical Assessment Engine  
**Audit Scope:** Domain Purity, Jurisdictional Topology, Epistemic Calibration, Runtime Immutability, and Multi-Lingual Determinism  
**Auditor Role:** Principal Systems Architect & Chief Software Auditor  

---

## 1. Executive Summary & Architectural Verdict

A forensic examination of the Assessment Engine codebase reveals a systemic divergence between the system’s target deployment profile (Fortune 500, Global Financial Institutions, Critical National Infrastructure) and its underlying implementation primitives. While the engine’s high-level orchestration and CEGAR (Counterexample-Guided Abstraction Refinement) pipeline exhibit modern structural intent, the foundational modules suffer from **epistemic fragility, domain-layer impurity, ontological conflation, and container-hostile state management**.

```
+-----------------------------------------------------------------------------------+
|                        CURRENT SYSTEMIC VULNERABILITY MATRIX                      |
+---------------------------+-------------------------------+-----------------------+
| Architectural Layer       | Observed Anti-Pattern         | Operational Impact    |
+---------------------------+-------------------------------+-----------------------+
| Domain Core               | Direct Filesystem I/O         | Breaks Functional Core|
| Policy & Governance       | Exception Swallowing          | Silent Compliance Drop|
| Jurisdictional Resolution | Surjective String Heuristics  | Legal Misattribution  |
| Intelligence Calibration  | Linear Numerology             | Uncalibrated Risk     |
| Runtime Persistence       | Source-Tree Mutation          | Pod CrashLoopBackOff  |
| Linguistic Verification   | Euro-Centric Stop-Word Sets   | CJK/RTL Hallucination |
+---------------------------+-------------------------------+-----------------------+
```

In a Tier-1 production environment, software does not fail merely through unhandled exceptions; it fails through **silent semantic corruption**. When an engine silently swallows a corrupted regulatory registry, maps an international industrial standard (`IEC 62443`) exclusively to the Federal Republic of Germany, or mutates its own source tree at runtime, it ceases to be a deterministic audit instrument and becomes an unquantified compliance liability.

This document catalogs every discovered architectural anti-pattern, establishes the exact failure modes under enterprise load and regulatory scrutiny, and specifies the mathematically rigorous, cloud-native target designs required to elevate the codebase to Tier-1 production standards.

---

## 2. Comprehensive Inventory of Deep Architectural Anti-Patterns

### 2.1. Anti-Pattern I: Surjective Jurisdictional Inference & Brittle Keyword Geolocation

* **Category:** Ontological Conflation / Primitive Obsession / Surjective Mapping Trap
* **Location:** `infrastructure/policies/jurisdictional_sovereignty.py` (Lines 100–125)

#### Forensic Code Evidence
```python
# infrastructure/policies/jurisdictional_sovereignty.py:100-125
for c in candidate_strings:
    c_clean = c.strip().upper()
    if c_clean in ("DE", "GERMANY", "DEUTSCHLAND", "BSI", "KRITIS", "NIS2", "IEC 62443"):
        inferred_codes.add("DE")
    elif c_clean in ("SA", "SAUDI ARABIA", "KSA", "NCA", "SAMA", "ECC", "CCRF"):
        inferred_codes.add("SA")
    elif c_clean in ("US", "USA", "UNITED STATES", "NIST", "FEDRAMP", "CMMC", "HIPAA", "SOX"):
        inferred_codes.add("US")
```

#### Architectural Critique
The resolution algorithm attempts to deduce an ISO-3166-1 alpha-2 sovereign state code by matching arbitrary uppercase substrings against a conflated set of geographic names, regulatory bodies, and technical standards. This implementation violates basic set-theoretic and domain-modeling principles:

1. **False Bijection between Standards and Sovereign States:** `IEC 62443` is an international series of standards developed by the ISA99 committee and adopted globally by the International Electrotechnical Commission. Hardcoding `IEC 62443 -> DE` forces any global manufacturing, energy, or maritime utility utilizing OT security standards into German legal jurisdiction (triggering *BSI IT-Grundschutz* and German *BDSG* mandates).
2. **Supranational Directive Collapse:** `NIS2` (Directive (EU) 2022/2555) is a supranational European Union directive applicable across all 27 EU Member States via national transposition laws (e.g., *BSIG* in Germany, *LPM* in France, *ACN* directives in Italy). Mapping `NIS2` exclusively to `DE` erases 26 sovereign jurisdictions and misapplies German federal law to French, Spanish, or Dutch entities.
3. **Extraterritorial Standard Conflation:** `NIST` (specifically the NIST CSF or SP 800-53) is used globally as a baseline technical taxonomy by organizations with zero nexus to United States jurisdiction. Inferring `US` legal sovereignty (and thereby invoking *CLOUD Act* or *FedRAMP* constraints) purely from the mention of `NIST` corrupts the legal threat model.

---

### 2.2. Anti-Pattern II: Heuristic Numerology & Uncalibrated Epistemic Scoring

* **Category:** Heuristic Numerology / Fake Precision / Epistemic Opacity
* **Location:** `infrastructure/client_intelligence.py` (Lines 121–135)

#### Forensic Code Evidence
```python
# infrastructure/client_intelligence.py:121-135
def estimate_confidence_score(self, source_count: int, specificity_signals: int, has_contradictions: bool) -> int:
    base = 40
    base += min(source_count, 3) * 10
    base += min(specificity_signals, 4) * 5
    if not has_contradictions and source_count > 0:
        base += 10
    return min(max(base, 0), 100)
```

#### Architectural Critique
This function purports to compute an epistemic confidence metric $[0, 100]$ representing the reliability of gathered client intelligence. In reality, it is an arbitrary linear combination of magic numbers (`40`, `10`, `5`, `10`) devoid of probabilistic grounding:

1. **Non-Zero Prior on Zero Evidence:** When `source_count == 0` and `specificity_signals == 0`, the function returns a baseline confidence of `40%`. In information theory and Bayesian inference, the absence of evidence must yield maximum entropy (zero confidence above a uniform prior), not a 40% assertion of certainty.
2. **Step-Function Saturation & Information Loss:** Capping `source_count` at `3` and `specificity_signals` at `4` means an intelligence dossier backed by 50 independent cryptographic audit logs and 20 architectural diagrams receives the exact same epistemic weight as one backed by 3 blog posts and 4 keyword matches.
3. **Boolean Contradiction Naive Penalty:** Treating `has_contradictions` as a binary toggle that merely withholds a `+10` bonus ignores source authority weighting. If three low-reliability web scrapes agree (`+30`) and one authoritative SEC 10-K filing contradicts them, the score only drops by 10 points (yielding `80%` confidence) despite a severe conflict with an authoritative primary source.

---

### 2.3. Anti-Pattern III: Impure Domain Layer & Direct Filesystem I/O Coupling

* **Category:** Leaky Domain I/O / Hexagonal Architecture Violation / Synchronous Blocking I/O
* **Location:** `domain/taxonomy_resolver.py`

#### Forensic Code Evidence
```python
# domain/taxonomy_resolver.py
from pathlib import Path
import json

class TaxonomyResolver:
    def __init__(self, config_path: str = "engine_config/taxonomy_multilingual.json"):
        self.config_path = Path(config_path)
        self._taxonomy_data = self._load_from_disk()

    def _load_from_disk(self) -> dict:
        if not self.config_path.exists():
            return {}
        return json.loads(self.config_path.read_text(encoding="utf-8"))
```

#### Architectural Critique
In Clean, Hexagonal (Ports and Adapters), and Functional Core / Imperative Shell architectures, the `domain/` layer must consist strictly of pure, side-effect-free business logic operating on in-memory value objects and entities. 

1. **Inversion of Control (IoC) Violation:** `TaxonomyResolver` hardcodes a relative filesystem path (`"engine_config/taxonomy_multilingual.json"`) and executes synchronous POSIX filesystem calls (`Path.exists()`, `Path.read_text()`) inside its constructor.
2. **Current Working Directory (CWD) Fragility:** Relative paths resolve against the OS process's current working directory (`os.getcwd()`). If a worker process, Celery daemon, or test runner is invoked from a subdirectory or parent workspace, `self.config_path.exists()` evaluates to `False`, silently initializing the domain resolver with an empty dictionary `{}`.
3. **Unbounded I/O Amplification:** Instantiating `TaxonomyResolver` per request or per domain validation cycle triggers repetitive disk reads and JSON deserialization on the main execution thread, introducing severe I/O wait latency under concurrent async workloads (e.g., FastAPI / `asyncio` event loops).

---

### 2.4. Anti-Pattern IV: Runtime Source-Tree Mutation & Container Immutability Violation

* **Category:** Runtime Package Mutation / Stateful Ephemeral Storage / Race Condition Hazard
* **Location:** `infrastructure/policies/jurisdictional_sovereignty.py`

#### Forensic Code Evidence
```python
# infrastructure/policies/jurisdictional_sovereignty.py
DYNAMIC_DIR = Path("engine_config/policies/jurisdictions_dynamic")

def persist_synthesized_jurisdiction(profile: JurisdictionalProfile) -> None:
    DYNAMIC_DIR.mkdir(parents=True, exist_ok=True)
    target_file = DYNAMIC_DIR / f"{profile.country_code.lower()}.json"
    with open(target_file, "w", encoding="utf-8") as f:
        json.dump(profile.model_dump(), f, indent=2)
```

#### Architectural Critique
During Just-In-Time (JIT) policy synthesis, the engine writes newly generated jurisdictional JSON artifacts directly into `engine_config/policies/jurisdictions_dynamic/` inside the application's source tree.

1. **Read-Only Root Filesystem Failure:** Enterprise Kubernetes deployments governed by CIS Benchmarks, NSA/CISA Kubernetes Hardening Guides, or FedRAMP High baselines enforce `securityContext.readOnlyRootFilesystem: true` on all application containers. Executing `DYNAMIC_DIR.mkdir()` or `open(..., "w")` inside the container image filesystem immediately raises an unhandled `PermissionError: [Errno 30] Read-only file system`, crashing the worker pod.
2. **Multi-Process File Corruption (TOCTOU & Torn Writes):** Calling `open(target_file, "w")` without POSIX file locking (`fcntl.flock`) or atomic rename semantics (`os.replace` via temporary file) means two concurrent async workers or Gunicorn processes synthesizing the same jurisdiction simultaneously will interleave their byte streams, producing a truncated or syntactically invalid JSON file on disk.
3. **Split-Brain Ephemeral State:** In a horizontally scaled deployment (e.g., $N$ stateless replicas behind an Envoy load balancer), writing a file to Pod A's local overlay filesystem makes that synthesized policy invisible to Pods B through $N$, and permanently destroys the state upon Pod A's next eviction or rolling deployment.

---

### 2.5. Anti-Pattern V: Euro-Centric Linguistic Guardrails & Silent Orthographic Bypass

* **Category:** Incomplete Linguistic Domain Modeling / Orthographic Bias / Silent Verification Bypass
* **Location:** `domain/linguistic_guardrail.py`

#### Forensic Code Evidence
```python
# domain/linguistic_guardrail.py
STOP_WORDS = {
    "en": {"the", "and", "of", "to", "in", "is", "for", "with", "on", "that"},
    "es": {"de", "la", "que", "el", "en", "y", "a", "los", "del", "se"},
    "de": {"der", "die", "und", "in", "den", "von", "zu", "das", "mit", "sich"},
    "fr": {"de", "la", "le", "et", "les", "des", "en", "un", "du", "une"}
}

def verify_language_consistency(text: str, target_lang: str) -> bool:
    words = set(text.lower().split())
    expected_stops = STOP_WORDS.get(target_lang, set())
    if not expected_stops:
        return True  # Silent bypass for unsupported languages
    overlap = words.intersection(expected_stops)
    return len(overlap) >= 2
```

#### Architectural Critique
The engine claims global enterprise support across MENA (Saudi Arabia, UAE), APAC (Japan, China, South Korea), and LATAM (Brazil), yet its linguistic verification guardrail relies on a naive whitespace-tokenized stop-word intersection covering only four Western European languages (`en`, `es`, `de`, `fr`).

1. **Unconditional Verification Bypass (`return True`):** For any language outside the four hardcoded keys—such as Arabic (`ar`), Japanese (`ja`), Mandarin Chinese (`zh`), Portuguese (`pt`), or Italian (`it`)—`STOP_WORDS.get(target_lang, set())` returns an empty set, causing `if not expected_stops: return True` to immediately pass validation. If an LLM hallucinates and outputs English text for a Saudi Arabian (`ar`) or Japanese (`ja`) regulatory audit, the guardrail reports `True` (valid).
2. **Failure on Unsegmented / Scriptio Continua Scripts:** `text.lower().split()` splits on ASCII whitespace. Japanese (`ja`) and Mandarin Chinese (`zh`) do not use whitespace between words; they are continuous character streams. Even if stop-words were added to `STOP_WORDS["ja"]`, `.split()` would produce full sentences as single tokens, causing `.intersection()` to evaluate to `0` and falsely reject valid Japanese text.
3. **Morphological Clitic Blindness in Abjads:** In Arabic (`ar`), prepositions and conjunctions (such as `و` *wa-*, `ب` *bi-*, `ل` *li-*, and the definite article `ال` *al-*) are orthographically fused as prefixes to the following noun, while pronouns attach as suffixes. Whitespace tokenization without morphological segmentation or Unicode script-block analysis fails completely.

---

### 2.6. Anti-Pattern VI: Silent Exception Swallowing on Critical Governance Registries

* **Category:** Fail-Open Security Vulnerability / Silent Error Swallowing / Observability Blindness
* **Location:** `infrastructure/policies/jurisdictional_sovereignty.py` (Lines 36–40)

#### Forensic Code Evidence
```python
# infrastructure/policies/jurisdictional_sovereignty.py:36-40
try:
    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
        registry = JurisdictionalRegistry(**data)
except Exception:
    registry = JurisdictionalRegistry()  # Defaults to empty registry {}
```

#### Architectural Critique
In security and regulatory compliance engineering, **Fail-Closed** is an inviolable axiom. Catching a bare `Exception` (encompassing `FileNotFoundError`, `PermissionError`, `json.JSONDecodeError`, and `pydantic.ValidationError`) and silently substituting an empty `JurisdictionalRegistry()` is a catastrophic Fail-Open defect.

1. **Silent Deactivation of Regulatory Controls:** If a malformed Git merge, disk corruption, or schema drift introduces a single trailing comma in `jurisdictional_sovereignty.json`, the engine catches the error, emits zero structured logs or metrics, and initializes an empty governance registry. Every subsequent assessment runs under the assumption that no static sovereign restrictions exist.
2. **Masking of Partial Torn Reads:** Coupled with Anti-Pattern IV (unlocked concurrent file writes), if a worker reads a partially written JSON file, the resulting `JSONDecodeError` is silently swallowed, causing transient, non-deterministic drops in regulatory enforcement across specific requests.

---

### 2.7. Anti-Pattern VII: Coarse-Grained Sovereignty Enum & Topological Conflation

* **Category:** Primitive Obsession / Dimensional Collapse
* **Location:** `domain/models.py` & `infrastructure/policies/jurisdictional_sovereignty.py`

#### Forensic Code Evidence
```python
# domain/models.py
class CloudSovereigntyLevel(str, Enum):
    PUBLIC_CLOUD = "Public Cloud"
    SOVEREIGN_CLOUD = "Sovereign Cloud"
    AIR_GAPPED_ON_PREM = "Air-Gapped On-Premises"
```

#### Architectural Critique
Reducing data sovereignty to a 1-dimensional, 3-state enumeration conflates five orthogonal architectural axes into a single primitive string:

1. **Physical Network Topology:** Public internet routability vs. private MPLS/DirectConnect vs. physical air-gap (unidirectional optical diodes).
2. **Legal Jurisdiction of the Cloud Service Provider (CSP):** Whether the CSP's parent entity is subject to extraterritorial compulsion laws (e.g., US *CLOUD Act* 18 U.S.C. § 2713, Chinese *National Intelligence Law* Art. 7) regardless of where the physical datacenter resides.
3. **Cryptographic Key Custody (KMS/HSM):** Provider-managed keys vs. Customer-Managed Keys (CMK) vs. External Key Management (EKM / Hold-Your-Own-Key) inside on-premises FIPS 140-3 Level 4 HSMs.
4. **Confidential Computing (TEE Attestation):** Whether memory pages in use are encrypted via hardware roots of trust (AMD SEV-SNP, Intel TDX, AWS Nitro Enclaves) preventing hypervisor inspection by the CSP.
5. **Operational Control Plane Residency:** Whether support personnel, telemetry pipelines, and IAM control planes are strictly restricted to cleared citizens residing within the sovereign territory (e.g., EU Gaia-X Label Level 3, German BSI C5, Saudi NCA CCRF).

---

## 3. Systemic Risks & Enterprise Failure Modes

When deployed within a Fortune 500 or Global Tier-1 enterprise infrastructure, the interaction of these anti-patterns produces compound systemic failures across legal, operational, and executive dimensions.

```
[Corrupted JSON / Missing File]
       |
       v (Anti-Pattern VI: Silent Exception Swallowing)
[Empty Jurisdictional Registry Initialized]
       |
       v (Anti-Pattern I: Naive Substring Geolocation)
["IEC 62443" Input Mapped to "DE" (Germany) Instead of Global OT]
       |
       v (Anti-Pattern IV: Runtime Source-Tree Mutation)
[JIT Synthesizer Attempts Write to Read-Only Container RootFS]
       |
       +---> [K8s ReadOnlyRootFS == True] ---> [Unhandled PermissionError / Pod CrashLoop]
       |
       +---> [K8s ReadOnlyRootFS == False] --> [Torn Write / Split-Brain State Across Pods]
                                                      |
                                                      v (Anti-Pattern V & II)
                                           [Uncalibrated 80% Confidence Score + 
                                            Unverified Arabic/Japanese Output]
```

### 3.1. Regulatory Compliance Penalties (DORA, GDPR, NCA CCRF, SEC)
* **Extraterritorial Misclassification:** Under the EU Digital Operational Resilience Act (DORA) and Schrems II mandates, financial entities must accurately assess third-party ICT concentration risk and extraterritorial data access. Because the engine conflates `Public Cloud` with legal jurisdiction and maps `NIS2` exclusively to Germany, a French or Italian bank undergoing assessment will receive fundamentally flawed legal remediation controls, exposing the institution to supervisory fines up to **2% of total annual worldwide turnover** (NIS2 Art. 34) or **1% of average daily worldwide turnover** (DORA Art. 50).
* **KSA NCA & SAMA Non-Compliance:** For deployments in the Kingdom of Saudi Arabia, the National Cybersecurity Authority (NCA) Cloud Cybersecurity Controls (CCC / CCRF) strictly mandate both physical data residency *and* cryptographic key custody within the Kingdom, alongside Arabic regulatory reporting integrity. If the engine silently bypasses Arabic linguistic verification (`return True`) and fails open on a corrupted registry, the resulting audit artifact violates mandatory NCA compliance attestations.

### 3.2. Container & Serverless Infrastructure Failures
* **CrashLoopBackOff in Hardened Clusters:** In Google Cloud Run, AWS Fargate, or hardened Kubernetes clusters enforcing CIS Pod Security Standards (`Restricted` profile), the root filesystem is mounted read-only (`ro`). The moment an assessment encounters an uncached jurisdiction and triggers JIT synthesis into `engine_config/policies/jurisdictions_dynamic/`, the worker crashes.
* **Ephemeral State Drift & Non-Determinism:** Even if mounted read-write on ephemeral container overlay storage, horizontal autoscaling (HPA) will route subsequent requests for the same client to different pods that lack the locally mutated JSON file, causing oscillating assessment outputs depending on which pod handles the RPC call.

### 3.3. Audit Board Invalidation & Epistemic Liability
* Chief Information Security Officers (CISOs) and External Auditors (Big 4 assurance teams) require **reproducible, calibrated provenance** for every risk score. When an audit board inspects the source code or tests sensitivity and discovers that an `85%` confidence score is merely `40 + (3 * 10) + (3 * 5)`—and that feeding zero sources yields `40%`—the entire quantitative model of the Assessment Engine is legally discredited as arbitrary numerology.

---

## 4. SOTA Enterprise Blueprint (The "Work of Art" Target Architecture)

To remediate these defects permanently, we replace ad-hoc procedural heuristics with **mathematically rigorous, type-safe, side-effect-free architectural patterns**.

---

### 4.1. Target Pattern I: Orthogonal 5-Dimensional Sovereignty Vector & Multi-Partite Jurisdictional Graph

Instead of a 3-state enum and substring matching, we model Sovereignty as an immutable **5-Dimensional Vector Lattice** and resolve jurisdictions via a **Typed Multi-Partite Directed Acyclic Graph (DAG)** separating *Technical Standards*, *Regulatory Frameworks*, *Supranational Unions*, and *ISO-3166 Sovereign States*.

```python
# domain/sovereignty_models.py
from enum import IntEnum, Enum
from typing import FrozenSet, Optional
from pydantic import BaseModel, Field, ConfigDict

class NetworkIsolationTopology(IntEnum):
    PUBLIC_INTERNET_ROUTABLE = 10
    VIRTUAL_PRIVATE_CLOUD_PEERING = 20
    DEDICATED_PHYSICAL_INTERCONNECT = 30
    LOGICAL_SOVEREIGN_ENCLAVE = 40
    PHYSICAL_AIR_GAP_OPTICAL_DIODE = 50

class KeyCustodyModel(IntEnum):
    CSP_MANAGED_MULTITENANT = 10
    CUSTOMER_MANAGED_KMS_CLOUD = 20
    CLOUD_HSM_DEDICATED_FIPS_140_3_L3 = 30
    EXTERNAL_HYOK_SOVEREIGN_HSM_L4 = 40

class ConfidentialComputeAttestation(IntEnum):
    NONE_STANDARD_HYPERVISOR = 10
    ENCRYPTED_VIRTUALIZATION_SEV_TDX = 20
    HARDWARE_ENCLAVE_CRYPTO_ATTESTED = 30

class ExtraterritorialJurisdictionExposure(IntEnum):
    SUBJECT_TO_FOREIGN_COMPULSION = 10     # e.g., US CLOUD Act / FISA 702 exposure
    MITIGATED_BY_EU_SOVEREIGN_PARTNER = 20 # e.g., Bleu (Orange/Capgemini) / Delos Cloud
    IMMUNE_DOMESTIC_LEGAL_ENTITY_ONLY = 30 # 100% domestic equity & operational control

class OperationalControlResidency(IntEnum):
    GLOBAL_FOLLOW_THE_SUN_SUPPORT = 10
    REGIONAL_RESIDENT_ENGINEERS = 20
    SECURITY_CLEARED_CITIZENS_ONLY = 30

class SovereigntyPostureVector(BaseModel):
    """
    Orthogonal 5-Dimensional Lattice representing exact technical and legal sovereignty.
    Supports partial ordering (A >= B iff all dimensions of A >= B).
    """
    model_config = ConfigDict(frozen=True)

    network_topology: NetworkIsolationTopology
    key_custody: KeyCustodyModel
    confidential_compute: ConfidentialComputeAttestation
    legal_immunity: ExtraterritorialJurisdictionExposure
    operational_residency: OperationalControlResidency

    def satisfies(self, required: "SovereigntyPostureVector") -> bool:
        """Dominance relation across the 5-dimensional product lattice."""
        return (
            self.network_topology >= required.network_topology
            and self.key_custody >= required.key_custody
            and self.confidential_compute >= required.confidential_compute
            and self.legal_immunity >= required.legal_immunity
            and self.operational_residency >= required.operational_residency
        )
```

#### Decoupled Jurisdictional Graph Resolution
Standards (`IEC 62443`, `ISO 27001`, `NIST CSF`) are modeled as **Jurisdiction-Agnostic Technical Frameworks**. Directives (`NIS2`, `GDPR`, `DORA`) are modeled as **Supranational Mandates** that expand only when intersected with an explicit geographic deployment footprint (ISO-3166-1 alpha-2 / ISO-3166-2 subdivision codes).

```python
# domain/jurisdiction_graph.py
from dataclasses import dataclass
from typing import Dict, Set, FrozenSet

@dataclass(frozen=True)
class RegulatoryNode:
    id: str
    scope: str  # "INTERNATIONAL_STANDARD" | "SUPRANATIONAL_DIRECTIVE" | "NATIONAL_STATUTE"
    applicable_iso3166: FrozenSet[str]  # Empty for global standards like IEC 62443

class DeterministicJurisdictionResolver:
    """
    Pure domain service. Never infers a sovereign state from an international technical standard.
    """
     EU_27_ISO_CODES: FrozenSet[str] = frozenset({
        "AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR", "DE", "GR", "HU",
        "IE", "IT", "LV", "LT", "LU", "MT", "NL", "PL", "PT", "RO", "SK", "SI", "ES", "SE"
    })

    def __init__(self, canonical_iso_map: Dict[str, str], regulatory_nodes: Dict[str, RegulatoryNode]):
        self._iso_map = canonical_iso_map
        self._nodes = regulatory_nodes

    def resolve_sovereign_footprints(
        self,
        explicit_locations: Set[str],
        declared_frameworks: Set[str]
    ) -> FrozenSet[str]:
        resolved_states: Set[str] = set()

        # 1. Resolve explicit geographic declarations via strict ISO-3166 canonical lookup
        for loc in explicit_locations:
            norm = loc.strip().upper()
            if norm in self._iso_map:
                resolved_states.add(self._iso_map[norm])

        # 2. Evaluate frameworks ONLY if they carry strict national statutory binding
        for fw in declared_frameworks:
            node = self._nodes.get(fw.strip().upper())
            if not node:
                continue
            if node.scope == "NATIONAL_STATUTE":
                resolved_states.update(node.applicable_iso3166)
            elif node.scope == "SUPRANATIONAL_DIRECTIVE":
                # If client operates in EU states, intersect; do not collapse to 'DE'
                eu_intersection = resolved_states.intersection(node.applicable_iso3166)
                if not eu_intersection and node.id in ("NIS2", "GDPR", "DORA"):
                    # Flag supranational applicability without fabricating a single nation-state
                    resolved_states.add("EU-SUPRANATIONAL")
            # Note: INTERNATIONAL_STANDARD (e.g., IEC 62443, NIST CSF) adds ZERO nation-state codes.

        return frozenset(resolved_states)
```

---

### 4.2. Target Pattern II: Bayesian Beta-Binomial Epistemic Confidence Calibration

We replace the linear magic-number heuristic (`base = 40 + ...`) with a mathematically grounded **Bayesian Beta-Binomial Conjugate Model** combined with Shannon Entropy contradiction decay.

Let the true reliability of an intelligence claim be modeled as a Beta distribution $\text{Beta}(\alpha, \beta)$ initialized with an uninformative Jeffreys prior $\alpha_0 = 0.5, \beta_0 = 0.5$ (or uniform Laplace prior $\alpha_0 = 1.0, \beta_0 = 1.0$).

* Each corroborating source $i \in \{1, \dots, N\}$ contributes positive evidence weighted by its **Source Authority Tier** $w_i \in (0, 1]$ (e.g., Primary Cryptographic/Regulatory Filing $w = 1.0$, Verified Architecture Spec $w = 0.7$, Secondary OSINT $w = 0.25$) and **Specificity Density** $s_i \in (0, 1]$:
  $$\alpha = \alpha_0 + \sum_{i=1}^{N} w_i \cdot (1 + s_i)$$
* Each contradicting signal $j \in \{1, \dots, M\}$ contributes negative evidence weighted by its authority $v_j$:
  $$\beta = \beta_0 + \gamma \sum_{j=1}^{M} v_j$$
* To prevent overconfidence on small sample sizes, we compute the **Lower Bound of the $(1 - \delta)$ Credible Interval** (or the posterior mean penalized by posterior variance $\sigma^2 = \frac{\alpha\beta}{(\alpha+\beta)^2(\alpha+\beta+1)}$), scaled to $[0, 100]$ with a zero-evidence floor of $0$:

```python
# domain/epistemic_calibration.py
import math
from dataclasses import dataclass
from typing import Sequence
from enum import Enum

class SourceAuthorityTier(Enum):
    PRIMARY_REGULATORY_FILING = 1.00   # SEC 10-K, BSI Audit Cert, SOC2 Type II Report
    INTERNAL_TELEMETRY_ATTESTED = 0.85 # Automated Cloud Config / IAM Dump
    VERIFIED_DOCUMENTATION = 0.60      # Architecture Diagrams, RFP Responses
    UNVERIFIED_OSINT_SCRAPE = 0.20     # Public Web Pages, Marketing Copy

@dataclass(frozen=True)
class EvidenceSignal:
    authority: SourceAuthorityTier
    specificity_ratio: float  # Continuous in [0.0, 1.0] based on named entity / metric density
    is_contradictory: bool = False

class BayesianEpistemicCalibrator:
    """
    Computes calibrated epistemic confidence in [0.0, 100.0] using Beta-Binomial
    posterior concentration and variance penalization. Zero evidence strictly yields 0.0.
    """
    PRIOR_ALPHA: float = 1.0
    PRIOR_BETA: float = 1.0
    CONTRADICTION_PENALTY_FACTOR: float = 2.5

    @classmethod
    def compute_calibrated_confidence(cls, signals: Sequence[EvidenceSignal]) -> float:
        if not signals:
            return 0.0

        alpha = cls.PRIOR_ALPHA
        beta = cls.PRIOR_BETA

        for sig in signals:
            clamped_spec = max(0.0, min(1.0, sig.specificity_ratio))
            weight = sig.authority.value * (0.5 + 0.5 * clamped_spec)
            if sig.is_contradictory:
                beta += cls.CONTRADICTION_PENALTY_FACTOR * weight
            else:
                alpha += weight

        total_concentration = alpha + beta
        posterior_mean = alpha / total_concentration
        posterior_variance = (alpha * beta) / (
            (total_concentration ** 2) * (total_concentration + 1.0)
        )
        std_error = math.sqrt(posterior_variance)

        # Conservative Lower Credible Bound (Mean - 1.645 * SE, approx 95% one-sided confidence)
        # Normalized so that prior state (alpha=1, beta=1) maps to 0.0 certainty gain
        prior_baseline = cls.PRIOR_ALPHA / (cls.PRIOR_ALPHA + cls.PRIOR_BETA)
        conservative_posterior = max(0.0, posterior_mean - 1.28 * std_error)

        if conservative_posterior <= (prior_baseline - 1.28 * math.sqrt(1.0 / 12.0)):
            return 0.0

        # Information-theoretic volume saturation factor: 1 - exp(-k * net_evidence)
        net_positive_evidence = max(0.0, alpha - cls.PRIOR_ALPHA)
        evidence_saturation = 1.0 - math.exp(-0.45 * net_positive_evidence)

        calibrated_score = 100.0 * conservative_posterior * evidence_saturation
        return round(min(100.0, max(0.0, calibrated_score)), 2)
```

---

### 4.3. Target Pattern III: Pure Functional Domain Core & Immutable Configuration Injection

We sever all filesystem I/O from `domain/taxonomy_resolver.py`. The Domain layer defines a strict **Protocol (Port)** and immutable Value Objects; the Infrastructure layer loads, validates, cryptographically hashes, and injects the data at process bootstrap.

```python
# domain/taxonomy_resolver.py (100% Pure Domain — Zero I/O Imports)
from typing import Protocol, Mapping, FrozenSet, Optional
from dataclasses import dataclass

@dataclass(frozen=True)
class TaxonomyConcept:
    concept_id: str
    canonical_labels: Mapping[str, str]  # ISO-639-1 -> Label
    synonyms: Mapping[str, FrozenSet[str]]

class TaxonomyRepositoryPort(Protocol):
    def get_concept(self, concept_id: str) -> Optional[TaxonomyConcept]: ...
    def resolve_term(self, term: str, lang_code: str) -> Optional[TaxonomyConcept]: ...

class PureTaxonomyResolver:
    """
    Pure in-memory domain service. O(1) lookup complexity. Zero filesystem access.
    """
    def __init__(self, concepts: Mapping[str, TaxonomyConcept]):
        self._concepts = concepts
        self._inverted_index: dict[tuple[str, str], TaxonomyConcept] = {}
        for concept in concepts.values():
            for lang, label in concept.canonical_labels.items():
                self._inverted_index[(lang.lower(), label.strip().lower())] = concept
            for lang, syn_set in concept.synonyms.items():
                for syn in syn_set:
                    self._inverted_index[(lang.lower(), syn.strip().lower())] = concept

    def resolve_term(self, term: str, lang_code: str) -> Optional[TaxonomyConcept]:
        return self._inverted_index.get((lang_code.lower(), term.strip().lower()))
```

---

### 4.4. Target Pattern IV: Fail-Closed Registry Bootstrap & Ephemeral-Safe Policy Persistence

1. **Fail-Closed Startup:** If `jurisdictional_sovereignty.json` or `taxonomy_multilingual.json` is missing, unreadable, or violates its Pydantic schema, the engine raises a fatal `GovernanceIntegrityFatalError` at process initialization, preventing the container readiness probe from passing.
2. **Container-Safe Persistence Port:** Dynamic JIT-synthesized jurisdictions are persisted through an injected `SynthesizedPolicyStorePort`. In production Kubernetes, this binds to a **Redis/PostgreSQL state store** or a dedicated writable volume (`/var/run/engine-state` / `/tmp`) using **atomic POSIX write-and-rename** (`tempfile.NamedTemporaryFile` + `os.fsync` + `os.replace`) to guarantee zero torn reads and full compliance with `readOnlyRootFilesystem: true`.

```python
# infrastructure/persistence/atomic_policy_store.py
import os
import json
import tempfile
from pathlib import Path
from typing import Optional
from domain.sovereignty_models import JurisdictionalProfile, JurisdictionalRegistry

class GovernanceIntegrityFatalError(RuntimeError):
    """Raised when critical compliance registries fail cryptographic or schema validation."""

def load_verified_registry_fail_closed(registry_path: Path) -> JurisdictionalRegistry:
    if not registry_path.exists() or not registry_path.is_file():
        raise GovernanceIntegrityFatalError(
            f"CRITICAL: Governance registry missing at {registry_path.resolve()}"
        )
    try:
        raw_bytes = registry_path.read_bytes()
        data = json.loads(raw_bytes.decode("utf-8"))
        registry = JurisdictionalRegistry.model_validate(data)
    except Exception as exc:
        raise GovernanceIntegrityFatalError(
            f"CRITICAL: Governance registry corrupted at {registry_path.resolve()}: {exc}"
        ) from exc

    if not registry.profiles:
        raise GovernanceIntegrityFatalError(
            "CRITICAL: Governance registry parsed successfully but contains zero profiles."
        )
    return registry

class AtomicWritableVolumePolicyStore:
    """
    Persists JIT-synthesized profiles strictly outside the source tree into an explicit
    mutable runtime volume using atomic POSIX rename semantics (zero torn reads).
    """
    def __init__(self, runtime_state_dir: Optional[Path] = None):
        env_dir = os.environ.get("ENGINE_RUNTIME_STATE_DIR", "/tmp/engine_synthesized_policies")
        self._state_dir = runtime_state_dir or Path(env_dir)
        self._state_dir.mkdir(parents=True, exist_ok=True)

    def save_profile_atomically(self, profile: JurisdictionalProfile) -> Path:
        target_path = self._state_dir / f"{profile.country_code.upper()}.json"
        serialized = json.dumps(profile.model_dump(mode="json"), indent=2, ensure_ascii=False)

        # Write to temporary file in the same filesystem, flush to disk, then atomic replace
        fd, tmp_path_str = tempfile.mkstemp(
            dir=str(self._state_dir),
            prefix=f".tmp_{profile.country_code}_",
            suffix=".json"
        )
        tmp_path = Path(tmp_path_str)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(serialized)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_path, target_path)
        except Exception:
            if tmp_path.exists():
                tmp_path.unlink(missing_ok=True)
            raise
        return target_path
```

---

### 4.5. Target Pattern V: Unicode Script-Block & Character N-Gram Linguistic Verifier

To eliminate the Euro-centric stop-word bias and the silent `return True` bypass on non-Western languages (`ar`, `ja`, `zh`, `ko`, `pt`, `it`, `ru`), we implement a **Two-Stage Deterministic Linguistic Guardrail**:

1. **Stage 1: Unicode Script Block Density Verification ($O(N)$ character scan):** Verifies that languages utilizing non-Latin orthographies (e.g., Arabic `U+0600..U+06FF`, CJK Unified Ideographs `U+4E00..U+9FFF`, Hiragana/Katakana `U+3040..U+30FF`, Hangul `U+AC00..U+D7AF`) contain the mandatory proportion of characters from their respective Unicode blocks. This immediately catches English LLM hallucinations when generating Arabic, Japanese, or Chinese reports without needing whitespace tokenization.
2. **Stage 2: Character Trigram / Function-Morpheme Profile Verification:** For Latin-script languages (`en`, `es`, `de`, `fr`, `pt`, `it`, `nl`, `pl`) and unsegmented scripts alike, checks character n-gram and bound-morpheme distributions, failing closed (`return False` or raising `UnsupportedLanguageVerificationError`) if an unconfigured ISO-639-1 code is requested.

```python
# domain/linguistic_guardrail.py
import unicodedata
from dataclasses import dataclass
from typing import FrozenSet, Mapping, Tuple

class UnsupportedLanguageVerificationError(ValueError):
    """Raised when linguistic verification is requested for an unconfigured ISO-639-1 language."""

@dataclass(frozen=True)
class OrthographicProfile:
    iso_code: str
    required_unicode_ranges: Tuple[Tuple[int, int], ...]
    min_script_ratio: float
    signature_substrings: FrozenSet[str]  # Works for both space-delimited words and CJK/Arabic particles
    min_signature_hits: int

LANGUAGE_PROFILES: Mapping[str, OrthographicProfile] = {
    "en": OrthographicProfile(
        iso_code="en",
        required_unicode_ranges=((0x0041, 0x007A),),
        min_script_ratio=0.70,
        signature_substrings=frozenset({" the ", " and ", " of ", " to ", " in ", " is ", " for ", " that ", " with "}),
        min_signature_hits=3,
    ),
    "de": OrthographicProfile(
        iso_code="de",
        required_unicode_ranges=((0x0041, 0x007A), (0x00C0, 0x00FF)),
        min_script_ratio=0.70,
        signature_substrings=frozenset({" der ", " die ", " und ", " in ", " den ", " von ", " zu ", " das ", " mit "}),
        min_signature_hits=3,
    ),
    "es": OrthographicProfile(
        iso_code="es",
        required_unicode_ranges=((0x0041, 0x007A), (0x00C0, 0x00FF)),
        min_script_ratio=0.70,
        signature_substrings=frozenset({" de ", " la ", " que ", " el ", " en ", " los ", " del ", " las ", " por "}),
        min_signature_hits=3,
    ),
    "fr": OrthographicProfile(
        iso_code="fr",
        required_unicode_ranges=((0x0041, 0x007A), (0x00C0, 0x00FF)),
        min_script_ratio=0.70,
        signature_substrings=frozenset({" de ", " la ", " le ", " et ", " les ", " des ", " en ", " un ", " du "}),
        min_signature_hits=3,
    ),
    "pt": OrthographicProfile(
        iso_code="pt",
        required_unicode_ranges=((0x0041, 0x007A), (0x00C0, 0x00FF)),
        min_script_ratio=0.70,
        signature_substrings=frozenset({" de ", " que ", " no ", " na ", " para ", " com ", " uma ", " os ", " não "}),
        min_signature_hits=3,
    ),
    "ar": OrthographicProfile(
        iso_code="ar",
        required_unicode_ranges=((0x0600, 0x06FF), (0x0750, 0x077F), (0xFB50, 0xFDFF), (0xFE70, 0xFEFF)),
        min_script_ratio=0.55,  # Allows embedded technical acronyms (e.g., ISO, NIST, TLS)
        signature_substrings=frozenset({"ال", "في ", "من ", "على ", "إلى ", "أن ", "التي ", "هذا ", "مع "}),
        min_signature_hits=3,
    ),
    "ja": OrthographicProfile(
        iso_code="ja",
        required_unicode_ranges=((0x3040, 0x309F), (0x30A0, 0x30FF), (0x4E00, 0x9FFF)),
        min_script_ratio=0.50,
        signature_substrings=frozenset({"の", "に", "は", "を", "た", "が", "で", "て", "と", "する", "ます"}),
        min_signature_hits=4,
    ),
    "zh": OrthographicProfile(
        iso_code="zh",
        required_unicode_ranges=((0x4E00, 0x9FFF),),
        min_script_ratio=0.50,
        signature_substrings=frozenset({"的", "是", "在", "和", "了", "有", "与", "为", "对", "及"}),
        min_signature_hits=4,
    ),
}

def verify_language_consistency_strict(text: str, target_lang: str) -> bool:
    """
    Deterministic, script-aware linguistic verification.
    Fails closed on unknown languages or script-block mismatch.
    """
    norm_lang = target_lang.strip().lower()[:2]
    profile = LANGUAGE_PROFILES.get(norm_lang)
    if profile is None:
        raise UnsupportedLanguageVerificationError(
            f"No deterministic linguistic verification profile registered for ISO code '{target_lang}'."
        )

    alpha_chars = [ch for ch in text if ch.isalpha()]
    if len(alpha_chars) < 10:
        return False

    # Stage 1: Unicode Script Block Ratio Check
    in_range_count = 0
    for ch in alpha_chars:
        cp = ord(ch)
        if any(start <= cp <= end for start, end in profile.required_unicode_ranges):
            in_range_count += 1

    script_ratio = in_range_count / len(alpha_chars)
    if script_ratio < profile.min_script_ratio:
        return False

    # Stage 2: Substring / Bound-Morpheme / Particle Intersection
    normalized_text = f" {text.lower()} "
    hits = sum(1 for sig in profile.signature_substrings if sig in normalized_text)
    return hits >= profile.min_signature_hits
```

---

## 5. Additional Systemic Anti-Patterns Discovered Across the Codebase

Beyond the six primary findings, forensic traversal of the broader repository architecture exposes three additional coupled anti-patterns that must be remediated concurrently:

### 5.1. Anti-Pattern VIII: Unbounded In-Memory Cache Growth Without Eviction (OOM Hazard)
* **Location:** `infrastructure/policies/jurisdictional_sovereignty.py` & `infrastructure/client_intelligence.py`
* **Defect:** Synthesized jurisdictional profiles and resolved client intelligence objects are accumulated in module-level Python dictionaries (`_DYNAMIC_CACHE = {}`) without an LRU bound (`functools.lru_cache(maxsize=...)` or TTL eviction).
* **Risk:** In long-running worker processes handling multi-tenant assessments with varied inputs, the module-level dictionary grows monotonically, causing steady RSS memory bloat until the Kubernetes kubelet terminates the container with `OOMKilled (Exit Code 137)`.

### 5.2. Anti-Pattern IX: Stringly-Typed Framework Identifiers & Lack of Canonicalization
* **Location:** Cross-module boundary between `domain/models.py` and `infrastructure/policies/`
* **Defect:** Regulatory frameworks are passed across boundaries as raw unvalidated `str` primitives (`"ISO27001"`, `"ISO-27001"`, `"ISO/IEC 27001:2022"`).
* **Risk:** Subtle formatting variations cause silent cache misses in policy lookups and duplicate synthesis loops in the CEGAR engine.
* **Target Fix:** Introduce a canonical `FrameworkURN` value object (e.g., `urn:lex:standard:iso-iec:27001:2022`) normalized at the API ingress boundary via a deterministic alias registry.

### 5.3. Anti-Pattern X: Synchronous File & Network I/O Inside Async Execution Paths
* **Location:** `infrastructure/policies/jurisdictional_sovereignty.py` (JIT LLM synthesis + file persistence)
* **Defect:** Synchronous `open()`, `json.load()`, and blocking HTTP client calls are invoked inside functions called by the async orchestration pipeline without offloading to `asyncio.to_thread()` or using `aiofiles` / `httpx.AsyncClient`.
* **Risk:** Blocks the single-threaded Python `asyncio` event loop during disk flushes or policy loading, degrading p99 tail latency and starving concurrent health-check probes (`LivenessProbe` timeouts).

---

## 6. Prioritized Remediation Roadmap

The remediation sequence is structured into four deterministic engineering phases prioritized by **Compliance Blast Radius** and **Runtime Stability ROI**.

```
Phase 1: Fail-Closed & Immutability (P0)  --->  Eliminates Container Crashes & Silent Governance Drops
Phase 2: Domain Purity & Graph (P0/P1)    --->  Eliminates Legal Misattribution (IEC 62443 / NIS2)
Phase 3: Bayesian & Linguistic (P1)       --->  Eliminates Fake Precision & CJK/Arabic Hallucinations
Phase 4: 5D Sovereignty Lattice (P2)      --->  Enables Gaia-X / BSI C5 / NCA CCRF Tier-1 Compliance
```

| Phase | Target Defect / Module | Concrete Engineering Action | Effort (Eng-Days) | Blast Radius | Architectural ROI |
| :--- | :--- | :--- | :---: | :---: | :--- |
| **Phase 1.1 (P0)** | **Anti-Pattern VI:** Silent Registry Fallback (`jurisdictional_sovereignty.py`) | Replace `except Exception: registry = JurisdictionalRegistry()` with `load_verified_registry_fail_closed()`. Add SHA-256 checksum & Pydantic strict schema assertion at startup. | 1.0 | Low | **Critical:** Guarantees Fail-Closed regulatory integrity; eliminates silent un-governed execution. |
| **Phase 1.2 (P0)** | **Anti-Pattern IV:** Source-Tree Runtime Mutation (`jurisdictional_sovereignty.py`) | Extract `SynthesizedPolicyStorePort`. Implement `AtomicWritableVolumePolicyStore` writing to `ENGINE_RUNTIME_STATE_DIR` (`/tmp` or Redis) via `mkstemp` + `os.fsync` + `os.replace`. | 2.0 | Medium | **Critical:** Unblocks Kubernetes `readOnlyRootFilesystem: true` compliance and eliminates torn JSON reads. |
| **Phase 2.1 (P0)** | **Anti-Pattern I:** Substring Geolocation (`jurisdictional_sovereignty.py`) | Decouple `INTERNATIONAL_STANDARD` (`IEC 62443`, `NIST`) and `SUPRANATIONAL_DIRECTIVE` (`NIS2`) from national ISO-3166 state inference via `DeterministicJurisdictionResolver`. | 3.0 | Medium | **High:** Eliminates legal misattribution of German/US national laws to global and EU-27 clients. |
| **Phase 2.2 (P1)** | **Anti-Pattern III:** Impure Domain I/O (`domain/taxonomy_resolver.py`) | Refactor `TaxonomyResolver` into `PureTaxonomyResolver` accepting an immutable `Mapping[str, TaxonomyConcept]` via constructor injection. Move JSON loading to `infrastructure/bootstrap.py`. | 2.0 | Medium | **High:** Restores Hexagonal/Clean Architecture purity; enables 100% in-memory unit testing and $O(1)$ lookups. |
| **Phase 3.1 (P1)** | **Anti-Pattern II:** Heuristic Numerology (`client_intelligence.py`) | Replace `estimate_confidence_score` linear constants with `BayesianEpistemicCalibrator` (Beta-Binomial conjugate model with source authority tiers and variance penalty). | 2.5 | Low | **High:** Provides mathematically defensible, audit-ready epistemic calibration; forces 0% confidence on 0 evidence. |
| **Phase 3.2 (P1)** | **Anti-Pattern V:** Euro-Centric Stop-Words (`domain/linguistic_guardrail.py`) | Replace `STOP_WORDS` whitespace split with `verify_language_consistency_strict` using Unicode script-block density + particle/morpheme matching across `en, de, es, fr, pt, ar, ja, zh`. | 2.5 | Low | **High:** Closes the `return True` verification bypass for MENA and APAC deployments. |
| **Phase 4.1 (P2)** | **Anti-Pattern VII:** 3-State Sovereignty Enum (`domain/models.py`) | Replace `CloudSovereigntyLevel` enum with `SovereigntyPostureVector` (5D lattice: Network, Key Custody, Confidential Compute, Extraterritorial Immunity, Operational Residency). | 4.0 | High | **Transformative:** Aligns engine ontology with EU Gaia-X, German BSI C5, and Saudi NCA CCRF frameworks. |

---

## 7. Verification & Architectural Fitness Functions

To prevent regression into these anti-patterns during future development cycles, the following **Automated Architectural Fitness Functions** (via `pytest` and AST static analysis) must be enforced as blocking CI/CD gates:

1. **Domain Purity AST Gate (`tests/architecture/test_domain_purity.py`):**
   Parses the Abstract Syntax Tree (`ast.parse`) of every `.py` file inside `domain/` and fails the build if any module imports `os`, `sys`, `pathlib`, `io`, `socket`, `requests`, `httpx`, `urllib`, or invokes the built-in `open()` function.
2. **Read-Only Root Filesystem Integration Gate (`tests/integration/test_immutable_container.py`):**
   Executes the full assessment and JIT synthesis pipeline with `chmod -R a-w engine_config/ domain/ infrastructure/` (or inside a `docker run --read-only --tmpfs /tmp` container) to mathematically prove zero source-tree mutations occur at runtime.
3. **Epistemic Boundary Invariant Property Tests (`tests/unit/test_epistemic_calibration.py`):**
   Uses `hypothesis` property-based testing to verify that:
   * $\text{Confidence}(\emptyset) == 0.0$ (Zero evidence strictly yields zero confidence).
   * Adding a contradictory primary source strictly decreases posterior confidence ($\text{Confidence}(E \cup \{c_{\text{contra}}\}) < \text{Confidence}(E)$).
   * International standards (`IEC 62443`, `ISO 27001`, `NIST CSF`) evaluated in isolation produce $\emptyset$ national ISO-3166 country codes.