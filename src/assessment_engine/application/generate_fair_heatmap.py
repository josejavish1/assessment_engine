import json
import sys
from pathlib import Path

import matplotlib.patches as patches
import matplotlib.pyplot as plt


def generate_heatmap(payload_path: str, output_image_path: str):
    r"""{'docstring': 'Generates and saves a Factor Analysis of Information Risk (FAIR) heatmap.\n\nThis function ingests risk data from a structured JSON file, processing\nThreat Event Frequency (TEF) and Loss Magnitude (LM) for each finding. The\nTEF and LM values are normalized to an integer scale of 1 to 5.\n\nThe risks are plotted onto a 5x5 grid where the y-axis represents TEF and\nthe x-axis represents LM. Cell backgrounds are color-coded based on the\nseverity score (TEF * LM): low (<8), medium (8-14), and high (>=15). Risk\nidentifiers are rendered within their corresponding grid cells. The resulting\nmatplotlib figure is saved as a PNG image to the specified path.\n\nArgs:\n    payload_path (str): The path to the input JSON file. The file is expected\n        to contain a `pillars_analysis` key, which holds a list of pillar\n        objects. Each pillar object should have a `health_check_asis` key\n        containing a list of findings. Each finding must provide numeric\n        `threat_event_frequency` and `loss_magnitude` values. Missing values\n        default to 3.\n    output_image_path (str): The destination file path for the generated PNG\n        heatmap. Parent directories are created automatically if they do not\n        exist.\n\nReturns:\n    None. The function writes the output to a file.\n\nRaises:\n    json.JSONDecodeError: If the input file at `payload_path` contains\n        malformed JSON.\n    TypeError: If the JSON data structure is invalid, such as a non-iterable\n        value where a list is expected during parsing.\n    ValueError: If `threat_event_frequency` or `loss_magnitude` values have\n        a non-numeric type that cannot be converted.\n    OSError: If writing the output image to `output_image_path` fails due to\n        an I/O or permissions error.'}."""
    payload_path_obj = Path(payload_path)
    output_image_path_obj = Path(output_image_path)

    print(f"📊 Generando Mapa de Calor FAIR para: {payload_path_obj}")

    # Ingest and structure risk data from the request payload.
    risks = []
    if payload_path_obj.exists():
        with open(payload_path_obj, "r", encoding="utf-8-sig") as f:
            bp = json.load(f)

        r_idx = 1
        for pilar in bp.get("pillars_analysis", []):
            pilar.get("pilar_name", "Pilar")
            for finding in pilar.get("health_check_asis", []):
                #
                tef = min(
                    5, max(1, int(round(finding.get("threat_event_frequency", 3))))
                )
                lm = min(5, max(1, int(round(finding.get("loss_magnitude", 3)))))

                risks.append({"id": f"RVS{r_idx:02d}", "tef": tef, "lm": lm})
                r_idx += 1

    print(f"   ├─ Detectados {len(risks)} riesgos activos en el payload.")

    # Group risks by their corresponding matrix cell, defined by Threat Event Frequency and Loss Magnitude coordinates on a 1-5 scale.
    # In accordance with the FAIR framework, the Y-axis (Threat Event Frequency) is oriented with its origin at the bottom (1) and ascends to the top (5).
    # The X-axis (Loss Magnitude) follows the conventional orientation, with values increasing from left (1) to right (5).
    grid_risks = {r: {c: [] for c in range(1, 6)} for r in range(1, 6)}
    for r in risks:
        grid_risks[r["tef"]][r["lm"]].append(r["id"])

    # Generate the FAIR heatmap visualization using the Matplotlib backend.
    fig, ax = plt.subplots(figsize=(6, 5), dpi=300)

    # Adhere to the corporate design standard by utilizing the specified pastel color palette for the heatmap cell backgrounds.
    color_low = "#D5F5E3"  # Define the standard color for low-severity risk cells.
    color_medium = (
        "#FCF3CF"  # Define the standard color for medium-severity risk cells.
    )
    color_high = "#FADBD8"  # Define the standard color for high-severity risk cells.

    # Iterate through the 25 matrix positions to render each heatmap cell.
    for r in range(1, 6):  # Configure the Y-axis for Threat Event Frequency (TEF).
        for c in range(1, 6):  # Configure the X-axis for Loss Magnitude (LM).
            # Calculate the cell's severity score as a function of its Threat Event Frequency (TEF) and Loss Magnitude (LM) coordinates.
            severity = r * c
            if severity >= 15:
                bg_color = color_high
            elif severity >= 8:
                bg_color = color_medium
            else:
                bg_color = color_low

            # The Matplotlib Rectangle patch anchor point is its lower-left corner, which dictates the coordinate placement for rendering.
            # Translate the 1-based matrix coordinates (column, row) to the 0-based coordinate system required by Matplotlib for plotting (c-1, r-1).
            rect = patches.Rectangle(
                (c - 0.5, r - 0.5),
                1.0,
                1.0,
                facecolor=bg_color,
                edgecolor="#FFFFFF",  # Apply a thick white border to each cell to create clear visual separation within the grid.
                linewidth=2.0,
            )
            ax.add_patch(rect)

            # Overlay risk identifiers onto their corresponding heatmap cells.
            cell_risks = grid_risks[r][c]
            if cell_risks:
                # When multiple risks occupy a single cell, identifiers are newline-delimited to ensure text wrapping and maintain readability.
                risk_text = "\n".join(cell_risks)
                ax.text(
                    c,
                    r,
                    risk_text,
                    color="#2E404D",  # Set text elements to the standard corporate dark color for consistent branding and readability.
                    fontsize=9,
                    fontweight="bold",
                    ha="center",
                    va="center",
                    family="sans-serif",
                )
            else:
                ax.text(
                    c, r, "-", color="#AAB7B8", fontsize=9, ha="center", va="center"
                )

    # Establish plot axis limits to precisely frame the 5x5 FAIR matrix grid.
    ax.set_xlim(0.5, 5.5)
    ax.set_ylim(0.5, 5.5)

    # Configure axis ticks to represent the discrete 1-5 integer scale of the FAIR matrix.
    ax.set_xticks(range(1, 6))
    ax.set_yticks(range(1, 6))
    ax.set_xticklabels(
        [f"LM {i}" for i in range(1, 6)],
        fontsize=8.5,
        fontweight="bold",
        color="#5D6D7E",
    )
    ax.set_yticklabels(
        [f"TEF {i}" for i in range(1, 6)],
        fontsize=8.5,
        fontweight="bold",
        color="#5D6D7E",
    )

    # Assign labels to the X (Loss Magnitude) and Y (Threat Event Frequency) axes.
    ax.set_xlabel(
        "Magnitud de Pérdida (LM) — Severidad de Impacto",
        fontsize=10,
        fontweight="bold",
        color="#2E404D",
        labelpad=10,
    )
    ax.set_ylabel(
        "Frecuencia de Amenaza (TEF) — Probabilidad",
        fontsize=10,
        fontweight="bold",
        color="#2E404D",
        labelpad=10,
    )
    ax.set_title(
        "Matriz de Exposición Cuantitativa al Riesgo (FAIR)",
        fontsize=11,
        fontweight="bold",
        color="#0072BC",
        pad=15,
    )

    # Disable all plot spines to create a minimalist, frameless heatmap that emphasizes the data grid.
    for spine in ["top", "right", "left", "bottom"]:
        ax.spines[spine].set_visible(False)

    ax.tick_params(
        axis="both", which="both", length=0
    )  # Disable axis tick marks to de-emphasize the axes and focus user attention on the grid.
    ax.set_aspect(
        "equal"
    )  # Set a 1:1 aspect ratio to ensure heatmap cells are rendered as squares, preventing spatial distortion.

    plt.tight_layout()

    #
    output_image_path_obj.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_image_path_obj, bbox_inches="tight", dpi=300)
    plt.close()

    print(f"🎉 ¡Mapa de calor FAIR guardado con éxito en: {output_image_path_obj}!")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Uso: python generate_fair_heatmap.py <payload_path> <output_image_path>")
        sys.exit(1)
    generate_heatmap(sys.argv[1], sys.argv[2])
