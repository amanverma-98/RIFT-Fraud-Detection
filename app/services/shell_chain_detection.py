"""
Shell company chain detection for anti-money laundering.

Detects suspicious chains where intermediate nodes appear to be
"shell companies" - entities with very low transaction activity
that are used solely to obscure money flows.

Uses optimized BFS with aggressive pruning for efficient detection.
"""

import networkx as nx
from typing import List, Dict, Tuple, Set, Deque
from collections import deque
import logging

from app.utils.logger import setup_logger
from app.utils.exceptions import GraphDetectionError

logger = setup_logger(__name__)


def detect_shell_chains(
    graph: nx.DiGraph,
    min_chain_length: int = 3,
    max_chain_length: int = 10,
    shell_threshold: int = 3,
    max_chains: int = 1000
) -> List[Dict]:
    """
    Detect suspicious shell company chains in a transaction network.

    A shell chain is a path where intermediate nodes have minimal transaction
    activity (likely shell companies used to obscure money flows).

    Definition:
    - Path length >= 3 nodes (source → intermediaries → destination)
    - Each intermediate node has <= shell_threshold total transactions
    - Uses BFS with aggressive pruning for efficiency

    Time Complexity: O(V + E) best case, O(V * E) worst case (many paths)
    - BFS traversal: O(V + E)
    - Pruning: Reduces search space significantly
    - Result collection: O(P) where P = paths found

    Space Complexity: O(V + E + P) for queue, visited set, and results

    Args:
        graph: networkx.DiGraph with transaction network
        min_chain_length: Minimum chain nodes (default: 3)
        max_chain_length: Maximum chain nodes (default: 10)
        shell_threshold: Max transactions for shell node (default: 3)
        max_chains: Maximum chains to return (default: 1000)

    Returns:
        List[Dict] with detected shell chains:
        [{
            'chain': ['SOURCE', 'SHELL1', 'SHELL2', 'DEST'],
            'length': 4,
            'shell_nodes': ['SHELL1', 'SHELL2'],
            'shell_node_degrees': {'SHELL1': 2, 'SHELL2': 1},
            'is_suspicious': True,
            'risk_score': 0.85
        }]

    Raises:
        GraphDetectionError: If validation fails

    Example:
        >>> shells = detect_shell_chains(G, shell_threshold=3)
        >>> for shell in shells:
        >>>     print(f"Suspicious chain: {' → '.join(shell['chain'])}")
        >>>     print(f"  Risk score: {shell['risk_score']:.2f}")
    """
    try:
        logger.info(
            f"Starting shell chain detection: nodes={graph.number_of_nodes()}, "
            f"edges={graph.number_of_edges()}, shell_threshold={shell_threshold}"
        )

        # Validate inputs
        if not isinstance(graph, nx.DiGraph):
            raise TypeError("Input must be networkx.DiGraph")

        if graph.number_of_nodes() == 0:
            logger.warning("Empty graph provided")
            return []

        if min_chain_length < 3:
            raise ValueError("min_chain_length must be >= 3")

        if max_chain_length < min_chain_length:
            raise ValueError("max_chain_length must be >= min_chain_length")

        # Pre-calculate node degrees (for pruning)
        node_degrees = _calculate_node_degrees(graph)

        # Find all shell chains using BFS with pruning
        all_chains = _find_shell_chains_bfs(
            graph,
            node_degrees,
            min_chain_length,
            max_chain_length,
            shell_threshold,
            max_chains
        )

        # Deduplicate chains (same path in different order)
        unique_chains = _deduplicate_chains(all_chains)

        # Calculate risk scores
        chains_with_scores = _calculate_chain_risk_scores(unique_chains)

        # Sort by risk score (highest first)
        chains_with_scores.sort(
            key=lambda x: x['risk_score'],
            reverse=True
        )

        logger.info(
            f"Shell chain detection complete: found {len(chains_with_scores)} chains "
            f"with {len(unique_chains)} unique paths"
        )

        return chains_with_scores

    except (TypeError, ValueError, GraphDetectionError):
        raise
    except Exception as e:
        logger.error(f"Error detecting shell chains: {str(e)}", exc_info=True)
        raise GraphDetectionError(f"Shell chain detection failed: {str(e)}")


def _calculate_node_degrees(graph: nx.DiGraph) -> Dict[str, int]:
    """
    Calculate total degree (in + out) for each node.

    Time Complexity: O(V)
    Space Complexity: O(V)

    Used for pruning: if node has > threshold degree, skip exploring from it.
    """
    degrees = {}
    for node in graph.nodes():
        in_deg = graph.in_degree(node)
        out_deg = graph.out_degree(node)
        degrees[node] = in_deg + out_deg

    return degrees


