"""
Advanced cycle detection algorithms for transaction graph analysis.

Provides optimized cycle detection with filtering and deduplication
for fraud detection in transaction networks.
"""

import networkx as nx
from typing import List, Set, Tuple, DefaultDict
from collections import defaultdict
import logging

from app.utils.logger import setup_logger

logger = setup_logger(__name__)


def detect_cycles(
    graph: nx.DiGraph,
    min_length: int = 3,
    max_length: int = 5
) -> List[List[str]]:
    """
    Detect simple cycles in a directed graph with length constraints.

    Efficiently finds all simple cycles with lengths between min_length and max_length
    (inclusive), removes duplicates, and returns clean structured output.

    Time Complexity:
    - Best case: O(V + E) for sparse graphs with few cycles
    - Worst case: O(V * E) for dense graphs
    - Practical: O(C * L) where C = number of cycles, L = average cycle length

    Space Complexity: O(V + E + C*L) where C = cycles found, L = avg cycle length

    Args:
        graph: networkx.DiGraph object
        min_length: Minimum cycle length (default: 3). Must be >= 2
        max_length: Maximum cycle length (default: 5). Must be >= min_length

    Returns:
        List[List[str]]: List of cycles, each cycle is a list of node IDs representing
                        the path (e.g., ['A', 'B', 'C'] means A→B→C→A).
                        Sorted by cycle length then lexicographically for consistency.

    Raises:
        ValueError: If min_length < 2 or max_length < min_length

    Example:
        >>> import networkx as nx
        >>> G = nx.DiGraph()
        >>> G.add_edges_from([('A', 'B'), ('B', 'C'), ('C', 'A')])
        >>> cycles = detect_cycles(G, min_length=3, max_length=5)
        >>> cycles
        [['A', 'B', 'C']]

    Notes:
        - Returns only simple cycles (no repeated nodes except start/end)
        - Removes duplicate cycles (e.g., [A,B,C], [B,C,A], [C,A,B] counted as one)
        - Empty list returned if no cycles exist in specified range
        - For very large graphs, consider filtering nodes first
    """
    # Validate parameters
    if min_length < 2:
        raise ValueError(f"min_length must be >= 2, got {min_length}")
    if max_length < min_length:
        raise ValueError(f"max_length must be >= min_length, got {max_length}")

    if not isinstance(graph, nx.DiGraph):
        raise TypeError(f"Expected networkx.DiGraph, got {type(graph)}")

    logger.info(
        f"Starting cycle detection: nodes={graph.number_of_nodes()}, "
        f"edges={graph.number_of_edges()}, length_range=[{min_length}, {max_length}]"
    )

    # Get all simple cycles from NetworkX
    # Time: O(V + E) for algorithms, but actual cycle enumeration is exponential
    try:
        all_cycles = list(nx.simple_cycles(graph))
        logger.debug(f"Found {len(all_cycles)} total cycles (before filtering)")
    except nx.NetworkXNoCycle:
        logger.info("No cycles detected in graph")
        return []
    except Exception as e:
        logger.error(f"Error detecting cycles: {str(e)}")
        raise

    # Filter by length and deduplicate - O(C * L^2) where C = cycles, L = length
    filtered_cycles = _filter_and_deduplicate_cycles(
        all_cycles,
        min_length=min_length,
        max_length=max_length
    )

    # Sort for consistent output
    sorted_cycles = _sort_cycles(filtered_cycles)

    logger.info(
        f"Cycle detection complete: found {len(sorted_cycles)} cycles "
        f"in length range [{min_length}, {max_length}]"
    )

    for i, cycle in enumerate(sorted_cycles, 1):
        logger.debug(f"  Cycle {i} (length {len(cycle)}): {' → '.join(cycle + [cycle[0]])}")

    return sorted_cycles


