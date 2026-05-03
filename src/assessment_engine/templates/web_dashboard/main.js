let DATA;
let charts = { global: null, tower: null };
let currentProgramFilter = null;

function init() {
    try {
        DATA = JSON.parse(document.getElementById('nexus-data').textContent);
        if(typeof Chart !== 'undefined') Chart.register(ChartDataLabels);
        document.getElementById('ui-score').innerText = DATA.strategy.global_score;
        document.getElementById('ui-headline').innerText = DATA.strategy.headline;
        document.getElementById('ui-narrative').innerText = DATA.strategy.narrative;
        document.getElementById('ui-business-impacts').innerHTML = (DATA.strategy.business_impacts || []).map(i => `<li class="text-[11px] text-slate-300 leading-tight flex items-start gap-3"><i class="fa-solid fa-check-double text-emerald-500 mt-1 shrink-0"></i> ${i}</li>`).join('');
        renderHeatmap(); renderRoadmap(); renderInsights(); renderPrograms(); renderGlobalChart(); renderOpModel();
        renderProposals(); renderSankey();
    } catch(e) { console.error(e); }
}

function renderProposals() {
    const proposals = DATA.roadmap.proactive_proposals || [];
    document.getElementById('ui-proposals').innerHTML = proposals.length > 0 ? proposals.map((p, idx) => `
        <div onclick="openProposalModal(${idx})" class="cursor-pointer glass p-8 rounded-[2.5rem] border-l-[8px] border-l-sky-500 hover:border-l-emerald-500 shadow-2xl relative overflow-hidden group transition-all transform hover:-translate-y-1">
            <div class="absolute top-0 right-0 p-6 flex gap-4">
                <span class="px-3 py-1 bg-sky-500 group-hover:bg-emerald-500 text-slate-950 text-[9px] font-black rounded-lg uppercase tracking-widest transition-colors">${(p.investment_and_timeline||{}).tcv_range || 'TBD'}</span>
            </div>
            <div class="max-w-4xl">
                <h3 class="text-2xl font-black text-white mb-4 tracking-tighter uppercase leading-none group-hover:text-emerald-400 transition-colors flex items-center gap-4">${p.initiative_name} <i class="fa-solid fa-arrow-right text-emerald-500 opacity-0 group-hover:opacity-100 transition-opacity"></i></h3>
                <p class="text-sm text-slate-300 font-light leading-relaxed mb-8">${p.executive_synthesis}</p>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div class="p-6 bg-rose-500/5 rounded-3xl border border-rose-500/10">
                        <b class="text-rose-400 text-[10px] font-black uppercase tracking-[0.2em] block mb-3 italic">Riesgo por Inacción</b>
                        <p class="text-xs text-rose-100/80 leading-relaxed font-medium line-clamp-2">${(p.context_and_why||{}).cost_of_inaction || 'N/A'}</p>
                    </div>
                    <div class="p-6 bg-emerald-500/5 rounded-3xl border border-emerald-500/10">
                        <b class="text-emerald-400 text-[10px] font-black uppercase tracking-[0.2em] block mb-3 italic">Resultado Objetivo</b>
                        <p class="text-xs text-emerald-100/80 leading-relaxed font-medium line-clamp-2">${(p.solution_and_what||{}).target_state || 'N/A'}</p>
                    </div>
                </div>
            </div>
        </div>
    `).join('') : '<p class="text-slate-500 italic text-center p-20 glass rounded-[2.5rem]">No hay propuestas proactivas definidas en el payload actual.</p>';
}

function openProposalModal(idx) {
    const p = DATA.roadmap.proactive_proposals[idx];
    document.getElementById('prop-name').innerText = p.initiative_name;
    document.getElementById('prop-tcv').innerText = "INVERSIÓN / PLAZO: " + ((p.investment_and_timeline||{}).tcv_range || 'TBD');
    document.getElementById('prop-synthesis').innerText = p.executive_synthesis;
    const dd = p.deep_dive || {};
    document.getElementById('prop-deliverables').innerHTML = (dd.deliverables || ["Ver matriz de alcance adjunta."]).map(d => `<li>${d}</li>`).join('');
    document.getElementById('prop-roi').innerText = dd.roi || "ROI validado en el Business Case detallado.";
    document.getElementById('prop-prereq').innerText = dd.prerequisites || "Ninguna dependencia bloqueante identificada.";
    const modal = document.getElementById('proposal-modal');
    modal.classList.remove('hidden');
    setTimeout(() => { modal.classList.remove('opacity-0'); modal.querySelector('div').classList.remove('scale-95'); }, 10);
}

