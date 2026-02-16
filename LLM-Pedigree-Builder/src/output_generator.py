"""Generate visual and shareable artifacts for pedigree data."""

from __future__ import annotations

import io
import json
from pathlib import Path
from typing import Any, Dict, Optional

import matplotlib.pyplot as plt
import networkx as nx
import qrcode
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from src.analysis_engine import AnalysisResult, build_graph


def build_pedigree_figure(pedigree: Dict[str, Any], output_path: Optional[str] = None) -> io.BytesIO:
    graph = build_graph(pedigree)
    fig, ax = plt.subplots(figsize=(8, 6))

    if graph.number_of_nodes() == 0:
        ax.text(0.5, 0.5, "No family members yet", ha="center", va="center")
        ax.axis("off")
    else:
        pos = nx.spring_layout(graph, seed=42)
        labels = {node: data.get("name", str(node)) for node, data in graph.nodes(data=True)}
        nx.draw_networkx_nodes(graph, pos, node_color="#d6eaf8", node_size=1200, ax=ax)
        nx.draw_networkx_labels(graph, pos, labels=labels, font_size=8, ax=ax)
        nx.draw_networkx_edges(graph, pos, arrows=True, ax=ax)
        edge_labels = {(u, v): data.get("type", "") for u, v, data in graph.edges(data=True)}
        nx.draw_networkx_edge_labels(graph, pos, edge_labels=edge_labels, font_size=7, ax=ax)
        ax.set_title("Family Pedigree")
        ax.axis("off")

    buffer = io.BytesIO()
    fig.tight_layout()
    fig.savefig(buffer, format="png", dpi=180)
    plt.close(fig)
    buffer.seek(0)

    if output_path:
        Path(output_path).write_bytes(buffer.getvalue())
        buffer.seek(0)
    return buffer


def generate_qr_code(pedigree: Dict[str, Any], output_path: str) -> None:
    payload = json.dumps(pedigree, ensure_ascii=False)
    image = qrcode.make(payload)
    image.save(output_path)


def generate_pedigree_pdf(
    pedigree: Dict[str, Any],
    output_path: str,
    figure_png: io.BytesIO,
    analysis: Optional[AnalysisResult] = None,
    notes: str = "",
) -> None:
    c = canvas.Canvas(output_path, pagesize=letter)
    width, height = letter

    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, height - 50, "LLM Pedigree Builder Report")
    c.setFont("Helvetica", 10)
    c.drawString(50, height - 70, "Warning: Not medical advice. For clinician review only.")

    c.drawImage(ImageReader(figure_png), 50, height - 380, width=500, height=280, preserveAspectRatio=True)

    y = height - 400
    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, y, "People Summary")
    y -= 18
    c.setFont("Helvetica", 9)

    for person in pedigree.get("people", []):
        text = f"#{person['id']} {person['name']} ({person['gender']}) DOB: {person['dob']} Conditions: {', '.join(person['conditions']) or 'None'}"
        c.drawString(55, y, text[:110])
        y -= 12
        if y < 120:
            c.showPage()
            y = height - 60

    if analysis:
        y -= 10
        c.setFont("Helvetica-Bold", 11)
        c.drawString(50, y, "Risk Analysis")
        y -= 16
        c.setFont("Helvetica", 9)
        c.drawString(55, y, f"Inbreeding coefficient (approx): {analysis.inbreeding_coefficient}")
        y -= 12
        c.drawString(55, y, f"Risk level: {analysis.risk_level}")
        y -= 12
        for flag in analysis.inheritance_flags:
            c.drawString(55, y, f"- {flag}"[:110])
            y -= 12

    if notes:
        y -= 12
        c.setFont("Helvetica-Bold", 11)
        c.drawString(50, y, "Notes")
        y -= 14
        c.setFont("Helvetica", 9)
        for line in notes.splitlines():
            c.drawString(55, y, line[:110])
            y -= 12

    c.save()
