**MEMORANDUM TO THE BOARD OF DIRECTORS – CEMENTOS MOLINS**
**FROM:** Principal Data Center Infrastructure Auditor (Uptime Institute Tier-IV Senior Fellow)
**SUBJECT:** Independent Peer Review and Audit of *Anexo Técnico: Centro de Datos Físico e Instalaciones (AS-IS)* – Prepared by NTT DATA
**DATE:** October 2026

---

### 1. OVERALL VERDICT

**I DEMAND REVISIONS before the Board accepts this deliverable or authorizes any capital expenditure based upon it.** 

While the report accurately identifies critical macro-level geographical and physical security vulnerabilities, it suffers from severe internal contradictions in its risk modeling, a superficial treatment of critical electromechanical topologies, and an over-reliance on automated consulting templates that fail to justify the underlying math of its financial projections.

---

### 2. TECHNICAL REALISM OF THE DIAGNOSTIC

From an operational standpoint, the report is a hybrid of sharp, plant-level observation and lazy, boilerplate consulting templating. 

**Where it reflects operational reality:**
The diagnostic accurately captures the gritty reality of heavy manufacturing IT/OT environments. Identifying the 500-meter proximity between CPD 1 and CPD 2 in Sant Vicenç dels Horts as a shared fault domain—sharing a single municipal medium-voltage (MV) utility feed and unmeshed dark fiber—is spot-on. Furthermore, the report correctly highlights the acute threat of cement and aggregate particulate contamination in remote batching plants, the lack of hot/cold aisle containment, and the alarming "Shadow IT" practices where plant personnel splice their own fiber and install unauthorized Wi-Fi APs directly into the batching control networks. The observation that the HPE SimpliVity hyperconverged cluster lacks the N+X compute/RAM headroom to survive a full site failover is a crucial, non-obvious catch.

**Where it fails my Uptime Institute Tier-IV scrutiny (The Consulting Template Trap):**
As a physical infrastructure audit, the electromechanical depth is unacceptably shallow. 
* **Electrical Topology & ATS Omissions:** The glossary defines Automatic Transfer Switches (ATS), and the scope mentions UPS (SAI) and generators, yet the body of the report contains **zero technical analysis** of the electrical single-line diagram (SLD). Are the UPS systems in an $N$, $N+1$, or $2N$ configuration? What is the battery runtime at peak load? Are there diesel generators on-site at Sant Vicenç? What is the fuel autonomy? Are the ATS units single points of failure (SPOFs) lacking maintenance bypasses? Giving "Energy and Electrical Continuity" a score of 2.50/5.0 while admitting both CPDs share a single municipal MV feed and lack compute failover capacity is a contradiction.
* **Cooling & Fire Suppression Vague Generalities:** In the Fire Protection section, the report merely quotes an FM Global statistic about VESDA and clean agents, without actually stating what Molins currently has installed! Do CPD 1 and 2 use FM-200, Novec 1230, Inergen, water sprinklers, or hand-held extinguishers? Are the room perimeters properly sealed to retain clean agent concentration? We are not told.
* **Template Artifacts:** Several paragraphs end mid-sentence without punctuation, and Table 16 literally leaves a bracket unclosed from an English template: *"incidencias no contenidas en HVAC Cooling Resiliency (N+1 / 2N."* Furthermore, theCMMI scale definitions in the text (e.g., 1.60–2.59 is "Nivel 2 - Gestionado") clash with the English labels in the diagnostic text (where 1.67 and 1.75 are labeled "Initial").

---

### 3. SCRUTINY OF RISK FORMULATION & NUMBERS

The report utilizes the Open FAIR™ standard and claims a 10,000-iteration Monte Carlo simulation. While the baseline hourly downtime cost of **13,061 €/h** is a reasonable, conservative figure for a €1.144B enterprise (representing roughly 10% of gross hourly revenue burn across global operations, localized to the Spanish/corporate hub), the downstream risk math is riddled with fatal flaws that a sharp Molins engineer will easily dismantle.

#### A. Evaluation of the Numbers (ALE & P90)
There is a glaring, inexcusable mathematical contradiction in the report’s catastrophe modeling:
* In the Executive Summary and Section 4.3.1, the report defines the **"Extreme Crisis / P90 Scenario"** (simultaneous loss of redundant power and thermal collapse) as requiring **21.7 hours** to recover, resulting in a total financial impact of **729,076 €** (282,843 € operational downtime + 446,232 € emergency response costs).
* Yet, in the individual risk tables (Tables 11–16), **every single individual risk except one claims a longer outage duration than the worst-case P90 scenario!** 
  * RVS06 (Shared MV Feed/Site Failure) estimates **77.4 hours** of downtime (SLE: 707,660 €).
  * RVS01 (Lack of electrical telemetry) estimates **57.9 hours** of downtime (SLE: 302,500 €).
  * RVS02 (Lack of HVAC telemetry/N+1) estimates **57.9 hours** of downtime (SLE: 302,500 €).
  * RVS04 (Physical server theft in Precast) estimates **44.2 hours** of downtime (SLE: 230,924 €).

