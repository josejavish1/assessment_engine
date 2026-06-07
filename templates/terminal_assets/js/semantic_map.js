/**
 * Sovereign Strategic Terminal V10 - Semantic Map
 * Pure SVG topology renderer with deterministic drill-down.
 */

const SVG_NS = "http://www.w3.org/2000/svg";

class SemanticMap extends HTMLElement {
    constructor() {
        super();
        this.containerId = "semantic-map-container";
        this.svgId = "semantic-map-svg";
        this.currentFilter = "GLOBAL";
        this.selectedId = "";
        this.nodeElements = new Map();
        this.edgeElements = [];
        this.visibleEdges = [];
        this.resizeObserver = null;
        this.onReady = () => this.render();
        this.onResize = () => this.render();
        this.onHighlight = (event) => this.highlightNode(event.detail && event.detail.id);
        this.onClearHighlight = () => this.resetHighlight();
    }

    connectedCallback() {
        window.addEventListener("terminal-ready", this.onReady);
        window.addEventListener("resize", this.onResize);
        window.addEventListener("highlight-node", this.onHighlight);
        window.addEventListener("clear-highlight", this.onClearHighlight);

        const container = document.getElementById(this.containerId);
        if (container && "ResizeObserver" in window) {
            this.resizeObserver = new ResizeObserver(() => this.render());
            this.resizeObserver.observe(container);
        }
    }

    disconnectedCallback() {
        window.removeEventListener("terminal-ready", this.onReady);
        window.removeEventListener("resize", this.onResize);
        window.removeEventListener("highlight-node", this.onHighlight);
        window.removeEventListener("clear-highlight", this.onClearHighlight);
        if (this.resizeObserver) this.resizeObserver.disconnect();
    }

    setFilter(filterId) {
        this.currentFilter = filterId || "GLOBAL";
        this.selectedId = "";
        this.render();
    }

    render() {
        const state = window.TerminalState;
        if (!state) return;

        const container = document.getElementById(this.containerId);
        const svg = document.getElementById(this.svgId);
        if (!container || !svg) return;

        const rect = container.getBoundingClientRect();
        const width = Math.max(320, Math.floor(rect.width));
        const height = Math.max(420, Math.floor(rect.height));
        if (width <= 0 || height <= 0) return;

        clearSvg(svg);
        svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
        svg.setAttribute("preserveAspectRatio", "xMidYMid meet");

        const topology = state.topology;
        if (!topology.nodes || topology.nodes.length === 0) {
            drawEmpty(svg, width, height);
            return;
        }

        const visibleNodes = this.selectNodes(topology.nodes, width);
        const positionedNodes = this.positionNodes(visibleNodes, width, height);
        const nodeMap = buildNodeMap(positionedNodes);
        this.visibleEdges = topology.edges
            .map((edge) => ({
                ...edge,
                sourceNode: findInMap(nodeMap, edge.source),
                targetNode: findInMap(nodeMap, edge.target)
            }))
            .filter((edge) => edge.sourceNode && edge.targetNode);

        const edgeLayer = svgEl("g", { class: "map-edge-layer" });
        const nodeLayer = svgEl("g", { class: "map-node-layer" });
        svg.append(edgeLayer, nodeLayer);

        this.nodeElements = new Map();
        this.edgeElements = [];
        this.visibleEdges.forEach((edge) => this.drawEdge(edgeLayer, edge));
        positionedNodes.forEach((node) => this.drawNode(nodeLayer, node, width));

        if (this.selectedId) {
            this.highlightNode(this.selectedId, true);
        }
    }

    selectNodes(nodes, width) {
        const state = window.TerminalState;
        if (this.currentFilter !== "GLOBAL") {
            const towerNodes = nodes.filter((node) => node.tower_id === this.currentFilter);
            return rankedNodes(towerNodes, state).slice(0, width < 700 ? 54 : 90);
        }

        const linkedIds = new Set();
        state.topology.edges.forEach((edge) => {
            linkedIds.add(edge.source);
            linkedIds.add(edge.target);
            linkedIds.add(String(edge.source).toLowerCase());
            linkedIds.add(String(edge.target).toLowerCase());
        });

        const maxNodes = width < 700 ? 48 : 96;
        return rankedNodes(nodes, state)
            .filter((node) => {
                return linkedIds.has(node.id)
                    || linkedIds.has(node.id.toLowerCase())
                    || node.type === "INITIATIVE"
                    || state.getDegree(node.id) > 0;
            })
            .slice(0, maxNodes);
    }

    positionNodes(nodes, width, height) {
        if (this.currentFilter === "GLOBAL") {
            return this.positionGlobal(nodes, width, height);
        }
        return this.positionTower(nodes, width, height);
    }

