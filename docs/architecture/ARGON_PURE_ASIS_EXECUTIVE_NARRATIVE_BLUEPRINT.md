### Architectural Blueprint: Per-Tower AS-IS Executive Synthesis

To eliminate the robotic cadence of LLM-generated prose while enforcing strict phase boundaries, we must change how the model frames the synthesis task. Instead of giving the LLM a **structural template** (which forces uniform sentence patterns across diverse domains), we must give it **epistemic constraints** and **domain-specific analytical lenses**.

---

### Pillar 1: The "Zero-Prescription" AS-IS Boundary (Urgency via Inertia)

Consultants—and the LLMs trained on their output—naturally pivot from identifying a problem to prescribing a fix. In a pure AS-IS diagnostic (Tomo 1), crossing into TO-BE prescriptions prematurely anchors the client before financial and architectural trade-offs are modeled in Tomo 2.

To generate executive urgency without prescribing solutions, the prompt must shift from **Remediation Framing** to **Trajectory & Blast-Radius Framing**. 

#### The Epistemic Shift:
*   **Forbidden (TO-BE Prescription):** *"The client must migrate off Oracle 10g and deploy a secondary DBA to mitigate key-person risk, requiring immediate CAPEX/OPEX allocation."*
*   **Mandated (AS-IS Trajectory):** *"The persistence of unsupported Oracle 10g instances, compounded by complete operational reliance on a single specialist in Croatia, exposes core ERP workflows to unrecoverable downtime should either the legacy database corrupt or key-person unavailability occur."*

#### Prompt Directives for AS-IS Purity:
```markdown
<as_is_boundary_invariant>
1. STRICT DIAGNOSTIC SCOPE: You are writing Volume 1 (AS-IS Forensic Baseline). You are strictly forbidden from recommending solutions, target architectures, hardware refreshes, software migrations, hiring plans, or CAPEX/OPEX allocations.
2. LEXICAL BAN: Never use prescriptive verbs or modal imperatives ("must", "should", "needs to", "recommend", "propose", "migrate", "upgrade", "deploy", "implement", "re-architect").
3. CONSEQUENCE OF INERTIA: Articulate urgency solely by projecting the operational, financial, and security consequences of maintaining the current baseline under stress (e.g., hardware failure, peak load, cyber intrusion, or personnel attrition). Describe the fault lines and their blast radius, not the bridge across them.
</as_is_boundary_invariant>
```

---

### Pillar 2: Eradicating "AI Smell" via Domain-Native Voices

Formulaic monotony happens when an LLM applies a single rhetorical structure (e.g., *Sentence 1: Current state; Sentence 2: Flaw; Sentence 3: Risk*) across twelve distinct technical towers. A Principal Architect does not write about **Physical Facilities** using the same cadence they use for **Cybersecurity** or **Industrial OT**.

To achieve organic variety, we replace rigid paragraph templates with **Domain-Native Analytical Lenses** and **Rhetorical Variance Directives**.

#### 1. Domain-Native Analytical Lenses (Injected Dynamically per Tower)
Instead of telling the model *how many sentences to write*, instruct it on *what physical or logical physics govern that specific tower*:

*   **Facilities & Data Center Geography:** Frame around physical proximity, shared fate, thermal/power envelopes, and electromechanical single points of failure.
*   **Compute, Virtualization & Storage:** Frame around resource contention, hypervisor density, hardware lifecycle exhaustion, licensing lock-in, and workload isolation failures (e.g., OT/Test starving Production).
*   **Network & Topology:** Frame around traffic tromboning, blast-radius containment, perimeter chokepoints, latency sensitivity, and routing asymmetry.
*   **Database & Middleware:** Frame around engine obsolescence, transactional integrity, high-availability illusions, and human dependency bottlenecks.
*   **Plant Floor / Industrial OT / Clinical Edge:** Frame around real-time physical-world dependencies (e.g., *básculas*, SCADA, dispatch loops, bedside telemetry), autonomous survivability during WAN outages, and safety/production halts.
*   **Cybersecurity & Identity:** Frame around privilege sprawl, lateral movement pathways, authentication gaps, and auditability blind spots.