function closeProposalModal() {
    const modal = document.getElementById('proposal-modal');
    modal.classList.add('opacity-0');
    modal.querySelector('div').classList.add('scale-95');
    setTimeout(() => modal.classList.add('hidden'), 300);
}

function renderSankey() {
    try {
        const svg = d3.select("#sankey-svg");
        const container = document.getElementById('sankey-container');
        if(!svg.node() || !container) return;
        const width = container.clientWidth;
        const height = container.clientHeight;
        svg.html("");
        d3.select("#sankey-tooltip").remove();
        const tooltip = d3.select("#sankey-container")
            .append("div")
            .attr("id", "sankey-tooltip")
            .attr("class", "absolute z-50 pointer-events-none opacity-0 transition-opacity duration-200 glass p-6 rounded-2xl border border-white/10 shadow-[0_0_30px_rgba(0,0,0,0.8)] max-w-sm backdrop-blur-xl");

        const nodes = []; const links = [];
        const towers = Object.values(DATA.towers);
        towers.forEach((t, i) => {
            const score = parseFloat(t.meta.score);
            const gapColor = score < 2.5 ? '#f43f5e' : (score < 3.5 ? '#f59e0b' : '#10b981');
            nodes.push({
                id: t.meta.id, name: t.meta.id, fullName: `Status ${t.meta.name}`, type:'GAP',
                desc: (t.executive_summary || '').substring(0, 120) + '...', score: t.meta.score,
                x: width * 0.15, y: (height/(towers.length+1))*(i+1), color: gapColor
            });
        });

        const progs = DATA.roadmap.programs || [];
        progs.forEach((p, i) => nodes.push({
            id: p.name, name: "Prog. " + (i+1), fullName: p.name, type:'PROG',
            desc: p.description || 'Habilitador estratégico de transformación.',
            x: width * 0.50, y: (height/(progs.length+1))*(i+1), color: '#6366f1'
        }));

        const impacts = DATA.strategy.business_impacts || [];
        impacts.forEach((m, i) => nodes.push({
            id: 'impact-'+i, name: "Impacto " + (i+1), fullName: m, type:'IMPACT',
            x: width * 0.85, y: (height/(impacts.length+1))*(i+1), color: '#10b981'
        }));

        const horizons = DATA.roadmap.horizons || {};
        const progToTowers = {};
        Object.values(horizons).flat().forEach(initiative => {
            if (initiative.program && initiative.tower) {
                if (!progToTowers[initiative.program]) progToTowers[initiative.program] = new Set();
                progToTowers[initiative.program].add(initiative.tower);
            }
        });

        nodes.filter(n => n.type==='PROG').forEach((pn, progIdx) => {
            let linkedTowers = progToTowers[pn.fullName] ? Array.from(progToTowers[pn.fullName]) : [];
            if (linkedTowers.length === 0 && progs.length > 0) {
                const towersPerProg = Math.max(1, Math.floor(towers.length / progs.length));
                const startIndex = progIdx * towersPerProg;
                linkedTowers = towers.slice(startIndex, startIndex + towersPerProg).map(t => t.meta.id);
            }

            linkedTowers.forEach(tId => {
                const sourceNode = nodes.find(n => n.type === 'GAP' && n.id === tId);
                if (sourceNode) links.push({source: sourceNode, target: pn});
            });

            if (impacts.length > 0) {
                const targetIdx = progIdx % impacts.length;
                const target = nodes.filter(i => i.type==='IMPACT')[targetIdx];
                if (target) links.push({source: pn, target: target});
                if (impacts.length > 1 && progs.length > 1) {
                    const secondaryIdx = (progIdx + 1) % impacts.length;
                    const secTarget = nodes.filter(i => i.type==='IMPACT')[secondaryIdx];
                    if (secTarget) links.push({source: pn, target: secTarget});
                }
            }
        });

        nodes.filter(n => n.type==='GAP').forEach((gn, gapIdx) => {
            const hasLink = links.some(l => l.source.id === gn.id);
            if (!hasLink && progs.length > 0) {
                const targetProg = nodes.filter(n => n.type==='PROG')[gapIdx % progs.length];
                if (targetProg) links.push({source: gn, target: targetProg});
            }
        });

        const linkGen = d3.linkHorizontal().x(d => d.x).y(d => d.y);
        const linkPaths = svg.append("g").selectAll("path").data(links).enter().append("path")
            .attr("d", linkGen).attr("fill", "none")
            .attr("stroke", "rgba(255, 255, 255, 0.05)")
            .attr("stroke-width", 2)
            .attr("class", "transition-all duration-300");

        const nodeGroups = svg.append("g").selectAll("g").data(nodes).enter().append("g")
            .attr("transform", d => `translate(${d.x},${d.y})`)
            .style("cursor", "crosshair");

        nodeGroups.append("circle").attr("r", 18).attr("fill", "transparent").attr("stroke", d => d.color).attr("stroke-width", 1).style("opacity", 0.3).attr("stroke-dasharray", "2,2");
        nodeGroups.append("circle").attr("r", 8).attr("fill", d => d.color).style("box-shadow", "0 0 10px white");
        nodeGroups.append("text")
            .attr("dy", d => d.type === 'PROG' ? -25 : 4)
            .attr("dx", d => d.type === 'GAP' ? -25 : (d.type === 'IMPACT' ? 25 : 0))
            .attr("text-anchor", d => d.type === 'GAP' ? "end" : (d.type === 'IMPACT' ? "start" : "middle"))
            .attr("fill", "#cbd5e1")
            .style("font-size", "11px").style("font-weight", "800").style("letter-spacing", "0.1em")
            .text(d => d.name);

        nodeGroups.on("mouseenter", function(event, d) {
            nodeGroups.style("opacity", n => (n === d || links.some(l => (l.source === d && l.target === n) || (l.target === d && l.source === n) || (l.source === n && l.target === d))) ? 1 : 0.1);
            linkPaths
                .attr("stroke", l => {
                    if (l.source === d || l.target === d) return d.color;
                    if (d.type === 'GAP' && l.source.type === 'PROG' && links.some(ll => ll.source === d && ll.target === l.source)) return l.source.color;
                    if (d.type === 'IMPACT' && l.target.type === 'PROG' && links.some(ll => ll.target === d && ll.source === l.target)) return l.target.color;
                    return "rgba(255,255,255,0.01)";
                })
                .attr("stroke-width", l => (l.source === d || l.target === d) ? 5 : 2)
                .style("opacity", l => (l.source === d || l.target === d || (d.type === 'GAP' && l.source.type === 'PROG' && links.some(ll => ll.source === d && ll.target === l.source)) || (d.type === 'IMPACT' && l.target.type === 'PROG' && links.some(ll => ll.target === d && ll.source === l.target))) ? 1 : 0);

            let htmlContent = "";
            if(d.type === 'GAP') {
                htmlContent = `<span class="text-[9px] font-black text-rose-400 uppercase tracking-widest block mb-2"><i class="fa-solid fa-triangle-exclamation"></i> Dolor Operativo</span>
                               <h4 class="text-lg font-black text-white leading-tight mb-3">${d.fullName}</h4>
                               <div class="inline-flex items-center gap-2 mb-4 bg-rose-500/10 border border-rose-500/20 px-3 py-1 rounded-lg"><span class="text-[9px] text-rose-300 uppercase font-bold">Madurez As-Is:</span><span class="text-sm font-black text-rose-400 mono">${d.score}/5.0</span></div>
                               <p class="text-xs text-slate-300 leading-relaxed font-medium">${d.desc}</p>`;
            } else if(d.type === 'PROG') {
                 htmlContent = `<span class="text-[9px] font-black text-indigo-400 uppercase tracking-widest block mb-2"><i class="fa-solid fa-rocket"></i> Vehículo de Ejecución</span>
                               <h4 class="text-lg font-black text-white leading-tight mb-3">${d.fullName}</h4>
                               <p class="text-xs text-slate-300 leading-relaxed font-medium bg-slate-900/50 p-3 rounded-xl border border-white/5">${d.desc}</p>`;
            } else {
                 htmlContent = `<span class="text-[9px] font-black text-emerald-400 uppercase tracking-widest block mb-2"><i class="fa-solid fa-bullseye"></i> Valor de Negocio Generado</span>
                               <h4 class="text-sm font-bold text-emerald-50 leading-relaxed italic border-l-4 border-emerald-500 pl-3">${d.fullName}</h4>`;
            }

            const mouseCoords = d3.pointer(event, container);
            let leftPos = mouseCoords[0] + 30;
            let topPos = mouseCoords[1] - 40;
            if(leftPos + 300 > width) leftPos = mouseCoords[0] - 340;
            if(topPos + 150 > height) topPos = height - 160;

            tooltip.html(htmlContent)
                   .style("left", leftPos + "px")
                   .style("top", topPos + "px")
                   .style("opacity", 1);
        })
        .on("mouseleave", function() {
            nodeGroups.style("opacity", 1);
            linkPaths.attr("stroke", "rgba(255, 255, 255, 0.05)").attr("stroke-width", 2).style("opacity", 1);
            tooltip.style("opacity", 0);
        });

    } catch(e) { console.warn("Sankey visualization error:", e); }
}