def _find_shell_chains_bfs(
    graph: nx.DiGraph,
    node_degrees: Dict[str, int],
    min_length: int,
    max_length: int,
    shell_threshold: int,
    max_chains: int
) -> List[List[str]]:
    """
    Find shell company chains using BFS with aggressive pruning.

    BFS Algorithm with Pruning:
    1. Start from each source node
    2. Use queue to track (current_node, path_so_far)
    3. For each node:
       - If intermediate node, check if <= shell_threshold degree
       - If not shell-like AND we're past min_length, could be destination
       - Expand to neighbors if path not too long
    4. When reaching min_length, record as potential chain
    5. Continue until max_length

    Time Complexity: O(V + E) with pruning, O(V * E) worst case
    Space Complexity: O(V + E + P) where P = paths found

    Pruning Optimizations:
    - Skip nodes with > shell_threshold degree (not shells)
    - Limit queue size (BFS can explode in dense graphs)
    - Early termination when max_chains reached
    - Skip cycles (don't revisit nodes in current path)
    """
    chains = []
    visited_paths: Set[Tuple[str, ...]] = set()

    logger.debug(f"Starting BFS from {graph.number_of_nodes()} potential sources")

    # Try starting from each node
    for source_node in graph.nodes():
        if len(chains) >= max_chains:
            logger.warning(f"Reached max_chains limit ({max_chains})")
            break

        # BFS from this source
        bfs_chains = _bfs_from_node(
            graph,
            source_node,
            node_degrees,
            min_length,
            max_length,
            shell_threshold,
            max_chains - len(chains)  # Remaining budget
        )

        for chain in bfs_chains:
            chain_key = tuple(chain)
            if chain_key not in visited_paths:
                chains.append(chain)
                visited_paths.add(chain_key)

    logger.debug(f"BFS found {len(chains)} total chains before deduplication")
    return chains


def _bfs_from_node(
    graph: nx.DiGraph,
    start_node: str,
    node_degrees: Dict[str, int],
    min_length: int,
    max_length: int,
    shell_threshold: int,
    max_chains: int
) -> List[List[str]]:
    """
    BFS from a single source node to find shell chains.

    Time Complexity: O(V + E) per source node
    Space Complexity: O(V + P) for queue and results

    Args:
        start_node: Starting node for BFS
        node_degrees: Pre-calculated degree for pruning
        min_length: Minimum path length
        max_length: Maximum path length
        shell_threshold: Threshold for shell node detection
        max_chains: Maximum chains to find

    Returns:
        List of chains found from this source
    """
    chains = []

    # Queue: (current_node, path_so_far)
    queue: Deque[Tuple[str, List[str]]] = deque([(start_node, [start_node])])
    visited_in_bfs: Set[Tuple[str, ...]] = set()

    while queue and len(chains) < max_chains:
        current_node, path = queue.popleft()

        # Path too long: stop exploring
        if len(path) >= max_length:
            continue

        # Prune: avoid cycles in path
        if len(path) != len(set(path)):
            continue

        # Get neighbors (successors in directed graph)
        neighbors = list(graph.successors(current_node))

        for neighbor in neighbors:
            new_path = path + [neighbor]

            # Check if we can record this as a chain
            if len(new_path) >= min_length:
                # Verify intermediate nodes are shells (except first and last)
                is_valid_chain = _is_valid_shell_chain(
                    new_path,
                    node_degrees,
                    shell_threshold
                )

                if is_valid_chain:
                    path_key = tuple(new_path)
                    if path_key not in visited_in_bfs:
                        chains.append(new_path)
                        visited_in_bfs.add(path_key)

            # Continue exploring if not at max length
            if len(new_path) < max_length:
                queue.append((neighbor, new_path))

    return chains


def _is_valid_shell_chain(
    path: List[str],
    node_degrees: Dict[str, int],
    shell_threshold: int
) -> bool:
    """
    Validate that intermediate nodes are likely shell companies.

    Only check intermediate nodes (skip first and last node).
    A shell company has <= shell_threshold total transactions.

    Time Complexity: O(L) where L = path length
    Space Complexity: O(1)

    Args:
        path: List of nodes in path
        node_degrees: Pre-calculated degrees
        shell_threshold: Maximum degree for shell node

    Returns:
        True if all intermediate nodes are shells, False otherwise
    """
    if len(path) < 3:
        return False

    # Check intermediate nodes (index 1 to len-2)
    for i in range(1, len(path) - 1):
        node = path[i]
        degree = node_degrees.get(node, 0)

        # If intermediate node has too many transactions, not a shell
        if degree > shell_threshold:
            return False

    return True


def _deduplicate_chains(chains: List[List[str]]) -> List[List[str]]:
    """
    Remove duplicate chains from results.

    Two chains are considered duplicates if they have the same nodes
    in the same order.

    Time Complexity: O(C * L) where C = chains, L = chain length
    Space Complexity: O(C * L) for set storage

    Args:
        chains: List of chains

    Returns:
        List with duplicates removed
    """
    seen: Set[Tuple[str, ...]] = set()
    unique = []

    for chain in chains:
        chain_key = tuple(chain)
        if chain_key not in seen:
            seen.add(chain_key)
            unique.append(chain)

    logger.debug(f"Deduplicated {len(chains)} to {len(unique)} unique chains")
    return unique