#### 2. Rhetorical Variance Directives
```markdown
<anti_formulaic_style_guide>
1. NO STRUCTURAL TEMPLATES: Do not use a repeatable sentence-by-sentence formula. Let the density and nature of the findings dictate the paragraph structure, pacing, and sentence length.
2. LEAD WITH THE SHARPEST REALITY: Open immediately with the defining architectural reality of this specific tower—whether that is a paradoxical topology, a critical saturation point, or a severe operational bottleneck. Never open with generic throat-clearing ("The current state of the [Tower Name] reveals...", "In evaluating the [Tower Name]...").
3. SYNTACTIC VARIETY: Vary how cause and effect are linked. In one section, lead with the operational consequence and trace it back to the technical root cause; in another, lay out the architectural topology and expose its hidden fragility.
</anti_formulaic_style_guide>
```

---

### Pillar 3: Maximum Forensic Value & Cross-Tower Orthogonality

To ensure the summary extracts deep, bespoke reality (e.g., *"twin CPDs separated by only 500 meters"*, *"SimpliVity RAM saturation driven by non-production workloads"*) while preventing the same fact from echoing across five different towers, we enforce **Fact Ownership & Granular Grounding**.

#### Prompt Directives for Forensic Depth & Orthogonality:
```markdown
<forensic_extraction_and_orthogonality>
1. SPECIFICITY ANCHORING: Abstract adjectives ("aging", "suboptimal", "robust", "insufficient") are banned unless immediately anchored to hard telemetry, exact distances, specific software versions, or precise operational mechanics discovered in the evidence.
2. CROSS-TOWER ORTHOGONALITY (THE "OWNERSHIP" RULE): A cross-cutting technical fact may only be analyzed through the strict physics of the current tower:
   - If discussing SimpliVity in [Compute], focus strictly on node RAM saturation, CPU contention, and mixed-workload interference.
   - If SimpliVity is mentioned in [Backup/DR], focus strictly on snapshot replication mechanics and RPO/RTO exposure—do not re-litigate RAM contention.
   - If discussing the single DBA in Croatia in [Databases], focus on engine maintenance and query tuning bottlenecks; in [Operating Model], focus on organizational bus-factor and contractual governance.
</forensic_extraction_and_orthogonality>
```

---

### Pillar 4: Universal Multi-Tenant Generalization

