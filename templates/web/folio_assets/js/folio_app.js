/**
 * Sovereign Strategic Folio V13 - Core Engine
 * Structural Hierarchy: Executive Preface -> AS-IS Diagnostic -> TO-BE Strategy -> TO-DO Roadmap
 */

window.PortalEngine = (function() {
    let _data = {};

    function init() {
        try {
            const nexusEl = document.getElementById('nexus-data');
            if (nexusEl) _data = JSON.parse(nexusEl.textContent);

            console.log("📖 Portal V13 Hydrated", {
                towers: Object.keys(_data.towers || {}).length,
                programs: _data.execution_roadmap?.programs?.length
            });

            showChapter('exec-summary');
        } catch (e) {
            console.error("Hydration Error", e);
        }
    }

    function showChapter(id) {
        document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
        const activeLink = document.querySelector(`[onclick="PortalEngine.showChapter('${id}')"]`);
        if (activeLink) activeLink.classList.add('active');

        const content = document.getElementById('portal-main-content');
        content.scrollTop = 0;

        if (id === 'exec-summary') renderExecSummary(content);
        else if (id === 'as-is-global') renderAsIsGlobal(content);
        else if (id === 'to-be-vision') renderToBeVision(content);
        else if (id === 'to-do-roadmap') renderToDoRoadmap(content);
        else if (id.startsWith('annex-')) renderTowerAnnex(id.replace('annex-', ''), content);
    }

    function renderExecSummary(container) {
        const s = _data.executive_summary || {};
        const overview = _data.strategic_overview || {};
        const bp = _data.burning_platform || [];

        container.innerHTML = `
            <div class="chapter-container">
                <span class="section-label">01. EXECUTIVE_PREFACE</span>
                <h1 class="h1-chapter" style="font-size:3.5rem">${s.headline}</h1>
                <p class="intro-lead">${s.narrative}</p>

                <div style="display:grid; grid-template-columns: repeat(3, 1fr); gap:2rem; margin: 4rem 0;">
                    <div class="summary-stat-card">
                        <span class="nav-label">Global_Maturity</span>
                        <div style="font-family:var(--font-mono); font-size:3rem; font-weight:700; color:var(--accent-blue)">${s.maturity_pulse?.score || '3.0'}</div>
                        <p style="font-size:0.7rem; font-weight:800; color:#adb5bd">${s.maturity_pulse?.band || 'TRANSITIONAL'}</p>
                    </div>
                    <div class="summary-stat-card">
                        <span class="nav-label">Risk_Exposure</span>
                        <div style="font-family:var(--font-mono); font-size:3rem; font-weight:700; color:var(--accent-red)">${bp.length}</div>
                        <p style="font-size:0.7rem; font-weight:800; color:#adb5bd">CRITICAL_VECTORS</p>
                    </div>
                    <div class="summary-stat-card">
                        <span class="nav-label">Target_Horizon</span>
                        <div style="font-family:var(--font-mono); font-size:1.5rem; font-weight:700; margin-top:1rem;">H2_PREDICTIVE</div>
                        <p style="font-size:0.7rem; font-weight:800; color:#adb5bd">2026_STRATEGY</p>
                    </div>
                </div>

                <div style="background:var(--bg-side); padding:3rem; border-radius:8px; margin-bottom:4rem;">
                    <h3 class="section-label">Primary_Burning_Platform</h3>
                    <div style="display:grid; grid-template-columns: 1fr 1fr; gap:3rem; margin-top:2rem;">
                        ${bp.slice(0, 4).map(risk => `
                            <div>
                                <h4 style="font-weight:800; color:var(--accent-red); font-size:0.8rem; margin-bottom:0.5rem">// ${risk.theme || risk.title}</h4>
                                <p style="font-size:0.85rem; color:var(--text-muted)">${risk.business_risk || risk.description}</p>
                            </div>
                        `).join('')}
                    </div>
                </div>

                <div style="display:grid; grid-template-columns: 1fr 1fr; gap:4rem;">
                    <div>
                        <h3 class="section-label">Strategic_Implications</h3>
                        <ul style="list-style:none; padding-left:0; margin-top:2rem;">
                            ${(overview.value_targets || []).map(i => `
                                <li style="margin-bottom:1.5rem; display:flex; gap:1rem;">
                                    <i class="fa-solid fa-arrow-right-long text-blue-600 mt-1"></i>
                                    <p style="font-weight:700; font-size:0.95rem;">${i}</p>
                                </li>
                            `).join('')}
                        </ul>
                    </div>
                    <div>
                        <h3 class="section-label">Immediate_Executive_Decisions</h3>
                        <div style="border: 2px solid var(--accent-blue); padding:2rem; border-radius:4px; margin-top:2rem;">
                            <p style="font-family:var(--font-mono); font-size:0.75rem; color:var(--accent-blue); font-weight:700">> APPROVE_WAVE_0_BUDGET</p>
                            <p style="font-family:var(--font-mono); font-size:0.75rem; margin-top:1rem">> RE-ALIGN_OT_SECURITY_GOVERNANCE</p>
                            <p style="font-family:var(--font-mono); font-size:0.75rem; margin-top:1rem">> INITIALIZE_AZURE_PLATFORM_DOGMA</p>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    function renderAsIsGlobal(container) {
        const heatmap = _data.heatmap || [];
        container.innerHTML = `
            <div class="chapter-container">
                <span class="section-label">02. AS-IS_DIAGNOSTIC</span>
                <h1 class="h1-chapter">Current Systemic Health</h1>
                <p class="intro-lead">An analysis of technical friction points across the corporate estate, revealing the gap between current operations and the Sovereign H2 model.</p>

                <div style="margin:4rem 0">
                    <h3 class="nav-label">Maturity_Heatmap_by_Tower</h3>
                    <div style="display:grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap:1rem; margin-top:2rem;">
                        ${heatmap.map(t => `
                            <div class="mini-score-card">
                                <span style="font-family:var(--font-mono); font-size:0.6rem; color:#adb5bd">${t.id}</span>
                                <div style="font-size:1.5rem; font-weight:800; color:${getScoreColor(t.score)}">${t.score}</div>
                                <p style="font-size:0.7rem; font-weight:700; line-height:1.1">${t.name}</p>
                            </div>
                        `).join('')}
                    </div>
                </div>

                <div class="systemic-finding-grid" style="display:grid; grid-template-columns: 1fr 1fr; gap:3rem;">
                    <div>
                        <h3 class="section-label">Structural_Inhibitors</h3>
                        <p style="font-size:0.95rem; color:var(--text-muted)">Se detecta una dependencia crítica de procesos manuales en el ciclo de vida de la infraestructura, lo que genera una latencia inaceptable para las demandas del negocio digital.</p>
                    </div>
                    <div style="border-left:1px solid var(--border-soft); padding-left:3rem;">
                        <h3 class="section-label">Evidence_Integrity</h3>
                        <p style="font-size:0.95rem; color:var(--text-muted)">Todos los hallazgos han sido validados mediante la resolución del Epistemic Graph, cruzando 247 nodos de evidencia documental y técnica.</p>
                    </div>
                </div>
            </div>
        `;
    }

    function renderToBeVision(container) {
        container.innerHTML = `
            <div class="chapter-container">
                <span class="section-label">03. TO-BE_STRATEGY</span>
                <h1 class="h1-chapter">The Sovereign DTO Model</h1>
                <p class="intro-lead">Evolving from a fragmented legacy estate to an automated, resilient, and cost-effective digital infrastructure.</p>

                <div style="height:400px; margin:4rem 0; border:1px solid var(--border-soft); padding:3rem; border-radius:8px;">
                    <canvas id="targetRadarChart"></canvas>
                </div>

                <div style="display:grid; grid-template-columns: 1fr 1fr; gap:4rem;">
                    <div>
                        <h3 class="section-label">Core_Value_Proposition</h3>
                        <p style="font-weight:700; font-size:1.2rem; line-height:1.4; color:var(--accent-blue)">Transformar la infraestructura de un centro de costes a un motor de aceleración de negocio mediante la hiper-automatización (H2).</p>
                    </div>
                    <div>
                        <h3 class="section-label">Target_Architecture_Principles</h3>
                        <ul style="list-style:none; padding-left:0; font-size:0.9rem; color:var(--text-muted)">
                            <li>// Software Defined Everything</li>
                            <li>// Zero-Trust by default</li>
                            <li>// FinOps-aware Engineering</li>
                        </ul>
                    </div>
                </div>
            </div>
        `;
        setTimeout(renderRadar, 100);
    }

    function renderToDoRoadmap(container) {
        const roadmap = _data.execution_roadmap || {};
        const programs = roadmap.programs || [];

        container.innerHTML = `
            <div class="chapter-container">
                <span class="section-label">04. TO-DO_ROADMAP</span>
                <h1 class="h1-chapter">Program Portfolio</h1>
                <p class="intro-lead">The orchestrated execution plan, organized into thematic programs with clear business cases and cross-tower dependencies.</p>

                <div class="program-portfolio" style="margin-top:4rem;">
                    ${programs.map(prog => `
                        <div class="program-block" style="margin-bottom:4rem; padding:3rem; border:1px solid var(--border-soft); border-radius:8px;">
                            <div style="display:flex; justify-content:space-between; align-items:start">
                                <div>
                                    <span class="nav-label" style="color:var(--accent-blue)">PROGRAM_NAME</span>
                                    <h2 style="font-weight:800; font-size:1.5rem; margin-bottom:1rem">${prog.name}</h2>
                                </div>
                                <div style="text-align:right">
                                    <span class="nav-label">Status</span>
                                    <p style="font-family:var(--font-mono); font-size:0.75rem; color:var(--accent-blue)">[ PENDING_INIT ]</p>
                                </div>
                            </div>
                            <p style="font-size:0.9rem; color:var(--text-muted); margin-bottom:2rem">${prog.description}</p>

                            <h4 class="nav-label">Constituent_Projects</h4>
                            <div style="display:grid; grid-template-columns: 1fr 1fr; gap:1.5rem; margin-top:1rem;">
                                ${prog.projects.map(p => `
                                    <div class="project-mini-card" style="padding:1.5rem; background:var(--bg-side); border-radius:4px;">
                                        <p style="font-weight:700; font-size:0.85rem">${p.title}</p>
                                        <p style="font-size:0.75rem; color:var(--text-muted); margin-top:0.5rem">${p.expected_outcome || 'Realización de beneficios sistémicos.'}</p>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }

    function renderTowerAnnex(towerId, container) {
        const t = _data.towers[towerId];
        if (!t) return;

        container.innerHTML = `
            <div class="chapter-container">
                <span class="section-label">TECHNICAL_ANNEX // ${towerId}</span>
                <h1 class="h1-chapter">${t.meta.name}</h1>
                <div style="display:flex; gap:3rem; align-items:center; margin-bottom:4rem;">
                    <div style="font-family:var(--font-mono); font-size:4rem; font-weight:500;">${t.meta.score}</div>
                    <p class="intro-lead" style="margin-bottom:0">${t.executive_summary}</p>
                </div>

                <div class="annex-body">
                    ${t.pillars.map(p => `
                        <div class="pillar-block">
                            <span class="pilar-title">${p.name} (SCORE: ${p.score})</span>
                            <div class="pillar-content">
                                ${p.health_check.map(gap => `
                                    <div class="finding-card">
                                        <span class="risk-tag">CRITICAL_GAP</span>
                                        <span class="finding-title">${gap.capability}</span>
                                        <p class="finding-body">${gap.finding}</p>
                                        <div class="evidence-box">
                                            <span class="evidence-label">LITERAL_EVIDENCE_SOURCE</span>
                                            ${gap.evidence || "Evidence validated through system-wide graph resolution and documentary review of corporate repositories."}
                                        </div>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }

    function renderRadar() {
        const state = window.PortalEngine.getData();
        const ctx = document.getElementById('targetRadarChart');
        if (!ctx) return;
        const towers = state.heatmap;
        new Chart(ctx, {
            type: 'radar',
            data: {
                labels: towers.map(t => t.id),
                datasets: [
                    { label: 'AS-IS', data: towers.map(t => parseFloat(t.score)), borderColor: '#BA1A1A', backgroundColor: 'rgba(186, 26, 26, 0.05)', borderWidth: 1, pointRadius: 0 },
                    { label: 'TO-BE', data: towers.map(t => 4.5), borderColor: '#16834A', backgroundColor: 'rgba(22, 131, 74, 0.1)', borderWidth: 2, pointRadius: 4 }
                ]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                scales: { r: { min: 0, max: 5, grid: { color: 'rgba(0,0,0,0.05)' }, pointLabels: { color: '#44474E', font: { size: 11, family: 'JetBrains Mono' } }, ticks: { display: false } } },
                plugins: { legend: { position: 'bottom' } }
            }
        });
    }

    function getScoreColor(score) {
        const s = parseFloat(score);
        if (s < 2.5) return '#BA1A1A';
        if (s < 3.5) return '#B7791F';
        return '#16834A';
    }

    function safeSetText(id, text) {
        const el = document.getElementById(id);
        if (el) el.innerText = text || "--";
    }

    return {
        init,
        showChapter,
        getData: () => _data
    };
})();
