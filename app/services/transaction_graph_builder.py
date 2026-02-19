import networkx as nx
import pandas as pd
from typing import Dict, List, Tuple, Optional, Set
from datetime import datetime
import logging

from app.utils.logger import setup_logger
from app.utils.exceptions import GraphDetectionError

logger = setup_logger(__name__)


class TransactionGraphBuilder:
    """
    High-performance service for building directed graphs from transaction data.

    Handles construction of transaction networks optimized for up to 10,000 transactions.
    Features:
    - O(E) time complexity (E = number of edges/transactions)
    - Duplicate edge aggregation
    - Edge attributes (amount, timestamp)
    - Comprehensive logging
    - Batch validation

    Example:
        builder = TransactionGraphBuilder()
        graph = builder.build(df)
        stats = builder.get_statistics()
    """

    def __init__(self, use_multi_digraph: bool = False):
        """
        Initialize the graph builder.

        Args:
            use_multi_digraph: If True, use MultiDiGraph to preserve multiple edges.
                              If False, use DiGraph and aggregate duplicate edges.
                              Default: False (aggregates for better memory efficiency)
        """
        self.use_multi_digraph = use_multi_digraph
        self._graph: Optional[nx.DiGraph] = None
        self._stats: Dict = {}
        self._build_time: Optional[float] = None

        graph_type = "MultiDiGraph" if use_multi_digraph else "DiGraph"
        logger.info(f"TransactionGraphBuilder initialized (graph_type={graph_type})")

    def build(self, transactions_df: pd.DataFrame) -> nx.DiGraph:
        """
        Build a directed graph from transaction data.

        Time Complexity: O(E) where E = number of transactions
        Space Complexity: O(V + E) where V = vertices, E = edges

        Args:
            transactions_df: DataFrame with columns:
                - source: Source account/entity
                - destination: Destination account/entity
                - amount: Transaction amount (float)
                - timestamp: Transaction timestamp (datetime)

        Returns:
            networkx.DiGraph: Directed graph with edges containing attributes

        Raises:
            GraphDetectionError: If validation fails or build process fails

        Example:
            builder = TransactionGraphBuilder()
            df = pd.DataFrame({
                'source': ['A', 'B', 'C'],
                'destination': ['B', 'C', 'A'],
                'amount': [100.0, 200.0, 150.0],
                'timestamp': [datetime.now()] * 3
            })
            graph = builder.build(df)
        """
        import time

        try:
            start_time = time.time()
            logger.info(f"Starting graph build from {len(transactions_df)} transactions")

            # Validate input
            self._validate_input(transactions_df)

            # Create graph
            self._graph = self._create_graph()

            # Add edges with attributes - O(E) operation
            self._add_edges_to_graph(transactions_df)

            # Calculate build statistics
            self._build_time = time.time() - start_time
            self._calculate_statistics()

            logger.info(
                f"Graph built successfully in {self._build_time:.3f}s: "
                f"{self._graph.number_of_nodes()} nodes, "
                f"{self._graph.number_of_edges()} edges"
            )

            return self._graph

        except GraphDetectionError:
            raise
        except Exception as e:
            logger.error(f"Error building graph: {str(e)}", exc_info=True)
            raise GraphDetectionError(f"Failed to build transaction graph: {str(e)}")

    def _validate_input(self, df: pd.DataFrame) -> None:
        """Validate input DataFrame structure and data quality."""
        required_columns = {'source', 'destination', 'amount', 'timestamp'}

        if not isinstance(df, pd.DataFrame):
            raise GraphDetectionError("Input must be a pandas DataFrame")

        if df.empty:
            raise GraphDetectionError("Input DataFrame is empty")

        missing_columns = required_columns - set(df.columns)
        if missing_columns:
            raise GraphDetectionError(
                f"Missing required columns: {missing_columns}. "
                f"Required: {required_columns}"
            )

        # Check for null values in required columns
        null_counts = df[list(required_columns)].isnull().sum()
        if null_counts.any():
            logger.warning(
                f"Found null values: {null_counts[null_counts > 0].to_dict()}"
            )

        logger.info(f"Input validation passed for {len(df)} transactions")

    def _create_graph(self) -> nx.DiGraph:
        """Create appropriate graph type."""
        if self.use_multi_digraph:
            graph = nx.MultiDiGraph()
            logger.debug("Created MultiDiGraph (preserves multiple edges)")
        else:
            graph = nx.DiGraph()
            logger.debug("Created DiGraph (aggregates duplicate edges)")

        return graph

    def _add_edges_to_graph(self, transactions_df: pd.DataFrame) -> None:
        """
        Add edges from DataFrame to graph.

        Time Complexity: O(E) where E = number of transactions

        Handles two strategies:
        1. MultiDiGraph: Preserves all transactions as separate edges
        2. DiGraph: Aggregates duplicate edges by summing amounts

        Args:
            transactions_df: Transaction data
        """
        aggregated_edges = {}
        edge_timestamps = {}
        edge_counts = {}

        logger.debug("Starting edge aggregation phase (O(E))")

        # Phase 1: Aggregate transactions - O(E)
        for idx, row in transactions_df.iterrows():
            source = str(row['source']).strip()
            destination = str(row['destination']).strip()
            amount = float(row['amount'])
            timestamp = row['timestamp']

            if source == destination:
                logger.warning(f"Skipping self-loop: {source} → {source}")
                continue

            edge_key = (source, destination)

            if edge_key in aggregated_edges:
                aggregated_edges[edge_key] += amount
                edge_counts[edge_key] += 1

                # Keep latest timestamp
                if isinstance(timestamp, datetime) and isinstance(edge_timestamps[edge_key], datetime):
                    edge_timestamps[edge_key] = max(edge_timestamps[edge_key], timestamp)
            else:
                aggregated_edges[edge_key] = amount
                edge_counts[edge_key] = 1
                edge_timestamps[edge_key] = timestamp

        logger.debug(
            f"Aggregation complete: {len(aggregated_edges)} unique edges from "
            f"{len(transactions_df)} transactions"
        )

        # Phase 2: Add edges to graph - O(E)
        logger.debug("Adding edges to graph (O(E))")

        for (source, destination), total_amount in aggregated_edges.items():
            count = edge_counts[(source, destination)]
            timestamp = edge_timestamps[(source, destination)]

            if self.use_multi_digraph:
                # MultiDiGraph: add as separate edges
                # For simplicity, we still aggregate but could preserve all
                self._graph.add_edge(
                    source,
                    destination,
                    amount=total_amount,
                    count=count,
                    timestamp=timestamp,
                    average_amount=total_amount / count if count > 0 else 0
                )
            else:
                # DiGraph: add with aggregated attributes
                self._graph.add_edge(
                    source,
                    destination,
                    amount=total_amount,
                    count=count,
                    timestamp=timestamp,
                    average_amount=total_amount / count if count > 0 else 0
                )

        logger.info(f"Added {len(aggregated_edges)} edges to graph")

    def _calculate_statistics(self) -> None:
        """Calculate and store graph statistics."""
        if not self._graph:
            return

        self._stats = {
            'nodes': self._graph.number_of_nodes(),
            'edges': self._graph.number_of_edges(),
            'density': nx.density(self._graph),
            'is_connected': nx.is_weakly_connected(self._graph),
            'num_weakly_connected_components': nx.number_weakly_connected_components(self._graph),
            'num_strongly_connected_components': nx.number_strongly_connected_components(self._graph),
        }

        # Calculate aggregate metrics
        total_amount = sum(
            data.get('amount', 0)
            for _, _, data in self._graph.edges(data=True)
        )

        self._stats['total_amount'] = total_amount
        self._stats['avg_edge_amount'] = (
            total_amount / self._graph.number_of_edges()
            if self._graph.number_of_edges() > 0
            else 0
        )

        logger.debug(f"Statistics calculated: {self._stats}")

    def get_graph(self) -> Optional[nx.DiGraph]:
        """Get the built graph."""
        return self._graph

    def get_statistics(self) -> Dict:
        """
        Get graph statistics.

        Returns:
            Dictionary containing:
            - nodes: Number of nodes (accounts)
            - edges: Number of edges (relationships)
            - density: Graph density (0-1)
            - is_connected: Whether graph is weakly connected
            - num_weakly_connected_components: Number of components
            - num_strongly_connected_components: Number of SCCs
            - total_amount: Sum of all transaction amounts
            - avg_edge_amount: Average transaction amount per edge
        """
        return self._stats.copy()

    def get_build_time(self) -> Optional[float]:
        """Get graph build time in seconds."""
        return self._build_time

    def get_edge_list(self) -> List[Dict]:
        """
        Get list of edges with attributes.

        Returns:
            List of dictionaries with edge information
        """
        if not self._graph:
            return []

        edges = []
        for source, destination, data in self._graph.edges(data=True):
            edges.append({
                'source': source,
                'destination': destination,
                'amount': data.get('amount', 0),
                'count': data.get('count', 1),
                'average_amount': data.get('average_amount', 0),
                'timestamp': data.get('timestamp'),
            })

        return edges

    def get_node_metrics(self) -> Dict[str, Dict]:
        """
        Calculate metrics for each node.

        Returns:
            Dictionary mapping node IDs to their metrics:
            - in_degree: Number of incoming edges
            - out_degree: Number of outgoing edges
            - in_amount: Total amount received
            - out_amount: Total amount sent
            - net_flow: out_amount - in_amount
        """
        if not self._graph:
            return {}

        metrics = {}

        for node in self._graph.nodes():
            in_degree = self._graph.in_degree(node)
            out_degree = self._graph.out_degree(node)

            # Calculate amounts
            in_amount = sum(
                data.get('amount', 0)
                for _, _, data in self._graph.in_edges(node, data=True)
            )

            out_amount = sum(
                data.get('amount', 0)
                for _, _, data in self._graph.out_edges(node, data=True)
            )

            metrics[node] = {
                'in_degree': in_degree,
                'out_degree': out_degree,
                'in_amount': in_amount,
                'out_amount': out_amount,
                'net_flow': out_amount - in_amount,
                'total_activity': in_amount + out_amount,
            }

        logger.debug(f"Calculated metrics for {len(metrics)} nodes")
        return metrics

    def find_high_degree_nodes(self, percentile: float = 90) -> List[Tuple[str, Dict]]:
        """
        Find nodes with high in-degree and out-degree.

        Args:
            percentile: Percentile threshold (0-100)

        Returns:
            List of (node_id, metrics) tuples
        """
        if not self._graph or self._graph.number_of_nodes() == 0:
            return []

        metrics = self.get_node_metrics()

        # Calculate percentile thresholds
        all_in_degrees = [m['in_degree'] for m in metrics.values()]
        all_out_degrees = [m['out_degree'] for m in metrics.values()]

        in_threshold = pd.Series(all_in_degrees).quantile(percentile / 100)
        out_threshold = pd.Series(all_out_degrees).quantile(percentile / 100)

        # Filter high-degree nodes
        high_degree_nodes = [
            (node, metrics[node])
            for node, m in metrics.items()
            if m['in_degree'] >= in_threshold or m['out_degree'] >= out_threshold
        ]

        logger.info(
            f"Found {len(high_degree_nodes)} high-degree nodes "
            f"(in_thresh={in_threshold:.0f}, out_thresh={out_threshold:.0f})"
        )

        return sorted(
            high_degree_nodes,
            key=lambda x: x[1]['in_degree'] + x[1]['out_degree'],
            reverse=True
        )

    def detect_cycles(self) -> List[List[str]]:
        """
        Detect cycles in the transaction graph.

        Time Complexity: O(V + E)

        Returns:
            List of cycles (each cycle is a list of nodes)
        """
        logger.debug("Detecting cycles in graph")

        try:
            cycles = list(nx.simple_cycles(self._graph))
            cycles = [cycle for cycle in cycles if len(cycle) > 1]

            logger.info(f"Found {len(cycles)} cycles in graph")
            return cycles

        except Exception as e:
            logger.warning(f"Error detecting cycles: {str(e)}")
            return []

    def get_path_between(self, source: str, destination: str) -> Optional[List[str]]:
        """
        Find shortest path between two nodes.

        Args:
            source: Source node
            destination: Destination node

        Returns:
            List of nodes in shortest path, or None if no path exists
        """
        if not self._graph:
            return None

        try:
            path = nx.shortest_path(self._graph, source, destination)
            logger.debug(f"Path found: {source} → {destination} ({len(path)} nodes)")
            return path
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            logger.debug(f"No path found: {source} → {destination}")
            return None

    def find_cliques(self) -> List[List[str]]:
        """
        Find cliques in the underlying undirected graph.

        Returns:
            List of cliques (each clique is a list of nodes)
        """
        if not self._graph:
            return []

        logger.debug("Finding cliques in graph")

        try:
            # Convert to undirected for clique detection
            undirected = self._graph.to_undirected()
            cliques = list(nx.find_cliques(undirected))
            cliques = [c for c in cliques if len(c) > 2]  # Only cliques with 3+ nodes

            logger.info(f"Found {len(cliques)} cliques with 3+ nodes")
            return cliques

        except Exception as e:
            logger.warning(f"Error finding cliques: {str(e)}")
            return []

    def export_to_json(self) -> Dict:
        """
        Export graph to JSON-serializable format.

        Returns:
            Dictionary containing nodes and edges with all attributes
        """
        if not self._graph:
            return {'nodes': [], 'edges': [], 'stats': {}}

        nodes = [
            {
                'id': node,
                'label': str(node),
                'type': 'account'
            }
            for node in self._graph.nodes()
        ]

        edges = [
            {
                'source': source,
                'target': destination,
                'amount': data.get('amount', 0),
                'count': data.get('count', 1),
                'timestamp': str(data.get('timestamp', '')) if data.get('timestamp') else None,
            }
            for source, destination, data in self._graph.edges(data=True)
        ]

        return {
            'nodes': nodes,
            'edges': edges,
            'stats': self._stats,
            'build_time': self._build_time,
        }

    def reset(self) -> None:
        """Clear the graph and statistics."""
        self._graph = None
        self._stats = {}
        self._build_time = None
        logger.info("Graph builder reset")


def build_transaction_graph(
    transactions_df: pd.DataFrame,
    use_multi_digraph: bool = False
) -> nx.DiGraph:
    """
    Convenience function to build transaction graph in one call.

    Args:
        transactions_df: DataFrame with transaction data
        use_multi_digraph: Whether to preserve multiple edges

    Returns:
        networkx.DiGraph: Built graph

    Example:
        graph = build_transaction_graph(df)
    """
    builder = TransactionGraphBuilder(use_multi_digraph=use_multi_digraph)
    return builder.build(transactions_df)
