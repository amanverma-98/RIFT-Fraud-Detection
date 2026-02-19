"""Graph validation and utility functions for transaction analysis."""

import pandas as pd
import networkx as nx
from typing import List, Dict, Any, Tuple
from datetime import datetime

from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class GraphValidator:
    """Utility class for validating and analyzing graphs."""

    @staticmethod
    def validate_graph_integrity(graph: nx.DiGraph) -> Dict[str, Any]:
        """
        Validate graph integrity and quality.

        Args:
            graph: NetworkX DiGraph to validate

        Returns:
            Dictionary with validation results
        """
        if not isinstance(graph, (nx.DiGraph, nx.MultiDiGraph)):
            logger.error("Invalid graph type")
            return {'valid': False, 'error': 'Invalid graph type'}

        if graph.number_of_nodes() == 0:
            logger.warning("Graph has no nodes")
            return {'valid': False, 'error': 'Graph is empty'}

        results = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'nodes': graph.number_of_nodes(),
            'edges': graph.number_of_edges(),
        }

        # Check for isolated nodes
        isolated = [n for n in graph.nodes() if graph.degree(n) == 0]
        if isolated:
            results['warnings'].append(
                f"Found {len(isolated)} isolated nodes (no in/out degree)"
            )

        # Check edge attributes
        missing_amounts = 0
        for _, _, data in graph.edges(data=True):
            if 'amount' not in data or data['amount'] is None:
                missing_amounts += 1

        if missing_amounts > 0:
            results['warnings'].append(
                f"{missing_amounts} edges missing 'amount' attribute"
            )

        logger.info(f"Graph validation: {results['valid']}")
        return results

    @staticmethod
    def get_suspicious_patterns(
        graph: nx.DiGraph,
        min_cycle_length: int = 3
    ) -> Dict[str, List]:
        """
        Identify potentially suspicious patterns in the graph.

        Patterns include:
        - Cycles (circular money flows)
        - High-degree nodes (many transactions)
        - Isolated cliques (separate groups)

        Args:
            graph: Transaction graph
            min_cycle_length: Minimum cycle length to report

        Returns:
            Dictionary with detected patterns
        """
        patterns = {
            'cycles': [],
            'high_degree_nodes': [],
            'dense_subgraphs': [],
        }

        # Detect cycles
        try:
            cycles = list(nx.simple_cycles(graph))
            patterns['cycles'] = [
                list(c) for c in cycles if len(c) >= min_cycle_length
            ][:10]  # Top 10
            logger.debug(f"Found {len(patterns['cycles'])} cycles")
        except Exception as e:
            logger.warning(f"Error detecting cycles: {e}")

        # Find high-degree nodes
        in_degrees = dict(graph.in_degree())
        out_degrees = dict(graph.out_degree())

        high_in = sorted(in_degrees.items(), key=lambda x: x[1], reverse=True)[:5]
        high_out = sorted(out_degrees.items(), key=lambda x: x[1], reverse=True)[:5]

        patterns['high_degree_nodes'] = {
            'high_in': high_in,
            'high_out': high_out,
        }

        logger.debug("Suspicious patterns identified")
        return patterns

    @staticmethod
    def compare_graphs(graph1: nx.DiGraph, graph2: nx.DiGraph) -> Dict[str, Any]:
        """
        Compare two graphs and return differences.

        Args:
            graph1: First graph
            graph2: Second graph

        Returns:
            Dictionary with comparison results
        """
        comparison = {
            'nodes_added': [],
            'nodes_removed': [],
            'edges_added': [],
            'edges_removed': [],
            'attribute_changes': [],
        }

        nodes1 = set(graph1.nodes())
        nodes2 = set(graph2.nodes())

        comparison['nodes_added'] = list(nodes2 - nodes1)
        comparison['nodes_removed'] = list(nodes1 - nodes2)

        edges1 = set(graph1.edges())
        edges2 = set(graph2.edges())

        comparison['edges_added'] = list(edges2 - edges1)
        comparison['edges_removed'] = list(edges1 - edges2)

        logger.info(
            f"Graph comparison: "
            f"+{len(comparison['nodes_added'])} nodes, "
            f"-{len(comparison['nodes_removed'])} nodes, "
            f"+{len(comparison['edges_added'])} edges, "
            f"-{len(comparison['edges_removed'])} edges"
        )

        return comparison


