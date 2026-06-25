/**
 * Sovereign Strategic Terminal V11 - Narrative Orchestrator
 * Ensures all UI elements are updated with data from TerminalState.
 */

window.addEventListener('terminal-ready', () => {
    const state = window.TerminalState;
    console.log("📜 Narrative Orchestrator Dispatched", state.apex);

    // ACT 1: APEX (Headline & Narrativa)
    const apex = state.apex;
    safeSetText('ui-headline', apex.headline);
    safeSetText('ui-narrative', apex.narrative);
    safeSetText('ui-score', apex.maturity);
    safeSetText('ui-risks', apex.risks);

    // ACT 2: AS-IS (Burning Platform Risks)
    renderBurningPlatform();

    // ACT 3: TO-BE (Value Targets)
    renderRadar();
    renderBusinessImpacts();

    // ACT 4: TO-DO (Roadmap)
    renderRoadmap();

    console.log("✅ Strategic Narrative V11.1 Fully Operational");
});

function renderBurningPlatform() {
    const state = window.TerminalState;
    const container = document.getElementById('details-panel'); // Reusing panel for static bp if map not active
    const risks = state.burningPlatform;

    if (risks.length > 0) {
        // Just adding a summary if no node is selected
        container.innerHTML = `
            <p class="label-text">Strategic_Friction</p>
            <div style="margin-top:2rem" class="custom-scrollbar">
                ${risks.map(r => `
                    <div style="margin-bottom:1.5rem">
                        <p class="data-text" style="color:var(--crimson)">// ${r.theme.toUpperCase()}</p>
                        <p style="font-size:0.75rem; color:#D1D5DB; margin-top:0.5rem">${r.business_risk}</p>
                    </div>
                `).join('')}
            </div>
        `;
    }
}

function renderBusinessImpacts() {
    const state = window.TerminalState;
    const container = document.getElementById('ui-impacts');
    if (!container) return;

    const impacts = state.businessImpacts;
    container.innerHTML = impacts.map(i => `
        <li style="margin-bottom:1.5rem; display:flex; gap:1rem; align-items:start">
            <span style="color:var(--mint); font-family:var(--font-data)">></span>
            <p class="insight-text" style="font-size:1.1rem; color:#E6E7ED">${i}</p>
        </li>
    `).join('');
}

function renderRadar() {
    const state = window.TerminalState;
    const ctx = document.getElementById('targetRadarChart');
    if (!ctx) return;

    const towers = state.heatmap;
    if (towers.length === 0) return;

    new Chart(ctx, {
        type: 'radar',
        data: {
            labels: towers.map(t => t.id),
            datasets: [
                {
                    label: 'Current (AS-IS)',
                    data: towers.map(t => parseFloat(t.score)),
                    borderColor: '#EE6666',
                    backgroundColor: 'rgba(238, 102, 102, 0.05)',
                    borderWidth: 1,
                    pointRadius: 0
                },
                {
                    label: 'Target (TO-BE)',
                    data: towers.map(t => 4.5),
                    borderColor: '#86EFAC',
                    backgroundColor: 'rgba(134, 239, 172, 0.1)',
                    borderWidth: 2,
                    pointRadius: 4
                }
            ]
        },
        options: {
            scales: {
                r: {
                    min: 0, max: 5,
                    grid: { color: 'rgba(255,255,255,0.05)' },
                    pointLabels: { color: '#8B949E', font: { size: 10, family: 'IBM Plex Mono' } },
                    ticks: { display: false }
                }
            },
            plugins: { legend: { labels: { color: '#fff', font: { family: 'IBM Plex Mono', size: 10 } } } }
        }
    });
}

function renderRoadmap() {
    const state = window.TerminalState;
    const container = document.getElementById('todo-roadmap');
    if (!container) return;

    const horizons = state.roadmap;
    const waves = [
        { k: "quick_wins_0_3_months", l: "Wave 0: Foundation", c: "crimson" },
        { k: "year_1_3_12_months", l: "Wave 1: Transformation", c: "cobalt" },
        { k: "year_2_12_24_months", l: "Wave 2: Scaling", c: "mint" }
    ];

    container.innerHTML = waves.map(w => {
        const projs = horizons[w.k] || [];
        if (projs.length === 0) return "";
        return `
            <div style="grid-column: 1 / -1; margin-top: 4rem;">
                <p class="eyebrow" style="color:var(--${w.c})">// ${w.l}</p>
                <div class="project-grid" style="margin-top:1.5rem">
                    ${projs.map(p => `
                        <div class="project-card">
                            <strong class="data-text" style="font-size:0.8rem">${p.title.toUpperCase()}</strong>
                            <p style="margin-top:1rem; line-height:1.4">${p.business_case}</p>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }).join('');
}

function safeSetText(id, text) {
    const el = document.getElementById(id);
    if (el) el.innerText = (text !== undefined && text !== null && text !== "") ? text : "--";
}

function safeSetHTML(id, html) {
    const el = document.getElementById(id);
    if (el) el.innerHTML = html || "";
}