function renderInsights() {
    document.getElementById('ui-burning-platform').innerHTML = DATA.strategy.burning_platform.map(bp => `<div class="space-y-2"><h3 class="text-rose-400 font-black text-[11px] uppercase tracking-widest leading-tight">${bp.theme}</h3><p class="text-slate-300 text-[11px] leading-relaxed font-medium text-justify">${bp.business_risk}</p></div>`).join('<div class="h-4 border-b border-rose-500/10"></div>');
}

function renderOpModel() {
    const html = (DATA.strategy.operating_model || []).map(o => `<div class="p-5 glass rounded-2xl border border-white/5"><b class="text-indigo-400 text-[10px] font-black uppercase block mb-2 tracking-widest">${o.area || 'Implicación'}</b><p class="text-[11px] text-slate-300 leading-relaxed font-medium">${o.description || o}</p></div>`).join('');
    document.getElementById('ui-op-model').innerHTML = html || '<p class="text-[10px] text-slate-500 italic">Análisis de modelo operativo consolidado en el dossier técnico.</p>';
}

function renderPrograms() {
    document.getElementById('ui-programs').innerHTML = DATA.roadmap.programs.map(p => `
        <div onclick="filterByProgram('${p.name}')" class="prog-card p-8 glass rounded-[2.5rem] border-l-8 border-l-indigo-600 shadow-xl group">
            <div class="flex justify-between items-start mb-4">
                <b class="text-sm text-white block uppercase font-black tracking-tight leading-tight group-hover:text-sky-400 transition-colors">${p.name}</b>
                <i class="fa-solid fa-filter text-indigo-500 text-[10px] opacity-0 group-hover:opacity-100 transition-opacity"></i>
            </div>
            <p class="text-xs text-slate-400 leading-relaxed line-clamp-4">${p.description}</p>
        </div>
    `).join('');
}

