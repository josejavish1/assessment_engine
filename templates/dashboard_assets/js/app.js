/**
 * Sovereign Dashboard Initialization (Tier 1 Drill-Down Edition)
 */

let charts = { global: null, tower: null };
window.SovereignDashboard = {
    selectedTower: null,

    selectTower(towerId) {
        console.log(`🎯 Focusing on Tower: ${towerId}`);
        this.selectedTower = towerId;

        // Update UI Highlights
        document.querySelectorAll('.tower-card').forEach(el => {
            el.classList.toggle('highlighted', el.dataset.towerId === towerId);
            el.classList.toggle('dimmed', el.dataset.towerId !== towerId);
        });

        // Update Sankey
        const sankey = document.querySelector('sovereign-sankey');
        if (sankey) {
            sankey.filterByTower(towerId);
            document.getElementById('sankey-status').innerText = `Focused View: Tower ${towerId} Impact Nexus`;
        }

        // Optional: Filter Roadmap or other sections
    },

    resetNexus() {
        this.selectedTower = null;
        document.querySelectorAll('.tower-card').forEach(el => {
            el.classList.remove('highlighted', 'dimmed');
        });
        const sankey = document.querySelector('sovereign-sankey');
        if (sankey) {
            sankey.resetFilter();
            document.getElementById('sankey-status').innerText = `Global View: Resolving Systemic Impact Nexus`;
        }
    }
};

function initDashboard() {
    window.SovereignState.init();
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initDashboard);
} else {
    initDashboard();
}

window.addEventListener('sovereign-ready', () => {
    renderStaticUI();
    renderHeatmap();
    renderRoadmap();
    renderCharts();
    console.log("💎 Sovereign Dashboard v6.1 (Drill-Down) Ready");
});

function renderStaticUI() {
    const state = window.SovereignState;
    const strategy = state.strategy;

    safeSetText('ui-score', strategy.global_score);
    safeSetText('ui-headline', strategy.headline);

    const narrative = strategy.narrative || "";
    if (narrative.includes("PENDIENTE")) {
        safeSetHTML('ui-narrative', `<span class="text-rose-400 italic">Strategic analysis refinement in progress...</span>`);
    } else {
        safeSetText('ui-narrative', narrative);
    }

    const clientName = state.nexus.client_id || "CLIENT";
    document.querySelectorAll('.client-id-display').forEach(el => {
        el.innerText = clientName.toUpperCase();
    });

    const impactsList = document.getElementById('ui-business-impacts');
    if (impactsList && strategy.business_impacts) {
        impactsList.innerHTML = strategy.business_impacts.map(i => `
            <li class="text-[11px] text-slate-300 leading-tight flex items-start gap-3">
                <i class="fa-solid fa-circle-check text-emerald-500 mt-1 shrink-0"></i> ${i}
            </li>
        `).join('');
    }

    const bpContainer = document.getElementById('ui-burning-platform');
    if (bpContainer && strategy.burning_platform) {
        bpContainer.innerHTML = strategy.burning_platform.map(bp => `
            <div class="space-y-2">
                <h3 class="text-rose-400 font-black text-[10px] uppercase tracking-widest leading-tight">${bp.theme}</h3>
                <p class="text-slate-300 text-[10px] leading-relaxed font-medium text-justify">${bp.business_risk}</p>
            </div>
        `).join('<div class="h-4 border-b border-rose-500/10"></div>');
    }
}

function renderHeatmap() {
    const state = window.SovereignState;
    const container = document.getElementById('ui-heatmap');
    if (!container) return;

    // Use heatmap data from global payload for scores
    const towers = state.heatmap || [];

    container.innerHTML = towers.map(t => {
        const score = parseFloat(t.score);
        const colorClass = score < 2.5 ? 'border-l-rose-600' : (score < 3.5 ? 'border-l-amber-500' : 'border-l-sky-600');
        const scoreColor = score < 2.5 ? 'text-rose-500' : (score < 3.5 ? 'text-amber-500' : 'text-sky-400');

        return `
            <div onclick="window.SovereignDashboard.selectTower('${t.id}')" data-tower-id="${t.id}" class="tower-card glass p-5 rounded-2xl border-l-4 ${colorClass} shadow-lg group cursor-pointer transition-all active:scale-95">
                <div class="flex justify-between items-center">
                    <div>
                        <span class="text-[8px] font-black text-slate-500 mono uppercase mb-0.5 block tracking-widest">${t.id}</span>
                        <h3 class="text-white font-bold text-sm leading-tight group-hover:text-sky-400 transition-colors">${t.name}</h3>
                    </div>
                    <div class="text-2xl font-black font-mono tracking-tighter ${scoreColor}">${t.score}</div>
                </div>
            </div>
        `;
    }).join('');
}