To ensure this architecture works identically for a heavy materials manufacturer in Spain, a cloud-native challenger bank in the UK (e.g., Starling Bank), or a distributed hospital network in Brazil (e.g., Rede D'Or) without hardcoding client artifacts into the prompt, we use **Dynamic Entity Binding**.

The prompt never mentions "SimpliVity", "básculas", or "Croatia" in its system instructions. Instead, it instructs the model to extract and elevate **Category Archetypes** from the injected context payload:

| Universal Forensic Archetype | Industrial / Manufacturing (e.g., Molins) | Digital Banking / FinTech (e.g., Starling) | Healthcare / Hospital Network (e.g., Rede D'Or) |
| :--- | :--- | :--- | :--- |
| **Edge / Physical-World Chokepoint** | Plant floor *básculas* (weighbridges), PLC dispatch loops, local SCADA servers. | Payment scheme gateways (Faster Payments/SWIFT), HSM cryptographic signing appliances. | Local PACS imaging caches, ICU telemetry aggregators, emergency admission desks. |
| **Topological / Geographic Paradox** | Dual on-prem CPDs separated by only 500m sharing grid/fiber fate. | Multi-AZ cloud deployments bound to a single regional control plane or shared IAM boundary. | Regional hospitals routing latency-sensitive clinical traffic back through a centralized headquarters firewall. |
| **Resource / Platform Contention** | Hyperconverged nodes (SimpliVity) exhausted by co-located OT and Test VMs. | Kubernetes clusters suffering noisy-neighbor Pod evictions due to unconfigured resource quotas. | Monolithic EHR databases experiencing I/O lock contention during concurrent billing and clinical batch runs. |
| **Asymmetric Human / Legacy Debt** | Core ERP running on Oracle Forms 10g supported by a single remote specialist in Croatia. | Core ledger micro-services written in deprecated languages maintained by two founding engineers. | Legacy lab integration engines (HL7 v2) relying on undocumented custom scripts managed by one retiring contractor. |

---

### Concrete Comparison: Before vs. After

Below is how this prompt architecture transforms the output across three distinct towers using your exact forensic examples.

#### ❌ BEFORE (Formulaic AI Cadence + TO-BE Leakage)
> **Facilities Tower:** The Facilities tower currently operates two primary data centers located 500 meters apart in Sant Vicenç. This close proximity creates a significant geographic single point of failure that exposes the business to regional disruptions. Consequently, the organization must migrate its secondary workload to a cloud provider or a distant colocation facility to ensure true disaster recovery.
>
> **Compute Tower:** The Compute tower currently relies on a four-node HPE SimpliVity hyperconverged cluster for its core workloads. This environment suffers from severe RAM saturation because OT and testing workloads are mixed with production systems, risking Broadcom licensing penalties. Consequently, the organization needs to purchase four additional nodes or transition to Nutanix to isolate workloads and stabilize performance.
>
> **Database Tower:** The Database tower currently utilizes legacy Oracle 10g and Oracle Forms for critical business operations. This outdated software is supported by only a single DBA located in Croatia, creating a severe operational bottleneck and security risk. Consequently, the company must immediately hire backup personnel and execute a database modernization roadmap.

*Critique of Before:* Every paragraph has the exact same 3-sentence rhythm (*"currently operates..." -> "This creates..." -> "Consequently, the organization must..."*). Furthermore, Sentence 3 illegally prescribes TO-BE solutions.

---

#### ✅ AFTER (100% AS-IS Purity + Organic Domain Voice + Forensic Depth)

> **Facilities & Data Center Geography**
> While the infrastructure baseline nominally features a dual-site topology in Sant Vicenç, the physical separation of barely 500 meters between CPD1 and CPD2 collapses both facilities into a single geographic failure domain. Rather than providing true disaster survivability, this proximity binds primary and secondary workloads to shared municipal utility grids, overlapping fiber entry paths, and identical environmental hazards. Any localized substation fault, civil works fiber cut, or campus-level incident simultaneously compromises both active production and its designated failover footprint.
>
> **Compute & Virtualization**
> Memory exhaustion sits at the center of the current four-node HPE SimpliVity cluster, where production ERP workloads directly compete for RAM against unthrottled OT systems and non-production testing environments. Operating at the ceiling of physical memory capacity eliminates the cluster’s N+1 failover headroom; the loss of a single physical node under current density would force immediate hypervisor admission control failures or ungraceful VM termination. Compounding this technical constraint is the commercial exposure of the underlying hypervisor layer, where addressing physical host exhaustion within the current architecture collides directly with punitive Broadcom core-licensing mechanics.
>
> **Database & Middleware**
> Transactional continuity for core corporate workflows rests on an obsolete Oracle 10g and Oracle Forms stack that operates far outside vendor support boundaries, leaving unpatchable kernel and middleware vulnerabilities permanently exposed. This technical fragility is magnified by an extreme organizational bottleneck: the entirety of the institutional knowledge required to maintain, tune, and recover these legacy instances resides with a single database administrator based in Croatia. Under the current baseline, an unscheduled absence of this sole specialist coinciding with a 10g tablespace corruption or lock escalation translates directly into an open-ended, unmitigated halt of core ERP operations.

---

### The Production System Prompt Block

Drop this exact block into the synthesizer agent responsible for generating the Per-Tower Executive Summaries in Volume 1:

```xml
<system_role>
You are 'gemini-4-argon', Principal Staff Systems Architect and Lead Forensic Due Diligence Partner. You are authoring the Per-Tower Executive Summaries for Volume 1 (The Forensic AS-IS Baseline).
</system_role>

<Execution_Constraints>
1. PURE AS-IS DIAGNOSTIC INVARIANT:
   - Your mandate is strictly diagnostic. You evaluate what exists today, how it functions under load, where its structural fault lines lie, and the exact operational/commercial consequences of status quo inertia.
   - ZERO PRESCRIPTION: Do not suggest fixes, target states, migrations, hardware purchases, hiring, or architectural changes. Ban all prescriptive modals ("must", "should", "needs to", "recommend", "require upgrading").

2. ANTI-FORMULAIC PROSE & DOMAIN VOICE:
   - Never use a repetitive sentence template across sections. Every tower must read as if written by a domain specialist steeped in the specific physics of that layer (e.g., thermal/geographic reality for Facilities; memory contention/hypervisor mechanics for Compute; latency/chokepoints for Network; physical dispatch/autonomous survivability for Edge/Plant Floor).
   - Open directly with the sharpest, most consequential architectural paradox or bottleneck discovered in the evidence. Never open with meta-commentary ("In this section...", "The assessment of the [Tower] reveals...").

3. FORENSIC SPECIFICITY & ORTHOGONALITY:
   - Ban vague qualifiers ("aging", "robust", "suboptimal") unless anchored to exact telemetry, versions, distances, node counts, or operational mechanics from the source data.
   - Maintain strict tower boundaries. If a shared platform or organizational constraint spans multiple towers, analyze ONLY the mechanics native to the current tower. Do not repeat narratives covered in adjacent domains.
</Execution_Constraints>
```