**MEMORANDUM**

**TO:** Board of Directors, Cementos Molins  
**FROM:** External Principal Enterprise Network Architect (Dual CCIE / SD-WAN Specialist)  
**DATE:** October 2026  
**SUBJECT:** Independent Peer-Review and Technical Audit of *Anexo Técnico: Redes y Conectividad (AS-IS)*  

---

### 1. OVERALL VERDICT

I **DEMAND REVISIONS** to this deliverable before it is accepted by the Board or used as the financial baseline for CAPEX allocation in *Tomo 2*. While the qualitative architectural discovery is exceptionally perceptive and accurately exposes critical single points of failure (SPOFs) in the Sant Vicenç dels Horts core, the document is undermined by severe mathematical discrepancies in its maturity scoring, blatant copy-paste errors from other infrastructure towers, a complete omission of the global network footprint (LATAM, North Africa, SECIL), and a deeply flawed actuarial risk model that grossly overestimates the financial blast radius of single-branch outages.

---

### 2. TECHNICAL REALISM OF THE DIAGNOSTIC

The report is a "Frankenstein" deliverable: half of it is brilliant, bespoke field engineering, and the other half is unedited, automated consulting boilerplate. 

**Where it hits the mark (True Operational Reality):**
The consultant who conducted the interviews clearly understood Molins' Spanish infrastructure. The characterization of the **"Sant Vicenç-centric" hub-and-spoke topology**—forcing all branch traffic to trombone back to the main factory only to exit via dark fiber to Equinix Barcelona and onward to Google Cloud (Amsterdam) via Equinix Fabric—is a textbook analysis of organic enterprise network debt. Furthermore, the breakdown of the branch archetypes (*Proxa* "Size S" ready-mix plants, *Precast* plants clinging to legacy RODCs and file servers from the ADSL era, and *Construction Solutions* offices) reflects genuine, boots-on-the-ground discovery. Identifying the "Bus Factor = 1" (a single engineer in Croatia acting as both Principal Network Architect and DBA, relying on an obsolete MoinMoin wiki) is a critical operational finding.

**Where it fails (Template Laziness and Scope Blindness):**
1. **Geographical Amnesia:** Cementos Molins is a €1.144B multinational operating across Spain, Portugal (SECIL), Latin America, and North Africa. This report reads as if Molins is a regional Catalan business. There is zero mention of international MPLS/IPsec transit, cross-border WAN latency, peering architectures with SECIL, or regional cloud hubs in the Americas. 
2. **Shallow Routing & Switching Forensics:** For a specialized network audit, the analysis of the Data Center & Campus LAN is shockingly superficial. In Section 3.2.1, the text contains a literal unedited template string: *"Carencia de telemetría continua de ancho de banda... Exposición operativa y riesgo de interrupción del servicio"* (missing even a period). Where is the analysis of the Spanning Tree Protocol (STP) topology vs. EVPN/VXLAN? What is the state of dynamic routing (OSPF/BGP) between the branches and the Sant Vicenç core? What specific switch models in the plants are End-of-Life/End-of-Support (EoL/EoS), and how are they surviving dust, heat, and vibration without industrial-grade IP67 enclosures?
3. **Methodology Contamination:** In Table 2 (Applied Standards), the report cites **SNIA Storage Security / ISO/IEC 27040** for *"immutable retention and storage resilience."* That belongs in the Storage/Backup annex, not the Network architecture report. This proves the consultancy recycled a master template without rigorous quality assurance.
4. **Internal Scoring Contradictions:** In the Executive Summary and Table 4, *Data Center & Campus Network* is scored at **2.50**, yielding a global weighted average of **1.92**. However, in Section 3.2.1 and Table 5, the auditor "calibrates" this exact pillar down to **1.25** due to a lack of trunk telemetry. If this pillar is 1.25, the global weighted score of 1.92 is mathematically impossible (it would drop to ~1.64). 

---

### 3. SCRUTINY OF RISK FORMULATION & NUMBERS

The application of the Open FAIR™ framework and Monte Carlo simulations gives this report a veneer of actuarial precision. However, when subjected to cold network engineering logic, the numbers collapse.

#### A. Critique of the Numbers (ALE & P90)
* **The Base Hourly Cost Fallacy (€13,061.29/h):** Cementos Molins generates €1.144B annually. Divided by 8,760 hours (cement kilns run 24/7/365), the gross revenue rate is ~€130,593/hour. Assuming a 10% net operational margin impact or direct IT-dependent value-add, a global baseline of €13,061/hour for a **total corporate blackout** is a reasonable, conservative metric.
* **The Blast Radius Fallacy (The Fatal Flaw in RVS02):** Look closely at risk **RVS02** (Single CPE/Firewall SPOF at ready-mix/precast plants), which represents the #1 risk in the report (€84,414/year ALE, €234,058 Single Loss Expectancy). To calculate that €234,058 SLE, the model assumes a **25.6-hour outage costing €9,142/hour—which is 70% of the global corporate downtime cost!** 
  * *Engineering Reality Check:* If a single perimeter firewall dies at a "Size S" Proxa concrete plant, **it does not halt 70% of Cementos Molins' global operations.** It isolates *one* small batching plant. Furthermore, all those single firewalls across 20+ branches do not fail simultaneously on the same day every 2.8 years. Applying 70% of the global enterprise hourly burn rate to a single branch CPE failure is actuarial malpractice.
