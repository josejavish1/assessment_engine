/**
 * Sovereign Sankey Component (Tier 1 Context-Aware Edition)
 * Implements high-performance filtering for executive drill-down.
 */

class SovereignSankey extends HTMLElement {
    constructor() {
        super();
        this.containerId = "sankey-container";
        this.svgId = "sankey-svg";
        this.currentFilter = null;
    }

    connectedCallback() {
        this.render();
        window.addEventListener('resize', () => this.render());
        window.addEventListener('sovereign-ready', () => this.render());
    }

    filterByTower(towerId) {
        this.currentFilter = towerId;
        this.render();
    }

    resetFilter() {
        this.currentFilter = null;
        this.render();
    }

    render() {
        const state = window.SovereignState;
        if (!state || !state.dto) return;

        const container = document.getElementById(this.containerId);
        const svg = d3.select(`#${this.svgId}`);
        if (!container || !svg.node()) return;

        const width = container.clientWidth;
        const height = container.clientHeight;
        svg.html("");

        const dto = state.dto;
        const topology = dto.topology || {};

        if (!topology.nodes || !topology.edges) {
            this._renderPlaceholder(svg, width, height, "Topography pending resolution...");
            return;
        }

        // --- DRILL-DOWN LOGIC ---
        let filteredNodes = topology.nodes;
        let filteredEdges = topology.edges;

        if (this.currentFilter) {
            // Filter nodes by Tower ID or their connections to that tower
            filteredNodes = topology.nodes.filter(n =>
                n.tower_id === this.currentFilter ||
                topology.edges.some(e =>
                    (e.source === n.id && topology.nodes.find(sn => sn.id === e.target)?.tower_id === this.currentFilter) ||
                    (e.target === n.id && topology.nodes.find(sn => sn.id === e.source)?.tower_id === this.currentFilter)
                )
            );

            const nodeIds = new Set(filteredNodes.map(n => n.id));
            filteredEdges = topology.edges.filter(e => nodeIds.has(e.source) && nodeIds.has(e.target));
        } else {
            // GLOBAL VIEW: Limit to major initiatives and gaps to avoid clutter
            // Tier-1 UX: Only show top 40 nodes by importance/connectivity in global view
            // (In a real 2026 app, we'd have a 'relevance' score)
            if (filteredNodes.length > 50) {
                // Show only nodes that have edges (systemic ones)
                const linkedIds = new Set();
                filteredEdges.forEach(e => { linkedIds.add(e.source); linkedIds.add(e.target); });
                filteredNodes = filteredNodes.filter(n => linkedIds.has(n.id)).slice(0, 50);
                const finalIds = new Set(filteredNodes.map(n => n.id));
                filteredEdges = filteredEdges.filter(e => finalIds.has(e.source) && finalIds.has(e.target));
            }
        }

        if (filteredNodes.length === 0) {
            this._renderPlaceholder(svg, width, height, `No systemic nexus found for Tower ${this.currentFilter}`);
            return;
        }

        this._drawSankey(svg, filteredNodes, filteredEdges, container, width, height);
    }

    _getColorForType(type, score) {
        if (type === 'GAP' || type === 'RISK') {
            const s = parseFloat(score || 2.5);
            if (s < 2.5) return '#f43f5e';
            if (s < 3.5) return '#f59e0b';
            return '#10b981';
        }
        return type === 'INITIATIVE' ? '#38bdf8' : '#64748b';
    }

    _getXForType(type, width) {
        if (type === 'RISK' || type === 'GAP') return width * 0.2;
        if (type === 'INITIATIVE') return width * 0.8;
        return width * 0.5;
    }

    _drawSankey(svg, nodes, links, container, width, height) {
        const nodeMap = {};
        const displayNodes = nodes.map(n => {
            const obj = {
                ...n,
                x: this._getXForType(n.type, width),
                y: 0,
                color: this._getColorForType(n.type, n.score)
            };
            nodeMap[n.id] = obj;
            return obj;
        });

        // Distribute Y
        const types = ['RISK', 'GAP', 'INITIATIVE', 'UNKNOWN'];
        types.forEach(t => {
            const group = displayNodes.filter(n => n.type === t || (t === 'UNKNOWN' && !['RISK', 'GAP', 'INITIATIVE'].includes(n.type)));
            group.forEach((n, i) => {
                n.y = (height / (group.length + 1)) * (i + 1);
            });
        });

        const displayLinks = links.map(l => ({
            source: nodeMap[l.source],
            target: nodeMap[l.target]
        })).filter(l => l.source && l.target);

        const linkGen = d3.linkHorizontal().x(d => d.x).y(d => d.y);

        // Render Links
        const paths = svg.append("g").selectAll("path").data(displayLinks).enter().append("path")
            .attr("d", linkGen)
            .attr("fill", "none")
            .attr("stroke", "rgba(255,255,255,0.03)")
            .attr("stroke-width", 1.5);

        // Render Nodes
        const groups = svg.append("g").selectAll("g").data(displayNodes).enter().append("g")
            .attr("transform", d => `translate(${d.x},${d.y})`)
            .style("cursor", "pointer");

        groups.append("circle").attr("r", 5).attr("fill", d => d.color).style("filter", "blur(2px)").style("opacity", 0.5);
        groups.append("circle").attr("r", 3).attr("fill", d => d.color);

        groups.append("text")
            .attr("dx", d => d.type === 'INITIATIVE' ? 12 : -12)
            .attr("dy", 4)
            .attr("text-anchor", d => d.type === 'INITIATIVE' ? "start" : "end")
            .attr("fill", "#94a3b8")
            .style("font-size", "9px").style("font-weight", "700").style("text-transform", "uppercase").style("letter-spacing", "0.05em")
            .text(d => d.label.length > 40 ? d.label.substring(0, 37) + "..." : d.label);

        // Interaction
        groups.on("mouseenter", function(event, d) {
            d3.select(this).select("circle:last-child").attr("r", 6).attr("fill", "#fff");
            paths.attr("stroke", l => (l.source === d || l.target === d) ? d.color : "rgba(255,255,255,0.01)")
                 .attr("stroke-width", l => (l.source === d || l.target === d) ? 3 : 1.5)
                 .style("opacity", l => (l.source === d || l.target === d) ? 1 : 0.1);
        }).on("mouseleave", function() {
            d3.select(this).select("circle:last-child").attr("r", 3).attr("fill", d => d.color);
            paths.attr("stroke", "rgba(255,255,255,0.03)").attr("stroke-width", 1.5).style("opacity", 1);
        });
    }

    _renderPlaceholder(svg, width, height, text) {
        svg.append("text").attr("x", width/2).attr("y", height/2).attr("text-anchor", "middle").attr("fill", "#475569").style("font-size", "12px").style("font-style", "italic").text(text);
    }
}

customElements.define('sovereign-sankey', SovereignSankey);
