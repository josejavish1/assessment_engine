**MEMORANDUM TO THE BOARD OF DIRECTORS – CEMENTOS MOLINS**
**FROM:** External Audit Practice – Global Head of ITSM & SRE (ITIL 4 Master)
**SUBJECT:** Peer-Review & Technical Audit of Deliverable `Molins_202610_Anexo_07_Operaciones_ITSM_ASIS.docx`

---

### 1. OVERALL VERDICT
I **DEMAND REVISIONS** to this deliverable before it can be accepted as a baseline for strategic CAPEX/OPEX allocation. While the qualitative operational diagnostic is remarkably perceptive and grounded in the gritty reality of Cementos Molins’ plant infrastructure, the quantitative risk modeling (Open FAIR™) and the internal mathematical consistency of the document are fundamentally broken, exhibiting severe consulting-template artifacts that would be immediately dismantled by a sharp Chief Financial Officer or Senior Engineer.

---

### 2. TECHNICAL REALISM OF THE DIAGNOSTIC
The qualitative diagnostic section is **highly authentic** and reflects the exact operational dysfunction typical of a €1.14B industrial conglomerate that has grown via M&A (e.g., the SECIL acquisition) while starving its core IT operations of headcount. It does not read like a generic template; the consultants clearly interviewed the engineers in the trenches.

**Where the diagnostic hits the mark:**
* **The "Canary-in-the-Coal-Mine" Anti-Pattern:** The revelation that the infrastructure team deliberately provisions Linux VMs with minimal disk and memory ("muy justitos") so that unoptimized Apache logs (1GB) crash the server early—forcing a manual log purge rather than configuring `logrotate` or fixing the underlying SQL `SELECT` queries—is a textbook, horrifyingly real example of Level 1 reactive toil. 
* **M&A Indigestion (SECIL / NOS):** Identifying that the Portuguese operations (SECIL) run as an unintegrated "black box" under telecom provider NOS—disconnected from Molins' service catalog—accurately highlights a massive governance blind spot.
* **The "SAU" Organizational Silo:** Calling out the newly created Operations/Service Desk unit (SAU) as an isolated silo operating in parallel to the 5-person core infrastructure team explains why Tier-1 triage is failing and why senior engineers spend >40% of their time on L1 firefighting.
* **Legacy Debt ("Ensalada de Versiones"):** Running end-of-life CentOS 5 and CentOS 6 in production without maintenance windows because the business won't allow plant downtime is the quintessential manufacturing IT dilemma.

**Where the diagnostic falls short (My Audit Lens):**
* **CMDB & Discovery:** The report assigns a 1.25 to Change/CMDB, yet spends almost zero time detailing the actual state of the CMDB. What tool is being used? How is asset discovery handled across OT/IT boundaries in the plants? You cannot fix Incident Triage or Change Management without knowing how Configuration Items (CIs) are mapped to business services like *Prenet* (the Precast mini-ERP).
* **Monitoring Fragmentation & Score Inflation:** The report awards **2.50/5.0** to *Observability, Event Management, and AIOps*. This is wildly generous. Having Zabbix run basic bash scripts to restart dead services while engineers manually kill blocked DB sessions and empty Apache logs is **not** 2.50 maturity, nor does it have anything to do with AIOps. Furthermore, there is no architectural breakdown of modern observability stacks (e.g., Prometheus/Loki/Grafana for metrics and log aggregation) versus legacy Zabbix polling. If they are manually purging 1GB Apache logs, centralized log management is clearly non-existent.

---

### 3. SCRUTINY OF RISK FORMULATION & NUMBERS

The quantitative section (`Evaluación Económica de Riesgos`) is where this report loses executive credibility. It attempts to dress up basic labor-hour multiplication in the prestigious clothing of "Open FAIR™" and "10,000 Monte Carlo iterations," resulting in glaring mathematical contradictions.

#### A. Opinion on the Numbers (ALE & P90)
* **The €91,200 ALE is Laughably Low for Business Risk, yet Mathematically Manipulated as "Toil":** For a company generating €1.144 Billion in revenue (~€130,000 per hour globally), an Annualized Loss Exposure of €91,200 is a rounding error. Why is it so low? Because the consultants **only modeled internal IT labor toil** (e.g., 8 hours of engineering time × €65/hr = €520 per event), completely omitting Primary Business Loss (plant downtime, halted cement trucks, unbilled concrete). 
* **The P90 Scenario (€132,240 for 8.3 hours of downtime) is Unrealistic:** In the P90 severe outage scenario (simultaneous central DB corruption and incident queue saturation), the report claims 8.3 hours of commercial and operational paralysis will cost Molins €107,888 in business interruption (~€13,000/hour). If central ERP/billing and plant scales (*básculas en Torre 10*) are down across Spain for an entire shift, the financial impact of halted logistics, spoiled perishable concrete in transit, and SLA penalties will easily exceed **€350,000 to €500,000**.