function filterByProgram(progName) {
    if(currentProgramFilter === progName) {
        currentProgramFilter = null;
        document.querySelectorAll('.proj-tile, .tower-card').forEach(el => el.classList.remove('dimmed', 'highlighted'));
        return;
    }
    currentProgramFilter = progName;
    document.querySelectorAll('.proj-tile').forEach(el => {
        const pName = el.getAttribute('data-program');
        if(pName === progName) { el.classList.remove('dimmed'); el.classList.add('highlighted'); }
        else { el.classList.add('dimmed'); el.classList.remove('highlighted'); }
    });
    document.querySelectorAll('.tower-card').forEach(el => {
        const tId = el.getAttribute('data-tower-id');
        const hasProj = Object.values(DATA.roadmap.horizons).some(h => h.some(p => p.program === progName && p.tower === tId));
        if(hasProj) { el.classList.remove('dimmed'); el.classList.add('highlighted'); }
        else { el.classList.add('dimmed'); el.classList.remove('highlighted'); }
    });
}

function renderHeatmap() {
    document.getElementById('ui-heatmap').innerHTML = Object.values(DATA.towers).map(t => {
        const rawTarget = (t.target_maturity || t.meta.target_maturity || "4.0").toString();
        let targetScore = rawTarget.match(/(\d+(\.\d+)?)/) ? rawTarget.match(/(\d+(\.\d+)?)/)[1] : "4.0";
        return `
        <div onclick="openTower('${t.meta.id}')" data-tower-id="${t.meta.id}" class="tower-card glass p-8 rounded-[2.5rem] border-l-8 ${parseFloat(t.meta.score) < 2.5 ? 'border-l-rose-600' : 'border-l-sky-600'} shadow-xl group">
            <div class="flex justify-between items-start mb-6">
                <div>
                    <span class="text-[10px] font-black text-slate-500 mono uppercase mb-1 block tracking-widest">${t.meta.id}</span>
                    <h3 class="text-white font-extrabold text-2xl leading-tight group-hover:text-sky-400 transition-colors">${t.meta.name}</h3>
                </div>
                <div class="text-4xl font-black font-mono tracking-tighter" style="color: #${t.meta.status_color}">${t.meta.score}</div>
            </div>
            <div class="flex items-center justify-between pt-6 border-t border-white/5">
                <div class="space-y-1">
                    <span class="text-[8px] font-black text-slate-500 uppercase block tracking-widest">Target Maturity</span>
                    <b class="text-xs text-white uppercase font-bold tracking-tighter">${targetScore}</b>
                </div>
                <div class="space-y-1 text-right">
                    <span class="text-[8px] font-black text-slate-500 uppercase block tracking-widest">Complejidad</span>
                    <b class="text-xs text-sky-400 uppercase font-bold tracking-tighter">${t.complexity}</b>
                </div>
            </div>
        </div>
        `;
    }).join('');
}