    positionGlobal(nodes, width, height) {
        const towerIds = Array.from(new Set(nodes.map((node) => node.tower_id))).sort((a, b) => {
            return a.localeCompare(b, undefined, { numeric: true });
        });
        const cx = width / 2;
        const cy = height / 2 + 16;
        const rx = Math.max(120, width * 0.31);
        const ry = Math.max(120, height * 0.27);
        const centers = new Map();

        towerIds.forEach((towerId, index) => {
            const angle = (-Math.PI / 2) + (Math.PI * 2 * index / Math.max(1, towerIds.length));
            centers.set(towerId, {
                x: cx + Math.cos(angle) * rx,
                y: cy + Math.sin(angle) * ry
            });
        });

        return nodes.map((node, index) => {
            const towerNodes = nodes.filter((item) => item.tower_id === node.tower_id);
            const localIndex = towerNodes.findIndex((item) => item.id === node.id);
            const center = centers.get(node.tower_id) || { x: cx, y: cy };
            const localRadius = Math.max(34, Math.min(width, height) * (towerNodes.length > 14 ? 0.13 : 0.09));
            const angle = (Math.PI * 2 * localIndex / Math.max(1, towerNodes.length)) + hashUnit(node.id) * 0.8;
            const typeBias = node.type === "RISK" ? -18 : node.type === "INITIATIVE" ? 18 : 0;
            return {
                ...node,
                x: clamp(center.x + Math.cos(angle) * localRadius + typeBias, 42, width - 42),
                y: clamp(center.y + Math.sin(angle) * localRadius + (index % 3) * 6, 84, height - 70)
            };
        });
    }

    positionTower(nodes, width, height) {
        const top = 112;
        const bottom = height - 84;
        const groups = {
            RISK: nodes.filter((node) => node.type === "RISK"),
            INITIATIVE: nodes.filter((node) => node.type === "INITIATIVE"),
            OTHER: nodes.filter((node) => node.type !== "RISK" && node.type !== "INITIATIVE")
        };

        const positioned = [];
        positionColumn(groups.RISK, width * 0.28, top, bottom, positioned);
        positionColumn(groups.INITIATIVE, width * 0.72, top, bottom, positioned);
        positionColumn(groups.OTHER, width * 0.5, top, bottom, positioned);
        return positioned;
    }

    drawEdge(layer, edge) {
        const source = edge.sourceNode;
        const target = edge.targetNode;
        const midX = (source.x + target.x) / 2;
        const path = svgEl("path", {
            class: "map-edge",
            d: `M ${source.x} ${source.y} C ${midX} ${source.y}, ${midX} ${target.y}, ${target.x} ${target.y}`,
            fill: "none",
            "data-source": source.id,
            "data-target": target.id
        });
        layer.append(path);
        this.edgeElements.push({ edge, element: path });
    }

    drawNode(layer, node, width) {
        const group = svgEl("g", {
            class: `map-node node-${node.type.toLowerCase()}`,
            transform: `translate(${node.x}, ${node.y})`,
            tabindex: "0",
            role: "button",
            "data-id": node.id
        });

        const radius = radiusFor(node);
        group.append(
            svgEl("circle", {
                class: "node-halo",
                r: radius * 3.4,
                fill: colorFor(node),
                opacity: "0.08"
            }),
            svgEl("circle", {
                class: "node-core",
                r: radius,
                fill: colorFor(node),
                stroke: "rgba(255,255,255,0.26)",
                "stroke-width": "1"
            })
        );

        const label = svgEl("text", {
            x: labelAnchorX(node, width),
            y: 4,
            "text-anchor": labelAnchor(node, width)
        });
        label.textContent = truncateLabel(node.label, width < 700 ? 28 : 42);
        group.append(label);

        const title = svgEl("title");
        title.textContent = `${node.type} :: ${node.tower_id} :: ${node.label}`;
        group.append(title);

        group.addEventListener("mouseenter", () => this.highlightNode(node.id));
        group.addEventListener("mouseleave", () => this.resetHighlight());
        group.addEventListener("click", () => this.selectNode(node.id));
        group.addEventListener("keydown", (event) => {
            if (event.key === "Enter" || event.key === " ") {
                event.preventDefault();
                this.selectNode(node.id);
            }
        });

        layer.append(group);
        this.nodeElements.set(node.id, group);
        this.nodeElements.set(node.id.toLowerCase(), group);
    }

    selectNode(nodeId) {
        if (!nodeId) return;
        this.selectedId = nodeId;
        this.highlightNode(nodeId, true);
        window.dispatchEvent(new CustomEvent("node-selected", { detail: { id: nodeId } }));
    }