#### B. How a Smart Client Engineer or CFO Will Shoot This Down
If I were defending the company's budget, I would reject the financial business case on the spot by pointing out four fatal flaws in the tables:

1. **The Heatmap Contradiction (Table 7 vs. Tables 11–15):**
   In Table 7 (Risk Matrix), **all five risks (RVS01–RVS05)** are plotted in row **TEF 2** (0.1 to 0.5 events/year—meaning once every 2 to 10 years) and columns **LM 2 / LM 3** (€13,000 to €208,000 per event). 
   However, in the detailed risk cards (Tables 11–15), those exact same risks are calculated using **TEF = 30 to 76 events/year** (which is **TEF 5**) and **SLE = €260 to €520 per event** (which is **LM 1**). The heatmap and the actuarial cards come from two completely different universes.
2. **The RVS03 "Ransomware for €520" Absurdity (Table 11):**
   RVS03 describes the risk of unpatched CentOS 5/6 servers leading to *“zero-day exploits, INCIBE alerts, ransomware compromise, or unplanned stops of production clusters in Sant Vicenç dels Horts.”* Yet, the financial calculation values this event at **€520 (8 hours of manual toil)** occurring **76 times a year**. You do not get hit by ransomware or suffer a plant cluster outage 76 times a year for €520 a pop. The narrative describes a catastrophic cybersecurity/availability event, while the math calculates routine manual patching toil.
3. **The Scoring Contradiction (Table 4 vs. Text & Table 5):**
   In the text and Table 5, the auditor proudly states they downgraded *Service Desk & Incident Management* from the client's self-assessment of 2.25 down to **1.25**. Yet, in Table 4 (the master summary table), the score is still listed as **2.25**, and the overall average of **2.10** is calculated using 2.25! (`(2.50 + 2.25 + 1.25 + 2.00 + 2.50) / 5 = 2.10`). Had they used their calibrated score of 1.25, the global maturity would be **1.90**.
4. **The "40% Capacity" Math Fallacy:**
   The text states that the 5 core engineers spend *>40% of their capacity* fighting fires. Five engineers working 1,800 hours/year = 9,000 hours. 40% of 9,000 hours is **3,600 hours of toil**, which at €65/hr equals **€234,000/year** in wasted salary alone. Yet, the total sum of all SLE toil across all 5 risk cards (Tables 11–15) only adds up to **1,402 hours (€91,200)**. Even Table 6 contradicts this by saying Toil (`V_gamma`) is only €19,881. The numbers are completely disconnected from the operational narrative.

---

### 4. WHAT IS GENUINELY IMPRESSIVE ABOUT THIS REPORT?

Despite the broken math, the **operational forensics** in this document are top-tier. 
1. **Unvarnished Truth:** The consultants did not sugarcoat the internal politics. Pointing out that the new SAU (Service Desk) was set up outside the governance of the Infrastructure Lead, and exposing the bizarre practice of choking VM disk space to catch runaway Apache logs, shows deep technical probing.
2. **OT/IT Convergence Awareness:** The report correctly links IT service management failures directly to physical plant operations—specifically citing how fragmented ticket handling delays the resolution of *paradas en básculas de planta (Torre 10)* (weighbridge stops) and truck expedition queries. This is exactly what a manufacturing Board of Directors needs to hear.
3. **Calibrated Skepticism:** The methodology of contrasting "Client Self-Assessment" vs. "Calibrated Forensic Reality" (Table 5) is an excellent executive tool to break through middle-management optimism—provided they fix the math in Table 4 so the downgrade actually reflects in the final score.

---

### 5. FINAL GRADE & ACTIONABLE RECOMMENDATION

* **FINAL GRADE:** **6.0 / 10** *(8.5/10 for Qualitative Technical Forensics; 3.5/10 for Quantitative Rigor and Document QA).*

* **ONE ACTIONABLE RECOMMENDATION BEFORE BOARD PRESENTATION:**
  **Decouple "Internal Engineering Toil" from "Business Operational Risk" and fix the broken tables.** Instruct the consulting team to immediately scrub the document to fix the Table 4 score calculation (1.90 vs 2.10) and align the Table 7 Heatmap with the Risk Cards. More importantly, force them to split the financial model into two distinct metrics:
  1. **IT Operational Toil (OPEX Waste):** Quantify the 40% wasted capacity of the 5 engineers (~€234k/year) plus the hidden shadow-IT support in the plants to justify hiring/automation in the Service Desk.
  2. **True Business Value at Risk (ALE):** Model the actual financial cost of plant weighbridge stops (*básculas*), halted concrete dispatching (*Prenet*), and CentOS 5/6 security breaches to justify the CAPEX required for infrastructure modernization and CMDB/Observability tooling. Do not present a €520 "Ransomware/Plant Outage" card to the Board.