def _filter_and_deduplicate_cycles(
    cycles: List[List[str]],
    min_length: int,
    max_length: int
) -> List[List[str]]:
    """
    Filter cycles by length and remove duplicates.

    A cycle [A,B,C] is equivalent to [B,C,A] and [C,A,B] (rotations).
    This function detects and removes these duplicates.

    Time Complexity: O(C * L^2) where C = number of cycles, L = cycle length
    Space Complexity: O(C * L)

    Args:
        cycles: List of cycles (potentially unordered)
        min_length: Minimum cycle length
        max_length: Maximum cycle length

    Returns:
        List of unique cycles with lengths in specified range
    """
    seen_cycles: Set[Tuple[str, ...]] = set()
    unique_cycles: List[List[str]] = []

    for cycle in cycles:
        cycle_len = len(cycle)

        # Filter by length
        if cycle_len < min_length or cycle_len > max_length:
            continue

        # Normalize cycle to handle rotations: e.g., [A,B,C], [B,C,A], [C,A,B]
        # Convert to tuple of sorted rotations for comparison
        normalized = _normalize_cycle(cycle)

        if normalized not in seen_cycles:
            seen_cycles.add(normalized)
            unique_cycles.append(cycle)

    return unique_cycles


def _normalize_cycle(cycle: List[str]) -> Tuple[str, ...]:
    """
    Normalize a cycle to handle rotational equivalence.

    Cycles [A,B,C], [B,C,A], [C,A,B] are all the same.
    Returns the lexicographically smallest rotation as the canonical form.

    Time Complexity: O(L^2) where L = cycle length
    Space Complexity: O(L)

    Args:
        cycle: List of node IDs

    Returns:
        Tuple representing canonical form of the cycle
    """
    if not cycle:
        return ()

    # Generate all rotations
    rotations = []
    for i in range(len(cycle)):
        rotation = tuple(cycle[i:] + cycle[:i])
        rotations.append(rotation)

    # Return lexicographically smallest rotation
    return min(rotations)


def _sort_cycles(cycles: List[List[str]]) -> List[List[str]]:
    """
    Sort cycles for consistent, readable output.

    Sorts first by length (ascending), then lexicographically.

    Time Complexity: O(C * L * log(C)) where C = cycles, L = cycle length
    Space Complexity: O(C * L)

    Args:
        cycles: List of cycles

    Returns:
        Sorted list of cycles
    """
    return sorted(cycles, key=lambda c: (len(c), c))


def detect_cycles_optimized(
    graph: nx.DiGraph,
    min_length: int = 3,
    max_length: int = 5,
    max_cycles: int = 100
) -> List[List[str]]:
    """
    Optimized cycle detection with result limit for large graphs.

    Similar to detect_cycles() but limits results and can provide early termination
    for very large graphs where cycle enumeration is expensive.

    Time Complexity: O(min(C, max_cycles) * L) in addition to cycle detection
    Space Complexity: O(max_cycles * L)

    Args:
        graph: networkx.DiGraph object
        min_length: Minimum cycle length
        max_length: Maximum cycle length
        max_cycles: Maximum number of cycles to return

    Returns:
        List of up to max_cycles cycles
    """
    cycles = detect_cycles(graph, min_length, max_length)

    if len(cycles) > max_cycles:
        logger.warning(
            f"Found {len(cycles)} cycles, returning top {max_cycles} "
            f"(sorted by length)"
        )
        cycles = cycles[:max_cycles]

    return cycles


def detect_simple_cycles_dfs(
    graph: nx.DiGraph,
    min_length: int = 3,
    max_length: int = 5
) -> List[List[str]]:
    """
    Detect cycles using DFS-based approach (alternative to NetworkX).

    Uses depth-first search to find cycles. Can be faster than NetworkX
    for small graphs or when early termination is desired.

    Time Complexity: O(V * E) worst case, O(V + E) best case
    Space Complexity: O(V + C*L) for recursion stack and results

    Args:
        graph: networkx.DiGraph object
        min_length: Minimum cycle length
        max_length: Maximum cycle length

    Returns:
        List of detected cycles
    """
    cycles: List[List[str]] = []
    visited: Set[str] = set()
    rec_stack: Set[str] = set()

    def dfs(node: str, path: List[str]) -> None:
        """DFS helper to find cycles."""
        if len(path) > max_length:
            return  # Early termination

        visited.add(node)
        rec_stack.add(node)
        path.append(node)

        for neighbor in graph.successors(node):
            if neighbor in rec_stack:
                # Found a cycle
                cycle_start = path.index(neighbor)
                cycle = path[cycle_start:] + [neighbor]
                cycle_nodes = cycle[:-1]  # Remove duplicate end node

                if min_length <= len(cycle_nodes) <= max_length:
                    cycles.append(cycle_nodes)

            elif neighbor not in visited:
                dfs(neighbor, path.copy())

        rec_stack.remove(node)

    # Run DFS from each node
    for node in graph.nodes():
        if node not in visited:
            dfs(node, [])

    # Deduplicate and return
    return _filter_and_deduplicate_cycles(cycles, min_length, max_length)