    highlightNode(nodeId, persistent = false) {
        if (!nodeId) return;
        const target = this.nodeElements.get(nodeId) || this.nodeElements.get(String(nodeId).toLowerCase());
        if (!target) return;

        const connected = new Set([target.dataset.id]);
        this.visibleEdges.forEach((edge) => {
            if (sameId(edge.sourceNode.id, target.dataset.id)) connected.add(edge.targetNode.id);
            if (sameId(edge.targetNode.id, target.dataset.id)) connected.add(edge.sourceNode.id);
        });

        this.nodeElements.forEach((element, key) => {
            if (key !== element.dataset.id) return;
            const active = connected.has(element.dataset.id);
            element.classList.toggle("dimmed", !active);
            element.classList.toggle("selected", sameId(element.dataset.id, target.dataset.id) && persistent);
        });

        this.edgeElements.forEach(({ edge, element }) => {
            const active = sameId(edge.sourceNode.id, target.dataset.id) || sameId(edge.targetNode.id, target.dataset.id);
            element.classList.toggle("dimmed", !active);
            element.classList.toggle("active", active);
        });
    }

    resetHighlight() {
        if (this.selectedId) {
            this.highlightNode(this.selectedId, true);
            return;
        }
        this.nodeElements.forEach((element, key) => {
            if (key !== element.dataset.id) return;
            element.classList.remove("dimmed", "selected");
        });
        this.edgeElements.forEach(({ element }) => {
            element.classList.remove("dimmed", "active");
        });
    }
}

function rankedNodes(nodes, state) {
    return [...nodes].sort((a, b) => rankNode(b, state) - rankNode(a, state));
}

function rankNode(node, state) {
    const typeWeight = node.type === "INITIATIVE" ? 12 : node.type === "RISK" ? 9 : 3;
    return typeWeight + (state.getDegree(node.id) * 7) + (node.score ? node.score : 0);
}

function positionColumn(nodes, x, top, bottom, output) {
    const sorted = nodes.slice().sort((a, b) => a.label.localeCompare(b.label));
    const span = Math.max(1, bottom - top);
    sorted.forEach((node, index) => {
        const y = sorted.length === 1 ? top + span / 2 : top + (span * index / (sorted.length - 1));
        output.push({ ...node, x, y });
    });
}

function buildNodeMap(nodes) {
    const map = new Map();
    nodes.forEach((node) => {
        map.set(node.id, node);
        map.set(node.id.toLowerCase(), node);
    });
    return map;
}

function findInMap(map, id) {
    if (!id) return null;
    return map.get(id) || map.get(String(id).toLowerCase()) || null;
}

function svgEl(name, attrs = {}) {
    const element = document.createElementNS(SVG_NS, name);
    Object.entries(attrs).forEach(([key, value]) => {
        element.setAttribute(key, String(value));
    });
    return element;
}

function clearSvg(svg) {
    while (svg.firstChild) svg.removeChild(svg.firstChild);
}

function drawEmpty(svg, width, height) {
    const text = svgEl("text", {
        class: "map-empty",
        x: width / 2,
        y: height / 2,
        "text-anchor": "middle"
    });
    text.textContent = "NO_TOPOLOGY_DATA";
    svg.append(text);
}

function colorFor(node) {
    if (node.type === "RISK") return "#ee6666";
    if (node.type === "INITIATIVE") return "#86efac";
    return "#8ea2ff";
}

function radiusFor(node) {
    const degree = window.TerminalState ? window.TerminalState.getDegree(node.id) : 0;
    return Math.max(4, Math.min(10, 4 + degree * 0.8));
}

function labelAnchor(node, width) {
    if (width < 760) return "middle";
    return node.type === "RISK" ? "end" : "start";
}

function labelAnchorX(node, width) {
    if (width < 760) return 0;
    return node.type === "RISK" ? -14 : 14;
}

function truncateLabel(value, limit) {
    const text = String(value || "");
    if (text.length <= limit) return text;
    return `${text.slice(0, Math.max(0, limit - 1))}...`;
}

function hashUnit(value) {
    const text = String(value || "");
    let hash = 0;
    for (let index = 0; index < text.length; index += 1) {
        hash = ((hash << 5) - hash + text.charCodeAt(index)) | 0;
    }
    return Math.abs(hash % 1000) / 1000;
}

function clamp(value, min, max) {
    return Math.max(min, Math.min(max, value));
}

function sameId(a, b) {
    return String(a).toLowerCase() === String(b).toLowerCase();
}

customElements.define("semantic-map", SemanticMap);