function renderRoadmap() {
    const h = DATA.roadmap.horizons || {};
    const m = [{k: "quick_wins_0_3_months", l: "H1: 0-3 Meses (Inmediato)", c: "rose"}, {k: "year_1_3_12_months", l: "H2: 3-12 Meses (Estratégico)", c: "sky"}, {k: "year_2_12_24_months", l: "H3: 12-24 Meses (Evolutivo)", c: "emerald"}];
    document.getElementById('ui-roadmap').innerHTML = m.map((map, idx) => {
        const items = h[map.k] || []; if(!items.length) return '';
        return `<div class="space-y-8"><div class="flex items-center gap-6 border-b border-white/5 pb-4"><h3 class="text-xs font-black text-white uppercase tracking-[0.5em] italic">${map.l}</h3></div><div class="grid grid-cols-1 md:grid-cols-4 lg:grid-cols-5 gap-4">${items.map(i => {
            let impactScore = 'Media';
            const textToAnalyze = ((i.title || '') + ' ' + (i.business_case || '')).toLowerCase();
            const isCritical = /riesgo crítico|continuidad|caída|ciberataque|spof|vulnerabilidad|ransomware|interrupción/i.test(textToAnalyze);
            const isHigh = /automatización|eficiencia|gobernanza|estandarización|reducción de coste|tco/i.test(textToAnalyze);
            if (isCritical) impactScore = 'Crítica';
            else if (isHigh || idx === 0) impactScore = 'Alta';
            const priorityColor = impactScore === 'Crítica' ? 'rose' : (impactScore === 'Alta' ? 'sky' : 'emerald');
            return `<div onclick="showProjectDetailsDirectly('${i.title}')" data-program="${i.program}" class="proj-tile p-6 glass rounded-2xl border border-white/5 hover:border-${map.c}-500/50 flex flex-col justify-between group min-h-[140px] shadow-xl relative overflow-hidden">
                <div class="absolute top-0 right-0 p-3"><span class="px-2 py-0.5 bg-${priorityColor}-500/20 text-${priorityColor}-400 text-[8px] font-black rounded-md border border-${priorityColor}-500/30 uppercase tracking-widest">${impactScore}</span></div>
                <b class="text-xs text-slate-100 leading-tight group-hover:text-sky-400 transition-colors pr-8">${i.title}</b>
                <div class="flex justify-between items-center mt-4 pt-4 border-t border-white/5"><span class="text-[9px] font-black text-slate-600 uppercase truncate pr-2">${i.program || 'TRANSF.'}</span><i class="fa-solid fa-magnifying-glass-plus text-sky-500 text-xs"></i></div>
            </div>`;
        }).join('')}</div></div>`;
    }).join('');
}

function getTargetScore(t) {
    let tm = t.target_maturity || t.meta.target_maturity || "4.0";
    if(typeof tm === 'string') {
        const match = tm.match(/(\d+(\.\d+)?)/);
        return match ? parseFloat(match[1]) : 4.0;
    }
    return parseFloat(tm) || 4.0;
}

function renderGlobalChart() {
    const ctx = document.getElementById('globalRadarChart').getContext('2d');
    charts.global = new Chart(ctx, {
        type: 'radar',
        data: {
            labels: DATA.heatmap.map(t => t.id),
            datasets: [
                { label: 'As-Is', data: DATA.heatmap.map(t => parseFloat(t.score)), backgroundColor: 'rgba(14, 165, 233, 0.3)', borderColor: '#38bdf8', borderWidth: 3, pointRadius: 5 },
                { label: 'Target', data: DATA.heatmap.map(t => getTargetScore(DATA.towers[t.id])), backgroundColor: 'transparent', borderColor: 'rgba(16, 185, 129, 0.3)', borderWidth: 1, borderDash: [6, 6], pointRadius: 0 }
            ]
        },
        options: { responsive: true, maintainAspectRatio: false, scales: { r: { min: 0, max: 5, ticks: { display: false }, grid: { color: 'rgba(255,255,255,0.06)' }, pointLabels: { color: '#fff', font: { weight: 'black', size: 14, family: 'JetBrains Mono' } } } }, plugins: { legend: { display: false }, datalabels: { color: '#fff', backgroundColor: '#38bdf8', borderRadius: 4, font: { weight: 'black', size: 10 }, formatter: (v) => v.toFixed(1), display: true } } }
    });
}

