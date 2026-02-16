"""Pedigree analytics for clinician-facing risk triage."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Set, Tuple

try:
    import networkx as nx  # type: ignore
except Exception:  # pragma: no cover
    nx = None


class _FallbackDiGraph:
    def __init__(self) -> None:
        self.nodes_data: Dict[int, Dict[str, Any]] = {}
        self.edge_data: Dict[Tuple[int, int], Dict[str, Any]] = {}

    def add_node(self, node: int, **attrs: Any) -> None:
        self.nodes_data[node] = attrs

    def add_edge(self, u: int, v: int, **attrs: Any) -> None:
        self.edge_data[(u, v)] = attrs

    def number_of_nodes(self) -> int:
        return len(self.nodes_data)

    def edges(self):
        return self.edge_data

    def successors(self, node: int):
        return [v for (u, v) in self.edge_data if u == node]


def _build_cycle_basis_fallback(graph: _FallbackDiGraph) -> List[List[int]]:
    adj: Dict[int, Set[int]] = {k: set() for k in graph.nodes_data}
    for (u, v) in graph.edge_data:
        adj.setdefault(u, set()).add(v)
        adj.setdefault(v, set()).add(u)

    cycles: List[List[int]] = []
    visited: Set[int] = set()

    for node in adj:
        if node in visited:
            continue
        stack = [(node, None)]
        parent: Dict[int, int | None] = {node: None}
        while stack:
            cur, par = stack.pop()
            if cur in visited:
                continue
            visited.add(cur)
            for nbr in adj[cur]:
                if nbr == par:
                    continue
                if nbr in parent:
                    cycles.append([cur, nbr])
                else:
                    parent[nbr] = cur
                    stack.append((nbr, cur))
    return cycles


@dataclass
class AnalysisResult:
    inbreeding_coefficient: float
    inheritance_flags: List[str]
    risk_level: str
    recommendations: List[str]


def build_graph(pedigree: Dict[str, Any]):
    if nx is not None:
        graph = nx.DiGraph()
    else:
        graph = _FallbackDiGraph()

    for person in pedigree.get("people", []):
        graph.add_node(person["id"], **person)
    for relationship in pedigree.get("relationships", []):
        graph.add_edge(relationship["from"], relationship["to"], type=relationship["type"])
    return graph


def estimate_inbreeding(graph) -> float:
    """Approximate inbreeding coefficient using detected consanguineous loops."""
    if nx is not None and hasattr(graph, "to_undirected"):
        undirected = graph.to_undirected()
        cycles = nx.cycle_basis(undirected)
        total_cycle_nodes = sum(len(cycle) for cycle in cycles)
        if not cycles:
            return 0.0
    else:
        cycles = _build_cycle_basis_fallback(graph)
        if not cycles:
            return 0.0
        total_cycle_nodes = sum(len(cycle) for cycle in cycles)

    scaled = min(0.25, total_cycle_nodes / max(1, graph.number_of_nodes()) * 0.03125)
    return round(scaled, 4)


def _condition_to_people(pedigree: Dict[str, Any]) -> Dict[str, List[int]]:
    mapping: Dict[str, List[int]] = {}
    for person in pedigree.get("people", []):
        for condition in person.get("conditions", []):
            mapping.setdefault(condition.lower(), []).append(person["id"])
    return mapping


def _has_edge_with_type(graph, u: int, v: int, relationship_type: str) -> bool:
    if nx is not None and hasattr(graph, "has_edge"):
        return graph.has_edge(u, v) and graph.edges[u, v].get("type") == relationship_type
    return (u, v) in graph.edge_data and graph.edge_data[(u, v)].get("type") == relationship_type


def _successors(graph, node: int):
    if nx is not None and hasattr(graph, "successors"):
        return list(graph.successors(node))
    return graph.successors(node)


def infer_inheritance_patterns(graph, pedigree: Dict[str, Any]) -> List[str]:
    flags: List[str] = []
    condition_map = _condition_to_people(pedigree)

    for condition, affected_ids in condition_map.items():
        if len(affected_ids) >= 2:
            sibling_pairs = 0
            for i in affected_ids:
                for j in affected_ids:
                    if i >= j:
                        continue
                    if _has_edge_with_type(graph, i, j, "sibling"):
                        sibling_pairs += 1
            if sibling_pairs >= 1:
                flags.append(f"Autosomal recessive pattern possible for {condition}")

        parent_child_hits = 0
        for affected_id in affected_ids:
            for nbr in _successors(graph, affected_id):
                if nbr in affected_ids and (_has_edge_with_type(graph, affected_id, nbr, "parent") or _has_edge_with_type(graph, affected_id, nbr, "child")):
                    parent_child_hits += 1
        if parent_child_hits >= 1:
            flags.append(f"Autosomal dominant transmission possible for {condition}")

    if not flags:
        flags.append("No clear inheritance pattern detected from available data")
    return sorted(set(flags))


def _risk_bucket(inbreeding: float, flags: List[str]) -> str:
    if inbreeding > 0.0625 or any("dominant" in f.lower() for f in flags):
        return "High"
    if inbreeding > 0.015625 or any("recessive" in f.lower() for f in flags):
        return "Moderate"
    return "Low"


def analyze_pedigree(pedigree: Dict[str, Any]) -> AnalysisResult:
    graph = build_graph(pedigree)
    inbreeding = estimate_inbreeding(graph)
    flags = infer_inheritance_patterns(graph, pedigree)
    risk = _risk_bucket(inbreeding, flags)

    recommendations = [
        "This tool is not medical advice; review with a licensed genetic counselor.",
        "Consider confirmatory genetic testing if there are multiple affected relatives.",
    ]
    if risk == "High":
        recommendations.append("Recommend expedited specialist referral and targeted screening.")
    elif risk == "Moderate":
        recommendations.append("Recommend non-urgent genetics referral and family-wide history validation.")

    return AnalysisResult(
        inbreeding_coefficient=inbreeding,
        inheritance_flags=flags,
        risk_level=risk,
        recommendations=recommendations,
    )