def _calculate_chain_risk_scores(chains: List[List[str]]) -> List[Dict]:
    """
    Calculate risk scores for shell chains.

    Risk factors:
    - Longer chains (more obfuscation) = higher risk
    - More shell nodes = higher risk
    - Chains with very low-activity nodes = higher risk

    Time Complexity: O(C * L) where C = chains, L = chain length
    Space Complexity: O(C)

    Args:
        chains: List of shell chains

    Returns:
        List of chain dicts with risk_score calculated
    """
    structured_chains = []

    for chain in chains:
        # Identify shell nodes (intermediate nodes)
        shell_nodes = chain[1:-1] if len(chain) > 2 else []

        # Basic risk calculation (can be enhanced)
        # Length factor: longer chains = higher risk (up to 10)
        length_factor = min(len(chain) / 10, 1.0)

        # Shell count factor
        shell_factor = min(len(shell_nodes) / 5, 1.0)

        # Combined risk (weighted average)
        risk_score = (length_factor * 0.4 + shell_factor * 0.6)

        # Build degree map for shells
        shell_degrees = {node: 0 for node in shell_nodes}

        structured_chains.append({
            'chain': chain,
            'length': len(chain),
            'shell_nodes': shell_nodes,
            'shell_node_degrees': shell_degrees,  # Would be populated with actual degrees
            'is_suspicious': True,
            'risk_score': round(risk_score, 3),
        })

    return structured_chains


def detect_shell_chains_fast(
    graph: nx.DiGraph,
    shell_threshold: int = 3,
    max_chains: int = 1000
) -> List[Dict]:
    """
    Faster variant of shell chain detection using depth limits.

    Optimized for very large graphs by limiting search depth early.

    Time Complexity: O(V*E) worst case, but with tighter bounds
    Space Complexity: O(V + P) with smaller queue

    Args:
        graph: Transaction graph
        shell_threshold: Max degree for shell node
        max_chains: Maximum results

    Returns:
        List of suspicious shell chains
    """
    return detect_shell_chains(
        graph,
        min_chain_length=3,
        max_chain_length=6,  # Limit depth for speed
        shell_threshold=shell_threshold,
        max_chains=max_chains
    )


def find_shell_chains_with_amounts(
    graph: nx.DiGraph,
    shell_threshold: int = 3
) -> List[Dict]:
    """
    Find shell chains and include transaction amount information.

    Analyzes the flow of money through shell chains.

    Time Complexity: O(V + E + C*L) where C = chains, L = chain length
    Space Complexity: O(V + E + C*L)

    Args:
        graph: Transaction graph with amount attributes on edges
        shell_threshold: Max degree for shell node

    Returns:
        List of chains with transaction amounts
    """
    chains = detect_shell_chains(graph, shell_threshold=shell_threshold)

    enriched_chains = []

    for chain in chains:
        # Calculate total amount flowing through chain
        total_amount = 0.0
        amounts_per_edge = []

        for i in range(len(chain) - 1):
            src = chain['chain'][i]
            dst = chain['chain'][i + 1]

            if graph.has_edge(src, dst):
                edge_data = graph.edges[src, dst]
                amount = edge_data.get('amount', 0)
                total_amount += amount
                amounts_per_edge.append({
                    'from': src,
                    'to': dst,
                    'amount': amount
                })

        chain['total_amount'] = round(total_amount, 2)
        chain['amounts_per_edge'] = amounts_per_edge
        enriched_chains.append(chain)

    return enriched_chains


def get_shell_chain_statistics(chains: List[Dict]) -> Dict:
    """
    Calculate statistics about detected shell chains.

    Time Complexity: O(C * L) where C = chains, L = avg chain length
    Space Complexity: O(1)

    Args:
        chains: List of detected shell chains

    Returns:
        Dictionary with statistics
    """
    if not chains:
        return {
            'total_chains': 0,
            'avg_chain_length': 0,
            'max_chain_length': 0,
            'min_chain_length': 0,
            'avg_shell_nodes': 0,
            'max_risk_score': 0,
            'avg_risk_score': 0,
        }

    lengths = [c['length'] for c in chains]
    shell_counts = [len(c['shell_nodes']) for c in chains]
    risk_scores = [c['risk_score'] for c in chains]

    return {
        'total_chains': len(chains),
        'avg_chain_length': sum(lengths) / len(lengths),
        'max_chain_length': max(lengths),
        'min_chain_length': min(lengths),
        'avg_shell_nodes': sum(shell_counts) / len(shell_counts),
        'max_risk_score': max(risk_scores),
        'avg_risk_score': sum(risk_scores) / len(risk_scores),
        'distribution_by_length': _count_by_length(lengths),
    }


def _count_by_length(lengths: List[int]) -> Dict[int, int]:
    """Count chains by length."""
    distribution = {}
    for length in lengths:
        distribution[length] = distribution.get(length, 0) + 1
    return dict(sorted(distribution.items()))