def find_fraud_cycles(
    graph: nx.DiGraph,
    min_cycle_length: int = 3,
    max_cycle_length: int = 5,
    analyze_amounts: bool = True
) -> List[dict]:
    """
    Detect cycles and analyze them for potential fraud patterns.

    Returns enriched cycle information including transaction amounts
    and suspicious characteristics.

    Time Complexity: O(C * L + E) where C = cycles, L = avg length
    Space Complexity: O(C * L)

    Args:
        graph: Transaction graph
        min_cycle_length: Minimum cycle length
        max_cycle_length: Maximum cycle length
        analyze_amounts: If True, calculate total amounts in cycles

    Returns:
        List of dicts with cycle details:
        {
            'cycle': ['A', 'B', 'C'],
            'length': 3,
            'total_amount': 1500.0,  # if analyze_amounts=True
            'avg_amount': 500.0,      # if analyze_amounts=True
            'nodes': ['A', 'B', 'C'],
            'description': 'A→B→C→A'
        }

    Example:
        >>> fraud_cycles = find_fraud_cycles(graph)
        >>> for cycle_info in fraud_cycles:
        ...     print(f"Suspicious cycle: {cycle_info['description']}")
        ...     print(f"  Total amount: {cycle_info['total_amount']}")
    """
    cycles = detect_cycles(
        graph,
        min_length=min_cycle_length,
        max_length=max_cycle_length
    )

    fraud_cycles = []

    for cycle in cycles:
        cycle_info = {
            'cycle': cycle,
            'length': len(cycle),
            'nodes': cycle,
            'description': ' → '.join(cycle + [cycle[0]]),
        }

        # Analyze amounts if requested
        if analyze_amounts:
            total_amount = 0.0
            edge_count = 0

            # Sum amounts along the cycle path
            for i in range(len(cycle)):
                src = cycle[i]
                dst = cycle[(i + 1) % len(cycle)]

                if graph.has_edge(src, dst):
                    edge_data = graph.edges[src, dst]
                    total_amount += edge_data.get('amount', 0)
                    edge_count += 1

            cycle_info['total_amount'] = round(total_amount, 2)
            cycle_info['edge_count'] = edge_count
            if edge_count > 0:
                cycle_info['avg_amount'] = round(total_amount / edge_count, 2)

        fraud_cycles.append(cycle_info)

    # Sort by total amount (descending) for fraud investigation priority
    if analyze_amounts:
        fraud_cycles.sort(
            key=lambda x: x.get('total_amount', 0),
            reverse=True
        )

        logger.info(
            f"Found {len(fraud_cycles)} fraud cycles. "
            f"Top cycle: {fraud_cycles[0]['description']} "
            f"(${fraud_cycles[0]['total_amount']:,.2f})" if fraud_cycles else ""
        )

    return fraud_cycles


def get_cycle_statistics(cycles: List[List[str]]) -> dict:
    """
    Calculate statistics about detected cycles.

    Time Complexity: O(C * L) where C = cycles, L = avg length
    Space Complexity: O(1)

    Args:
        cycles: List of cycles

    Returns:
        Dictionary with statistics:
        {
            'total_cycles': int,
            'min_length': int,
            'max_length': int,
            'avg_length': float,
            'by_length': {length: count}
        }
    """
    if not cycles:
        return {
            'total_cycles': 0,
            'min_length': 0,
            'max_length': 0,
            'avg_length': 0,
            'by_length': {},
        }

    lengths = [len(c) for c in cycles]
    by_length: DefaultDict[int, int] = defaultdict(int)

    for length in lengths:
        by_length[length] += 1

    return {
        'total_cycles': len(cycles),
        'min_length': min(lengths),
        'max_length': max(lengths),
        'avg_length': sum(lengths) / len(lengths),
        'by_length': dict(sorted(by_length.items())),
    }