How can a multi-system catastrophic collapse (P90) take 21.7 hours to recover from, while a single failure in electrical telemetry (RVS01) causes a 57.9-hour outage? Furthermore, in the individual risk tables, SLE is calculated purely as *Hours × Hourly Rate*, completely ignoring the 446,232 € emergency contractor costs used in the P90 narrative. The model is mathematically incoherent.

#### B. Credibility of Risk Scenarios (How a Client Engineer Will Shoot Them Down)
If I were the Lead Facilities Engineer at Molins, I would immediately attack the following scenarios:
1. **The "Identical Twin" Template Fallacy (RVS01 vs. RVS02):** RVS01 (lack of power telemetry in main panels) and RVS02 (lack of HVAC telemetry and N+1 cooling) have the **exact same outage duration (57.9 hours)**, the **exact same SLE (302,500 €)**, and the **exact same frequency (1 in 7 years)**. From a physics and thermodynamics standpoint, this is absurd. A lack of power metering does not cause a 58-hour outage; a blown transformer or busbar fault does. Conversely, a cooling failure leads to thermal runaway in 15 to 30 minutes, which can bake storage controllers and require hardware replacement. Giving them identical actuarial parameters proves the consultants plugged generic numbers into a spreadsheet rather than modeling actual electromechanical failure modes.
2. **RVS04 (Legacy RODCs in Precast Plants):** The report claims that the physical compromise or failure of legacy Read-Only Domain Controllers (RODCs) and file servers in 9 peripheral Precast plants will cause a **44.2-hour outage** costing **5,224 €/h** (which is 40% of the *entire corporation's* hourly downtime cost). An engineer will rightly point out: *"First, the whole point of an RODC is that it caches credentials and cannot poison the central Active Directory forest. Second, how does losing a legacy server in one or two peripheral precast plants paralyze 40% of Cementos Molins' entire corporate operations for nearly two days?"*

#### C. Budget Defense Objections
If I were defending Molins' CAPEX budget against this report, I would freeze funding based on NTT DATA’s own **Liability Disclaimer (Section 5.2)**. The disclaimer explicitly admits that the entire diagnostic is based *exclusively* on questionnaires and qualitative interviews with Molins staff—meaning **the consultants did not perform empirical physical testing, thermal imaging, power quality analysis, or physical audits of the switchgear.** Why should the Board approve hundreds of thousands of Euros in CAPEX based on a report that simply echoes our own staff's opinions back to us wrapped in broken Monte Carlo math?

---

### 4. WHAT IS GENUINELY IMPRESSIVE ABOUT THIS REPORT?

Despite its quantitative and templating flaws, the report has three notable strengths:
1. **IT/OT Convergence & Shadow IT Visibility:** The identification of plant-floor operational risks—specifically workers connecting unauthorized cameras and Wi-Fi access points directly into the concrete batching control networks—is a high-value finding. It bridges the gap between physical facilities security and NIS2/ISO 27001 cybersecurity compliance.
2. **Cross-Layer Architectural Correlation:** The consultants did not just look at the physical room; they connected the physical electrical risk to the virtualization layer. Pointing out that the 500m dark fiber ring and dual-room setup is a "false redundancy" because the HPE SimpliVity nodes cannot handle a 100% workload evacuation during a single-site power loss is a brilliant, board-level insight.
3. **Organizational Friction Diagnosis:** Highlighting the operational silos between Factory Maintenance (who control plant power shutdowns) and IT Operations, alongside the lack of BMS-to-Zabbix telemetry integration, hits the nail on the head regarding how industrial data centers actually fail in the real world.

---

### 5. FINAL GRADE & ACTIONABLE RECOMMENDATION

* **FINAL GRADE:** **5.5 / 10** 
*(A strong 7.5 for qualitative strategic insights into industrial IT/OT risks, dragged down to a 5.5 by superficial electromechanical detail, copy-paste template errors, and contradictory Open FAIR math).*

* **ONE ACTIONABLE RECOMMENDATION FOR THE BOARD:**
**Withhold final sign-off on this document and instruct NTT DATA to reconcile the Open FAIR recovery time contradictions (the 21.7h P90 vs. 77.4h SLE discrepancy) and append a verified Electrical & Mechanical Single-Line Diagram (SLD) inventory for Sant Vicenç dels Horts.** Before spending CAPEX on new data center builds or DCIM software, Molins must know the exact kVA load, UPS battery state-of-health, generator ATS switching topology, and fire suppression agent status of CPD 1 and CPD 2.