* **The P90 Extreme Scenario (€685,148 / 21.3 hours):** The report claims that a simultaneous core control-plane partition and WAN outage requires 21.3 hours to recover because engineers must *"check that no critical data has been corrupted."* Networks are transport mechanisms; they do not corrupt data at rest. Moreover, the model claims **€406,911 in emergency external consulting fees** for a 21-hour outage. No Tier-1 vendor (Cisco TAC, Palo Alto, Fortinet, or NTT Data) charges €400,000 for less than a day of emergency incident response. Furthermore, why does a combined catastrophic failure take 21.3 hours to fix, whereas a single branch firewall replacement (RVS02) takes 25.6 hours? The MTTR logic is inverted.

#### B. Credibility of Risk Scenarios (How a Smart Client Engineer Will Shoot Them Down)
If I were Molins' internal Lead Architect (or the engineer in Croatia), I would dismantle RVS01 and RVS05 in five minutes during the steering committee meeting:
1. **RVS01 (Lack of trunk telemetry/oversubscription monitoring):** The report claims that simply *not having continuous bandwidth telemetry* on campus trunks will cause a **20.8-hour outage** costing €108,670 every 4.4 years. A smart engineer will rightly object: *"Lack of SNMP/sFlow monitoring does not cause a 21-hour blackout. At worst, link oversubscription causes micro-bursts, TCP retransmissions, and voice jitter. Even if a trunk saturates completely, clearing the congestion takes minutes via CLI, not 21 hours."*
2. **RVS05 (Lack of WAF / L4-L7 Load Balancing):** Identical copy-paste math to RVS01 (exactly 20.8h, €5,224/h, 4.4 years = €108,670 SLE). The internal team will point out that Molins is a B2B heavy materials manufacturer whose core ERP (SAP) is consumed internally via private Equinix Fabric, not a B2C e-commerce retailer reliant on public APIs. Claiming that the absence of a redundant WAF will cause a 40% global operational paralysis for 21 hours is generic fear-mongering.

#### C. Budget Defense Objections
If I were the CFO defending the budget, I would freeze approval and ask:
* *"Why are we using identical MTTR (20.8h), identical frequency (4.4 years), and identical financial impact (40% = €5,224/h) for two completely unrelated technical problems (Campus LAN telemetry in RVS01 and Cloud WAF in RVS05)? Are these real Monte Carlo simulations, or did your consultants hardcode default numbers into a spreadsheet?"*
* *"How can a single concrete plant firewall failure (RVS02) cost us €234,000, when the entire annual IT budget for a 'Size S' plant is a fraction of that, and the plant driver can use a 4G/5G cellular hotspot to print delivery notes in an emergency?"*

---

### 4. WHAT IS GENUINELY IMPRESSIVE ABOUT THIS REPORT?

Despite the mathematical flaws in the risk modeling, the consultant who performed the **qualitative architectural and organizational discovery** deserves high praise for three specific insights:

1. **Unmasking the "500-Meter DR Illusion" (RVS04):** Many enterprises delude themselves into thinking they have Disaster Recovery because they have two server rooms on the same campus. The auditor rightly calls out that having the Primary and Secondary CPDs separated by 500 meters inside a heavy industrial cement factory—connected by a single physical fiber duct—is merely local High Availability (HA), not DR. A single civil works excavator strike or substation fire takes out Molins globally.
2. **The Sant Vicenç "Cloud Trombone" (RVS03):** The report brilliantly articulates the contradiction of Molins' cloud strategy: investing in cutting-edge, low-latency Equinix Fabric to reach GCP in Amsterdam, while anchoring the entire physical entry point to a legacy factory floor in Sant Vicenç. If the factory loses power or fiber, all remote branches lose access to the cloud. Moving the SD-WAN hubs and cloud peering edge directly into the neutral Equinix Tier-III facility in Barcelona is the single most valuable architectural insight in this document.
3. **Organizational Courage:** Calling out the structural dysfunction between the newly formed Operations/SAU team and the Infrastructure Manager (reporting to Aleix), alongside the critical key-person dependency on the Croatian engineer/DBA, shows the auditors were not afraid to highlight political and human-capital realities that directly impact MTTR.

---

### 5. FINAL GRADE & ACTIONABLE RECOMMENDATION

* **FINAL GRADE:** **6.0 / 10**  
  *(Architecture & Operational Discovery: 8.5/10 | Actuarial Math & Document QA: 3.5/10)*

* **ONE ACTIONABLE RECOMMENDATION FOR THE BOARD:**  
  **Reject the financial risk quantifications as currently written and mandate a "Blast-Radius Recalibration" before proceeding to the Tomo 2 (Target Architecture & Investment) phase.** Instruct the consulting partner to:
  1. Scrub the document of copy-paste errors (remove SNIA storage standards, fix the Section 3.2.1 incomplete text, and reconcile the 2.50 vs. 1.25 Campus score discrepancy).
  2. Recalculate the Open FAIR™ models by separating **Global Core SPOFs** (Sant Vicenç CPD, Equinix transit, Core Routing—which genuinely risk €9k–€13k/hour) from **Edge/Branch SPOFs** (Proxa/Precast CPEs and plant switches—which only impact 1% to 3% of global revenue per event, even if they occur more frequently). 
  
  Once the math reflects physical network reality, prioritize CAPEX immediately on **decoupling the WAN/Cloud Edge from the Sant Vicenç factory floor into Equinix Barcelona**, and deploying dual-ISP SD-WAN with cellular (4G/5G) failover at the plants.