function openTower(id) {
    const t = DATA.towers[id];
    const color = '#' + t.meta.status_color;
    const targetVal = getTargetScore(t);
    document.getElementById('modal-tower-id').innerText = t.meta.id;
    document.getElementById('modal-tower-name').innerText = t.meta.name;
    document.getElementById('modal-tower-score').innerText = t.meta.score;
    document.getElementById('modal-tower-score').style.color = color;
    document.getElementById('modal-score-box').style.borderColor = color;
    document.getElementById('modal-tower-band').innerText = (t.meta.band || '---').toUpperCase();
    document.getElementById('modal-narrative').innerText = t.executive_summary;
    document.getElementById('modal-coi').innerText = t.cost_of_inaction || "Análisis de riesgo no disponible para esta torre.";
    document.getElementById('modal-decisions').innerHTML = (t.decisions || ["Consolidar arquitectura base.", "Establecer gobierno operativo."]).map(d => `<li>${d}</li>`).join('');
    document.getElementById('modal-business-impact').innerText = t.business_impact || "Protección de ingresos y continuidad de operaciones críticas.";
    const firstPillarVision = t.pillars.length > 0 ? t.pillars[0].target_vision : "Transformación hacia un modelo industrializado y gobernado.";
    document.getElementById('modal-vision-text').innerText = firstPillarVision;
    document.getElementById('modal-structural-risks').innerHTML = (t.structural_risks || []).length ? t.structural_risks.map(r => `<li class="flex items-start gap-3"><i class="fa-solid fa-circle-exclamation text-rose-500 mt-1 shrink-0"></i> ${r}</li>`).join('') : '<li class="italic text-slate-500">Sin riesgos críticos identificados.</li>';
    document.getElementById('modal-op-benefits').innerHTML = (t.operational_benefits || []).length ? t.operational_benefits.map(b => `<li class="flex items-start gap-3"><i class="fa-solid fa-circle-check text-emerald-500 mt-1 shrink-0"></i> ${b}</li>`).join('') : '<li class="italic text-slate-500">Mejora general de eficiencia y resiliencia.</li>';

    const allProjects = t.pillars.flatMap(p => p.projects);
    if (allProjects.length) {
        let ganttHtml = `
        <div class="relative mb-6">
            <div class="flex items-center gap-6">
                <div class="w-64 shrink-0"></div>
                <div class="flex-1 relative h-6 border-b border-white/10 flex justify-between text-[8px] lg:text-[9px] font-black text-slate-500 uppercase tracking-widest px-2">
                    <span>M0</span>
                    <span class="absolute left-[16.6%] -translate-x-1/2">M6</span>
                    <span class="absolute left-[33.3%] -translate-x-1/2">M12</span>
                    <span class="absolute left-[50%] -translate-x-1/2">M18</span>
                    <span class="absolute left-[66.6%] -translate-x-1/2">M24</span>
                    <span class="absolute left-[83.3%] -translate-x-1/2">M30</span>
                    <span>M36</span>
                </div>
            </div>
        </div>
        <div class="space-y-4">
        `;
        let currentDelay = 0;
        ganttHtml += allProjects.map((p, idx) => {
            const durationMonths = parseInt(p.duration) || 3;
            const widthPercent = Math.min(100, (durationMonths / 36) * 100);
            const startMonth = parseInt(p.start_month) || currentDelay;
            const leftMarginPercent = Math.min(100, (startMonth / 36) * 100);
            currentDelay = startMonth + Math.max(1, Math.floor(durationMonths * 0.7));
            return `
            <div class="group relative">
                <div class="flex items-center gap-6 mb-1">
                    <div class="w-64 shrink-0">
                        <span class="text-[11px] font-bold text-slate-100 group-hover:text-sky-400 transition-colors block truncate uppercase tracking-tight" title="${p.name}">${p.name}</span>
                        <span class="text-[8px] font-black text-slate-500 uppercase tracking-widest">${p.sizing || 'M'} | ${durationMonths} MESES</span>
                    </div>
                    <div class="flex-1 h-4 bg-slate-800/30 rounded-full overflow-hidden border border-white/5 relative bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjUiIGhlaWdodD0iMjUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PGcgc3Ryb2tlPSJyZ2JhKDI1NSwyNTUsMjU1LDAuMDUpIiBzdHJva2Utd2lkdGg9IjEiIGZpbGw9Im5vbmUiPjxwYXRoIGQ9Ik0wLDBMMDAsMjUiLz48L2c+PC9zdmc+')]">
                        <div class="absolute h-full bg-gradient-to-r from-sky-600 to-sky-400 rounded-full shadow-[0_0_15px_rgba(56,189,248,0.4)] transition-all duration-1000 border border-sky-300/30"
                             style="width: ${widthPercent}%; left: ${leftMarginPercent}%;"
                             title="${p.name} (Inicia: Mes ${startMonth}, Duración: ${durationMonths} meses)">
                        </div>
                    </div>
                </div>
            </div>`;
        }).join('');
        ganttHtml += `</div>`;
        document.getElementById('modal-gantt').innerHTML = ganttHtml;
    } else {
        document.getElementById('modal-gantt').innerHTML = '<p class="text-xs text-slate-500 italic text-center p-8">No hay cronograma de ingeniería definido para esta torre.</p>';
    }

    document.getElementById('modal-pillars-rows').innerHTML = t.pillars.map((p, idx) => {
        const mainGap = p.health_check && p.health_check.length > 0 ? p.health_check[0].finding : 'Evaluación técnica pendiente.';
        return `
        <div class="glass rounded-3xl border border-white/5 overflow-hidden shadow-xl mb-8">
            <div class="p-6 lg:p-8 bg-slate-900/60 border-b border-white/5 flex flex-col lg:flex-row items-start lg:items-center justify-between gap-6">
                <div class="flex items-center gap-6">
                    <span class="w-12 h-12 shrink-0 rounded-2xl bg-slate-800 text-sky-400 flex items-center justify-center font-black text-lg border border-sky-500/20 shadow-inner">${idx+1}</span>
                    <h4 class="text-xl lg:text-2xl font-black text-white tracking-tight uppercase">${p.name}</h4>
                </div>
                <div class="flex items-center gap-8 w-full lg:w-auto justify-between lg:justify-end">
                    <div class="text-4xl font-black text-sky-400 mono tracking-tighter drop-shadow-[0_0_10px_rgba(56,189,248,0.3)]">${p.score}</div>
                    <button onclick="document.getElementById('blueprint-panel-${idx}').classList.toggle('hidden')" class="px-6 py-3 bg-slate-800 hover:bg-sky-500 text-slate-300 hover:text-slate-950 text-[10px] font-black uppercase rounded-xl border border-white/10 hover:border-sky-400 tracking-[0.2em] transition-all shadow-lg whitespace-nowrap">Auditoría Técnica <i class="fa-solid fa-microscope ml-2"></i></button>
                </div>
            </div>
            <div class="p-6 lg:p-8 bg-slate-950/40 grid grid-cols-1 lg:grid-cols-3 gap-8 relative overflow-hidden">
                <div class="absolute top-0 left-1/2 -translate-x-1/2 w-full h-full bg-gradient-to-b from-sky-500/5 to-transparent pointer-events-none"></div>
                <div class="space-y-4 relative z-10">
                    <h5 class="text-[10px] font-black text-rose-400 uppercase tracking-widest flex items-center gap-2"><i class="fa-solid fa-magnifying-glass-chart"></i> Hallazgo Principal (As-Is)</h5>
                    <p class="text-xs text-slate-300 leading-relaxed font-medium line-clamp-4 text-justify">${mainGap}</p>
                </div>
                <div class="space-y-4 lg:border-l lg:border-white/5 lg:pl-8 relative z-10">
                    <h5 class="text-[10px] font-black text-emerald-400 uppercase tracking-widest flex items-center gap-2"><i class="fa-solid fa-bullseye"></i> Estado Objetivo (To-Be)</h5>
                    <p class="text-xs text-emerald-100/70 italic leading-relaxed line-clamp-4 text-justify">${p.target_vision || 'Visión estratégica en desarrollo.'}</p>
                </div>
                <div class="space-y-4 lg:border-l lg:border-white/5 lg:pl-8 relative z-10">
                    <h5 class="text-[10px] font-black text-sky-400 uppercase tracking-widest flex items-center gap-2"><i class="fa-solid fa-rocket"></i> Plan de Acción</h5>
                    <div class="space-y-3">
                        ${p.projects.slice(0,3).map(proj => `<div class="flex items-start gap-3"><i class="fa-solid fa-check text-sky-500 mt-0.5 text-[10px]"></i><span class="text-[11px] text-slate-200 font-bold uppercase tracking-tight leading-tight">${proj.name}</span></div>`).join('')}
                        ${p.projects.length > 3 ? `<div class="pt-2 border-t border-white/5 text-[9px] font-black text-slate-500 uppercase tracking-widest">+ ${p.projects.length - 3} iniciativas adicionales requeridas</div>` : (p.projects.length === 0 ? '<span class="text-xs text-slate-500 italic">No hay proyectos asociados.</span>' : '')}
                    </div>
                </div>
            </div>
            <div id="blueprint-panel-${idx}" class="hidden bg-slate-900 border-t border-sky-500/20">
                <div class="p-8 lg:p-10">
                    <h5 class="text-[11px] font-black text-white uppercase tracking-[0.3em] mb-8 flex items-center gap-3"><i class="fa-solid fa-stethoscope text-sky-500"></i> Desglose Técnico de Capacidades Evaluadas</h5>
                    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        ${(p.health_check || []).map(hc => `
                            <div class="p-6 bg-black/40 rounded-2xl border border-white/5 flex flex-col gap-4 shadow-inner">
                                <b class="text-[11px] text-sky-300 uppercase tracking-tight leading-snug border-b border-white/5 pb-3 block">${hc.capability}</b>
                                <p class="text-[11px] text-slate-400 leading-relaxed font-medium">${hc.finding}</p>
                                ${hc.business_risk ? `<div class="mt-auto pt-4 border-t border-rose-500/10"><span class="text-[9px] font-black text-rose-500 uppercase tracking-widest block mb-2">Riesgo de Negocio</span><p class="text-[10px] text-rose-200/80 leading-snug italic font-medium">${hc.business_risk}</p></div>` : ''}
                            </div>
                        `).join('')}
                    </div>
                </div>
            </div>
        </div>
        `;
    }).join('');

    document.getElementById('tower-modal').classList.remove('hidden');
    setTimeout(() => { document.getElementById('tower-modal').classList.remove('opacity-0'); document.getElementById('modal-content').classList.remove('scale-95'); }, 10);
    const ctx = document.getElementById('towerRadarChart').getContext('2d');
    if(charts.tower) charts.tower.destroy();
    charts.tower = new Chart(ctx, {
        type: 'radar',
        data: {
            labels: t.pillars.map(p => (p.name || '').substring(0,30)),
            datasets: [
                { label: 'As-Is', data: t.pillars.map(p => parseFloat(p.score)), backgroundColor: 'rgba(14, 165, 233, 0.4)', borderColor: '#38bdf8', borderWidth: 4, pointRadius: 6 },
                { label: 'Target', data: t.pillars.map(() => targetVal), backgroundColor: 'transparent', borderColor: 'rgba(16, 185, 129, 0.4)', borderWidth: 2, borderDash: [5, 5], pointRadius: 0 }
            ]
        },
        options: { responsive: true, maintainAspectRatio: false, scales: { r: { min: 0, max: 5, ticks: { display: false }, pointLabels: { color: '#94a3b8', font: { size: 12, weight: 'black' } }, grid: { color: 'rgba(255,255,255,0.08)' } } }, plugins: { legend: { display: false }, datalabels: { color: '#fff', backgroundColor: '#38bdf8', borderRadius: 4, font: { weight: 'black', size: 10 }, formatter: (v) => v.toFixed(1), display: true } } }
    });
}

