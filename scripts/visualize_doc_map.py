#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Interactive documentation map generator.

This script parses the documentation-map.yaml configuration and generates a
high-fidelity, interactive, dynamic 2D Force-Directed Graph using D3.js.
The output is written as a self-contained HTML file in working/documentation_map_visual.html.
"""

import json
import os
import sys
from pathlib import Path

import yaml


def generate_interactive_map(
    yaml_path_str: str = "docs/documentation-map.yaml",
    output_html_str: str = "working/documentation_map_visual.html",
) -> bool:
    """Parses documentation-map.yaml and exports a D3.js interactive HTML visualization.

    Args:
        yaml_path_str: Path to the input documentation-map YAML file.
        output_html_str: Path where the output interactive HTML file should be written.

    Returns:
        True if the visualization was successfully generated, False otherwise.
    """
    yaml_path = Path(yaml_path_str)
    output_html = Path(output_html_str)

    if not yaml_path.exists():
        print(f"[-] Input file not found: {yaml_path}", file=sys.stderr)
        return False

    try:
        with open(yaml_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except Exception as e:
        print(f"[-] Failed to parse YAML file: {e}", file=sys.stderr)
        return False

    nodes = []
    links = []
    node_set = set()

    entries = data.get("entries", [])
    if not isinstance(entries, list):
        print("[-] Invalid format: 'entries' must be a list.", file=sys.stderr)
        return False

    for entry in entries:
        path = entry.get("path")
        if not path:
            continue

        title = entry.get("title", path)
        doc_type = entry.get("doc_type", "unknown")
        status = entry.get("status", "Draft")

        node_set.add(path)
        nodes.append(
            {
                "id": path,
                "title": title,
                "type": doc_type,
                "status": status,
                "group": 1
                if doc_type == "canonical"
                else (2 if doc_type == "operational" else 3),
            }
        )

        # Parse source of truth dependencies
        for sot in entry.get("source_of_truth", []):
            if sot not in node_set:
                node_set.add(sot)
                nodes.append(
                    {
                        "id": sot,
                        "title": os.path.basename(sot),
                        "type": "source",
                        "status": "External/Code/Config",
                        "group": 4,
                    }
                )
            links.append({"source": sot, "target": path, "value": 2})

    # Embedded HTML with responsive D3.js force-directed graph representation
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Sovereign DocMap - assessment-engine</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            margin: 0;
            background-color: #0d1117;
            color: #c9d1d9;
            overflow: hidden;
        }}
        #header {{
            position: absolute;
            top: 20px;
            left: 20px;
            background: rgba(22, 27, 34, 0.9);
            padding: 15px 25px;
            border-radius: 8px;
            border: 1px solid #30363d;
            pointer-events: auto;
            max-width: 400px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.5);
        }}
        h1 {{ margin: 0 0 5px 0; font-size: 1.5rem; color: #58a6ff; }}
        h2 {{ margin: 0; font-size: 0.9rem; color: #8b949e; font-weight: normal; }}
        #legend {{
            margin-top: 15px;
            font-size: 0.8rem;
        }}
        .legend-item {{ display: flex; align-items: center; margin-bottom: 5px; }}
        .legend-color {{ width: 12px; height: 12px; margin-right: 8px; border-radius: 3px; }}
        #tooltip {{
            position: absolute;
            background: #161b22;
            border: 1px solid #30363d;
            padding: 10px;
            border-radius: 6px;
            font-size: 0.85rem;
            pointer-events: none;
            opacity: 0;
            transition: opacity 0.2s;
            box-shadow: 0 4px 12px rgba(0,0,0,0.5);
        }}
        svg {{ width: 100vw; height: 100vh; }}
        .node {{ stroke: #0d1117; stroke-width: 2px; cursor: grab; }}
        .node:active {{ cursor: grabbing; }}
        .link {{ stroke: #30363d; stroke-opacity: 0.6; stroke-width: 1.5px; fill: none; }}
    </style>
</head>
<body>
    <div id="header">
        <h1>Sovereign DocMap v4</h1>
        <h2>Assessment Engine - Documentation Relationship Graph</h2>
        <div id="legend">
            <div class="legend-item"><div class="legend-color" style="background: #1f77b4;"></div> Canonical (Sources of Truth)</div>
            <div class="legend-item"><div class="legend-color" style="background: #2ca02c;"></div> Operational (Guides & Processes)</div>
            <div class="legend-item"><div class="legend-color" style="background: #ff7f0e;"></div> Reference / Generated</div>
            <div class="legend-item"><div class="legend-color" style="background: #9467bd;"></div> Underlying Source of Truth</div>
        </div>
    </div>
    
    <div id="tooltip"></div>
    <svg></svg>

    <script>
        const graph = {{
            nodes: {json.dumps(nodes)},
            links: {json.dumps(links)}
        }};

        const svg = d3.select("svg"),
              width = window.innerWidth,
              height = window.innerHeight;

        const colorScale = d3.scaleOrdinal()
            .domain([1, 2, 3, 4])
            .range(["#1f77b4", "#2ca02c", "#ff7f0e", "#9467bd"]);

        const simulation = d3.forceSimulation(graph.nodes)
            .force("link", d3.forceLink(graph.links).id(d => d.id).distance(120))
            .force("charge", d3.forceManyBody().strength(-150))
            .force("center", d3.forceCenter(width / 2, height / 2))
            .force("collision", d3.forceCollide().radius(25));

        // Arrow markers for dependency direction
        svg.append("defs").append("marker")
            .attr("id", "arrow")
            .attr("viewBox", "0 -5 10 10")
            .attr("refX", 20)
            .attr("refY", 0)
            .attr("markerWidth", 6)
            .attr("markerHeight", 6)
            .attr("orient", "auto")
            .append("path")
            .attr("d", "M0,-5L10,0L0,5")
            .attr("fill", "#30363d");

        const link = svg.append("g")
            .attr("class", "links")
            .selectAll("line")
            .data(graph.links)
            .enter().append("line")
            .attr("class", "link")
            .attr("marker-end", "url(#arrow)");

        const node = svg.append("g")
            .attr("class", "nodes")
            .selectAll("circle")
            .data(graph.nodes)
            .enter().append("circle")
            .attr("class", "node")
            .attr("r", d => d.group === 4 ? 6 : 10)
            .attr("fill", d => colorScale(d.group))
            .call(d3.drag()
                .on("start", dragstarted)
                .on("drag", dragged)
                .on("end", dragended));

        const label = svg.append("g")
            .attr("class", "labels")
            .selectAll("text")
            .data(graph.nodes)
            .enter().append("text")
            .attr("font-size", "10px")
            .attr("fill", "#8b949e")
            .attr("dx", 14)
            .attr("dy", 4)
            .text(d => d.title);

        const tooltip = d3.select("#tooltip");

        node.on("mouseover", function(event, d) {{
            d3.select(this).attr("stroke", "#58a6ff").attr("stroke-width", "3px");
            tooltip.transition().duration(100).style("opacity", .9);
            tooltip.html(`<strong>Path:</strong> ${{d.id}}<br/>` +
                         `<strong>Title:</strong> ${{d.title}}<br/>` +
                         `<strong>Type:</strong> ${{d.type}}<br/>` +
                         `<strong>Status:</strong> ${{d.status}}`)
                   .style("left", (event.pageX + 15) + "px")
                   .style("top", (event.pageY - 28) + "px");
        }})
        .on("mousemove", function(event) {{
            tooltip.style("left", (event.pageX + 15) + "px")
                   .style("top", (event.pageY - 28) + "px");
        }})
        .on("mouseout", function() {{
            d3.select(this).attr("stroke", "#0d1117").attr("stroke-width", "2px");
            tooltip.transition().duration(100).style("opacity", 0);
        }});

        simulation.on("tick", () => {{
            link
                .attr("x1", d => d.source.x)
                .attr("y1", d => d.source.y)
                .attr("x2", d => d.target.x)
                .attr("y2", d => d.target.y);

            node
                .attr("cx", d => d.x)
                .attr("cy", d => d.y);

            label
                .attr("x", d => d.x)
                .attr("y", d => d.y);
        }});

        function dragstarted(event, d) {{
            if (!event.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
        }}

        function dragged(event, d) {{
            d.fx = event.x;
            d.fy = event.y;
        }}

        function dragended(event, d) {{
            if (!event.active) simulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
        }}

        window.addEventListener("resize", () => {{
            const w = window.innerWidth;
            const h = window.innerHeight;
            svg.attr("width", w).attr("height", h);
            simulation.force("center", d3.forceCenter(w / 2, h / 2)).restart();
        }});
    </script>
</body>
</html>
"""

    try:
        output_html.parent.mkdir(parents=True, exist_ok=True)
        with open(output_html, "w", encoding="utf-8") as f:
            f.write(html_content)
        print(f"[+] Dynamic map successfully generated at: {output_html}")
        return True
    except Exception as e:
        print(f"[-] Failed to write HTML output: {e}", file=sys.stderr)
        return False


if __name__ == "__main__":
    success = generate_interactive_map()
    sys.exit(0 if success else 1)