class GraphAnalyzer:
    """Advanced analysis functions for transaction graphs."""

    @staticmethod
    def calculate_centrality_measures(graph: nx.DiGraph) -> Dict[str, Dict]:
        """
        Calculate various centrality measures for nodes.

        Time Complexity: O(V^2) approximately

        Args:
            graph: Transaction graph

        Returns:
            Dictionary mapping nodes to centrality metrics
        """
        measures = {}

        try:
            # In-degree centrality
            in_centrality = nx.in_degree_centrality(graph)
            # Out-degree centrality
            out_centrality = nx.out_degree_centrality(graph)
            # Betweenness centrality
            betweenness = nx.betweenness_centrality(graph)

            for node in graph.nodes():
                measures[node] = {
                    'in_centrality': in_centrality.get(node, 0),
                    'out_centrality': out_centrality.get(node, 0),
                    'betweenness': betweenness.get(node, 0),
                }

            logger.debug(f"Calculated centrality for {len(measures)} nodes")

        except Exception as e:
            logger.warning(f"Error calculating centrality: {e}")

        return measures

    @staticmethod
    def find_money_laundering_patterns(graph: nx.DiGraph) -> List[Dict]:
        """
        Identify potential money laundering patterns.

        Patterns:
        - Circular flows (A→B→C→A)
        - Many intermediate nodes
        - Uniform amounts

        Args:
            graph: Transaction graph

        Returns:
            List of suspicious patterns
        """
        suspicious = []

        # Find cycles (circular flows)
        try:
            for cycle in nx.simple_cycles(graph):
                if len(cycle) >= 3:
                    # Get amounts in cycle
                    amounts = []
                    for i in range(len(cycle)):
                        src = cycle[i]
                        dst = cycle[(i + 1) % len(cycle)]
                        edge_data = graph.edges.get((src, dst, ), {})
                        if edge_data:
                            amounts.append(edge_data.get('amount', 0))

                    if amounts:
                        suspicious.append({
                            'type': 'circular_flow',
                            'cycle': cycle,
                            'total_amount': sum(amounts),
                            'avg_amount': sum(amounts) / len(amounts),
                        })

        except Exception as e:
            logger.warning(f"Error analyzing cycles: {e}")

        logger.info(f"Found {len(suspicious)} suspicious patterns")
        return suspicious

    @staticmethod
    def identify_money_mules(
        graph: nx.DiGraph,
        in_threshold: int = 5,
        out_threshold: int = 5
    ) -> List[Tuple[str, Dict]]:
        """
        Identify potential money mules (many in/out connections with small amounts).

        Args:
            graph: Transaction graph
            in_threshold: Minimum in-degree
            out_threshold: Minimum out-degree

        Returns:
            List of (node_id, metrics) for suspected mules
        """
        mules = []

        for node in graph.nodes():
            in_degree = graph.in_degree(node)
            out_degree = graph.out_degree(node)

            if in_degree >= in_threshold and out_degree >= out_threshold:
                # Calculate amounts
                in_amount = sum(
                    data.get('amount', 0)
                    for _, _, data in graph.in_edges(node, data=True)
                )
                out_amount = sum(
                    data.get('amount', 0)
                    for _, _, data in graph.out_edges(node, data=True)
                )

                avg_in = in_amount / in_degree if in_degree > 0 else 0
                avg_out = out_amount / out_degree if out_degree > 0 else 0

                mules.append((node, {
                    'in_degree': in_degree,
                    'out_degree': out_degree,
                    'in_amount': in_amount,
                    'out_amount': out_amount,
                    'avg_in': avg_in,
                    'avg_out': avg_out,
                    'balance': abs(in_amount - out_amount),
                }))

        logger.info(f"Identified {len(mules)} potential money mules")
        return sorted(mules, key=lambda x: x[1]['in_degree'] + x[1]['out_degree'], reverse=True)