function toggleBlueprintDetail(idx) {
    const el = document.getElementById('blueprint-panel-' + idx);
    if(el.classList.contains('open')) el.classList.remove('open');
    else { document.querySelectorAll('.blueprint-panel').forEach(p => p.classList.remove('open')); el.classList.add('open'); el.scrollIntoView({ behavior: 'smooth', block: 'center' }); }
}

function openProjectModal(towerId, pilarIdx, projIdx) {
    const p = DATA.towers[towerId].pillars[pilarIdx].projects[projIdx];
    document.getElementById('proj-name').innerText = p.name;
    document.getElementById('proj-sizing').innerText = "SIZE: " + p.sizing;
    document.getElementById('proj-case').innerText = p.business_case || "Valor estratégico capturado en Blueprint.";
    document.getElementById('proj-objective').innerText = p.tech_objective || p.objective;
    document.getElementById('proj-duration').innerText = "CALENDARIO: " + (p.duration || "TBD");
    document.getElementById('proj-deliverables').innerHTML = (p.deliverables || []).map(d => `<span class="px-4 py-2 bg-slate-950 text-slate-300 text-[11px] font-bold rounded-xl border border-white/5 shadow-inner leading-none">${d}</span>`).join('');
    document.getElementById('project-modal').classList.remove('hidden');
    setTimeout(() => { document.getElementById('project-modal').classList.remove('opacity-0'); document.getElementById('project-modal').querySelector('div').classList.remove('scale-95'); }, 10);
}

function closeProjectModal() { document.getElementById('project-modal').classList.add('opacity-0'); document.getElementById('project-modal').querySelector('div').classList.add('scale-95'); setTimeout(() => document.getElementById('project-modal').classList.add('hidden'), 300); }

function showProjectDetailsDirectly(title) {
    for (const t of Object.values(DATA.towers)) {
        for (let i=0; i<t.pillars.length; i++) {
            for (let j=0; j<t.pillars[i].projects.length; j++) {
                if (t.pillars[i].projects[j].name === title || t.pillars[i].projects[j].title === title) {
                    openProjectModal(t.meta.id, i, j); return;
                }
            }
        }
    }
}

function closeModal() { document.getElementById('tower-modal').classList.add('opacity-0'); document.getElementById('modal-content').classList.add('scale-95'); setTimeout(() => { document.getElementById('tower-modal').classList.add('hidden'); if(charts.tower) charts.tower.destroy(); }, 300); }

window.onload = init;