function renderRoadmap() {
    const state = window.SovereignState;
    const container = document.getElementById('ui-roadmap');
    if (!container || !state.roadmap) return;

    container.innerHTML = state.roadmap.map(wave => {
        const label = wave.wave;
        const color = label.includes("0") ? "rose" : label.includes("1") ? "sky" : "emerald";

        return `
            <div class="space-y-8">
                <div class="flex items-center gap-6 border-b border-white/5 pb-4">
                    <div class="h-4 w-4 rounded-full bg-${color}-500 shadow-[0_0_15px_rgba(0,0,0,0.5)]"></div>
                    <h3 class="text-sm font-black text-white uppercase tracking-[0.4em] italic">${label}</h3>
                </div>
                <div class="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-6">
                    ${wave.projects.map(projId => {
                        // Resolve project label from topology
                        const node = state.dto.topology?.nodes.find(n => n.id === projId);
                        const title = node ? node.label : projId;

                        return `
                            <div class="proj-tile p-6 glass rounded-3xl border border-white/5 hover:border-${color}-500/50 flex flex-col justify-between group min-h-[160px] shadow-2xl relative overflow-hidden transition-all hover:-translate-y-2">
                                <div class="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-100 transition-opacity">
                                    <i class="fa-solid fa-rocket text-${color}-400 text-2xl"></i>
                                </div>
                                <b class="text-[11px] text-slate-100 leading-snug group-hover:text-${color}-400 transition-colors pr-6 uppercase font-black">${title.length > 80 ? title.substring(0, 77) + "..." : title}</b>
                                <div class="flex justify-between items-center mt-6 pt-6 border-t border-white/5">
                                    <span class="text-[8px] font-black text-slate-600 uppercase tracking-widest">${node?.tower_id || 'Global'}</span>
                                    <div class="h-6 w-6 rounded-full bg-white/5 flex items-center justify-center group-hover:bg-${color}-500/20 transition-colors">
                                        <i class="fa-solid fa-arrow-right text-[10px] text-slate-500 group-hover:text-${color}-400"></i>
                                    </div>
                                </div>
                            </div>
                        `;
                    }).join('')}
                </div>
            </div>
        `;
    }).join('');
}

function renderCharts() {
    const state = window.SovereignState;
    const ctx = document.getElementById('globalRadarChart');
    if (!ctx) return;

    if (charts.global) charts.global.destroy();

    const towers = state.heatmap || [];
    charts.global = new Chart(ctx.getContext('2d'), {
        type: 'radar',
        data: {
            labels: towers.map(t => t.id),
            datasets: [
                {
                    label: 'As-Is',
                    data: towers.map(t => parseFloat(t.score)),
                    backgroundColor: 'rgba(14, 165, 233, 0.2)',
                    borderColor: '#38bdf8',
                    borderWidth: 2,
                    pointRadius: 3
                },
                {
                    label: 'Target',
                    data: towers.map(t => parseFloat(t.target_maturity || 4.0)),
                    backgroundColor: 'transparent',
                    borderColor: 'rgba(16, 185, 129, 0.3)',
                    borderWidth: 1,
                    borderDash: [4, 4],
                    pointRadius: 0
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                r: {
                    min: 0, max: 5,
                    ticks: { display: false },
                    grid: { color: 'rgba(255,255,255,0.05)' },
                    pointLabels: { color: '#64748b', font: { weight: 'bold', size: 10, family: 'JetBrains Mono' } }
                }
            },
            plugins: { legend: { display: false }, datalabels: { display: false } }
        }
    });
}

function safeSetText(id, text) {
    const el = document.getElementById(id);
    if (el) el.innerText = text || "--";
}

function safeSetHTML(id, html) {
    const el = document.getElementById(id);
    if (el) el.innerHTML = html || "";
}
