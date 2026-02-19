"""
Compliance Reporting System for Fraud Detection.

Generates structured compliance reports with suspicious accounts,
detected fraud rings, and summary statistics. All output is
deterministically formatted and JSON serializable.

Time Complexity: O(V + E + P log P) where V=accounts, E=edges, P=patterns
Space Complexity: O(V + E + R) where R=fraud rings detected
"""

import networkx as nx
import pandas as pd
from typing import List, Dict, Set, Tuple, Any
from datetime import datetime
from collections import defaultdict
import json
import logging

from app.utils.logger import setup_logger
from app.utils.exceptions import GraphDetectionError
from app.services import (
    calculate_suspicion_scores,
    get_suspicion_score_summary,
)

logger = setup_logger(__name__)


def generate_report(
    graph: nx.DiGraph,
    transactions_df: pd.DataFrame,
    suspicion_scores: List[Dict] = None,
    min_ring_size: int = 2,
    max_ring_size: int = 50,
    ring_score_threshold: int = 30,
    suspicious_account_threshold: int = 30
) -> Dict[str, Any]:
    """
    Generate a comprehensive compliance report with suspicious accounts
    and detected fraud rings.

    Aggregates suspicion scores and performs community detection to identify
    fraud rings (clusters of interconnected accounts with coordinated fraud patterns).

    Time Complexity: O(V + E + P log P) for sorting and community detection
      - Suspicion scoring: O(V + E + N log N)
      - Fraud ring detection: O(V + E) community detection
      - Sorting: O(P log P) where P = patterns
      - Report assembly: O(P + R*L) where R = rings, L = avg ring size

    Space Complexity: O(V + E + P + R*L)
      - Graph: O(V + E)
      - Suspicion scores: O(V)
      - Fraud rings: O(R*L)
      - Report: O(V + E + P + R*L)

    Args:
        graph: networkx.DiGraph with transaction network
        transactions_df: DataFrame with columns: sender_id, receiver_id, timestamp, amount
        suspicion_scores: Pre-calculated scores (optional, will calculate if None)
        min_ring_size: Minimum accounts in fraud ring (default: 2)
        max_ring_size: Maximum accounts in fraud ring (default: 50)
        ring_score_threshold: Minimum average score for ring (default: 30)
        suspicious_account_threshold: Minimum score to flag account (default: 30)

    Returns:
        Dict with schema:
        {
            'suspicious_accounts': [
                {
                    'account_id': str,
                    'suspicion_score': int,           # [0, 100]
                    'raw_score': int,                # [0, 130]
                    'triggered_patterns': [str],
                    'pattern_breakdown': {str: bool},
                    'score_breakdown': {str: int},
                    'transaction_count': int,
                    'involved_in_ring': bool,
                    'ring_id': int or None
                },
                ...
            ],
            'fraud_rings': [
                {
                    'ring_id': int,
                    'ring_size': int,
                    'member_count': int,
                    'account_ids': [str],
                    'avg_suspicion_score': float,
                    'max_suspicion_score': int,
                    'min_suspicion_score': int,
                    'total_transaction_amount': float,
                    'common_patterns': [str],
                    'descriptions': str
                },
                ...
            ],
            'summary': {
                'report_generated': str,              # ISO 8601 timestamp
                'total_accounts_analyzed': int,
                'total_accounts_flagged': int,
                'total_fraud_rings': int,
                'high_risk_accounts': int,           # score >= 80
                'medium_risk_accounts': int,         # 50-79
                'low_risk_accounts': int,            # 30-49
                'total_transaction_volume': float,
                'avg_flagged_account_score': float,
                'most_common_pattern': str,
                'pattern_distribution': {str: int}
            }
        }

    Raises:
        GraphDetectionError: If validation fails
        TypeError: If input types invalid
        ValueError: If parameters invalid

    Example:
        >>> report = generate_report(graph, transactions_df)
        >>> print(f"Flagged accounts: {report['summary']['total_accounts_flagged']}")
        >>> print(f"Fraud rings detected: {report['summary']['total_fraud_rings']}")
        >>> for ring in report['fraud_rings'][:3]:
        ...     print(f"Ring {ring['ring_id']}: {ring['member_count']} accounts")
    """
    try:
        logger.info(
            f"Starting compliance report generation: nodes={graph.number_of_nodes()}, "
            f"edges={graph.number_of_edges()}, transactions={len(transactions_df)}"
        )

        # Validate inputs
        _validate_report_inputs(graph, transactions_df)

        # Calculate suspicion scores if not provided
        if suspicion_scores is None:
            logger.debug("Calculating suspicion scores...")
            suspicion_scores = calculate_suspicion_scores(graph, transactions_df)

        # Filter suspicious accounts
        suspicious_accounts = [
            s for s in suspicion_scores
            if s['suspicion_score'] >= suspicious_account_threshold
        ]
        logger.info(f"Identified {len(suspicious_accounts)} suspicious accounts")

        # Enrich with transaction counts
        suspicious_accounts = _enrich_with_transaction_counts(
            suspicious_accounts, transactions_df
        )

        # Detect fraud rings
        logger.debug("Detecting fraud rings...")
        fraud_rings, account_ring_map = _detect_fraud_rings(
            graph,
            suspicious_accounts,
            min_ring_size,
            max_ring_size,
            ring_score_threshold
        )
        logger.info(f"Detected {len(fraud_rings)} fraud rings")

        # Add ring membership to accounts
        for account in suspicious_accounts:
            account_id = account['account_id']
            if account_id in account_ring_map:
                account['involved_in_ring'] = True
                account['ring_id'] = account_ring_map[account_id]
            else:
                account['involved_in_ring'] = False
                account['ring_id'] = None

        # Sort by suspicion score (descending) - deterministic
        suspicious_accounts.sort(
            key=lambda x: (
                -x['suspicion_score'],  # Descending score
                x['account_id']          # Then ascending by ID for ties
            )
        )

        fraud_rings.sort(
            key=lambda x: (
                -x['avg_suspicion_score'],  # Descending average score
                -x['member_count'],          # Then descending by size
                x['ring_id']                  # Then by ring ID
            )
        )

        # Generate summary statistics
        summary = _generate_summary(
            graph,
            transactions_df,
            suspicious_accounts,
            fraud_rings,
            suspicion_scores
        )

        # Assemble report
        report = {
            'suspicious_accounts': suspicious_accounts,
            'fraud_rings': fraud_rings,
            'summary': summary,
        }

        # Validate JSON serializability
        json.dumps(report)  # Will raise if not serializable

        logger.info(
            f"Compliance report generated: {len(suspicious_accounts)} accounts, "
            f"{len(fraud_rings)} rings, timestamp={summary['report_generated']}"
        )

        return report

    except (TypeError, ValueError, GraphDetectionError):
        raise
    except Exception as e:
        logger.error(f"Error generating compliance report: {str(e)}", exc_info=True)
        raise GraphDetectionError(f"Report generation failed: {str(e)}")


def _validate_report_inputs(graph: nx.DiGraph, transactions_df: pd.DataFrame) -> None:
    """
    Validate inputs for report generation.

    Time Complexity: O(N) for column checking
    Space Complexity: O(1)
    """
    if not isinstance(graph, nx.DiGraph):
        raise TypeError("Graph must be networkx.DiGraph")

    if not isinstance(transactions_df, pd.DataFrame):
        raise TypeError("Transactions must be pandas DataFrame")

    if graph.number_of_nodes() == 0:
        raise ValueError("Graph is empty")

    if transactions_df.empty:
        raise ValueError("Transactions DataFrame is empty")

    required_cols = {'sender_id', 'receiver_id', 'timestamp'}
    missing = required_cols - set(transactions_df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    logger.debug("Input validation passed")


def _enrich_with_transaction_counts(
    suspicious_accounts: List[Dict],
    transactions_df: pd.DataFrame
) -> List[Dict]:
    """
    Add transaction count and volume to account dicts.

    Time Complexity: O(N) for iteration
    Space Complexity: O(V) for storing counts

    Args:
        suspicious_accounts: List of account score dicts
        transactions_df: Transaction DataFrame

    Returns:
        Enhanced account dicts with transaction counts
    """
    # Count transactions per account
    account_txn_counts = defaultdict(int)
    for _, row in transactions_df.iterrows():
        account_txn_counts[str(row['sender_id'])] += 1
        account_txn_counts[str(row['receiver_id'])] += 1

    # Add to accounts
    for account in suspicious_accounts:
        account['transaction_count'] = account_txn_counts.get(account['account_id'], 0)

    return suspicious_accounts


def _detect_fraud_rings(
    graph: nx.DiGraph,
    suspicious_accounts: List[Dict],
    min_size: int,
    max_size: int,
    score_threshold: int
) -> Tuple[List[Dict], Dict[str, int]]:
    """
    Detect fraud rings (clusters of interconnected suspicious accounts).

    Uses multiple strategies:
    1. Strongly connected components (accounts that can reach each other)
    2. Common pattern participation (accounts in same cycles/chains)
    3. Direct connectivity (accounts that transact with each other)

    Time Complexity: O(V + E) for SCC detection
    Space Complexity: O(V + R*L) where R=rings, L=avg size

    Args:
        graph: Transaction graph
        suspicious_accounts: List of flagged accounts
        min_size: Minimum ring size
        max_size: Maximum ring size
        score_threshold: Minimum average score for ring

    Returns:
        Tuple of (fraud_rings, account_ring_map)
        - fraud_rings: List of ring dictionaries
        - account_ring_map: Dict mapping account_id -> ring_id
    """
    suspicious_account_ids = {s['account_id'] for s in suspicious_accounts}
    account_scores = {s['account_id']: s for s in suspicious_accounts}

    # Create subgraph of suspicious accounts only
    suspicious_subgraph = graph.subgraph(suspicious_account_ids).copy()

    fraud_rings = []
    account_ring_map = {}
    ring_id = 0

    # Strategy 1: Strongly Connected Components (high connectivity)
    sccs = list(nx.strongly_connected_components(suspicious_subgraph))
    logger.debug(f"Found {len(sccs)} strongly connected components")

    for scc in sccs:
        if min_size <= len(scc) <= max_size:
            ring_data = _create_ring_data(
                ring_id,
                list(scc),
                account_scores,
                graph,
                suspicious_subgraph
            )

            if ring_data['avg_suspicion_score'] >= score_threshold:
                fraud_rings.append(ring_data)
                for account_id in scc:
                    account_ring_map[account_id] = ring_id
                ring_id += 1

    # Strategy 2: Find additional rings via common pattern participation
    if len(fraud_rings) < 100:  # Reasonable limit
        additional_rings = _find_pattern_based_rings(
            suspicious_accounts,
            min_size,
            max_size,
            score_threshold,
            account_ring_map,
            ring_id
        )

        for ring_data in additional_rings:
            # Check for overlap with existing rings
            account_ids = set(ring_data['account_ids'])
            already_mapped = {
                aid for aid in account_ids if aid in account_ring_map
            }

            if len(already_mapped) < 0.5 * len(account_ids):  # < 50% overlap
                fraud_rings.append(ring_data)
                for account_id in account_ids:
                    if account_id not in account_ring_map:
                        account_ring_map[account_id] = ring_data['ring_id']
                ring_id += 1

    logger.debug(f"Detected {len(fraud_rings)} fraud rings total")
    return fraud_rings, account_ring_map


def _create_ring_data(
    ring_id: int,
    account_ids: List[str],
    account_scores: Dict[str, Dict],
    full_graph: nx.DiGraph,
    ring_subgraph: nx.DiGraph
) -> Dict[str, Any]:
    """
    Create structured ring data for a group of accounts.

    Time Complexity: O(L + E_ring) where L = list size, E_ring = edges in ring
    Space Complexity: O(L)

    Args:
        ring_id: Ring identifier
        account_ids: List of accounts in ring
        account_scores: Mapping of account_id -> score dict
        full_graph: Complete transaction graph
        ring_subgraph: Subgraph containing only ring accounts

    Returns:
        Dictionary with ring information
    """
    # Get scores for accounts
    ring_scores = [
        account_scores[aid]['suspicion_score']
        for aid in account_ids
        if aid in account_scores
    ]

    # Calculate statistics
    avg_score = sum(ring_scores) / len(ring_scores) if ring_scores else 0
    max_score = max(ring_scores) if ring_scores else 0
    min_score = min(ring_scores) if ring_scores else 0

    # Calculate transaction volume
    total_amount = 0.0
    for u, v in ring_subgraph.edges():
        if full_graph.has_edge(u, v):
            edge_data = full_graph.edges[u, v]
            total_amount += edge_data.get('amount', 0)

    # Find common patterns
    common_patterns = _find_common_patterns(account_ids, account_scores)

    # Generate description
    description = _generate_ring_description(
        ring_id,
        account_ids,
        common_patterns,
        avg_score
    )

    return {
        'ring_id': ring_id,
        'ring_size': len(account_ids),
        'member_count': len(account_ids),
        'account_ids': sorted(account_ids),
        'avg_suspicion_score': round(avg_score, 2),
        'max_suspicion_score': int(max_score),
        'min_suspicion_score': int(min_score),
        'total_transaction_amount': round(total_amount, 2),
        'common_patterns': sorted(common_patterns),
        'descriptions': description,
    }


def _find_pattern_based_rings(
    suspicious_accounts: List[Dict],
    min_size: int,
    max_size: int,
    score_threshold: int,
    already_mapped: Dict[str, int],
    start_ring_id: int
) -> List[Dict]:
    """
    Find fraud rings based on shared fraud patterns.

    Accounts are grouped if they share the same patterns and have
    compatible suspicion profiles.

    Time Complexity: O(V^2) worst case for pattern matching
    Space Complexity: O(V * P) where P = patterns per account

    Args:
        suspicious_accounts: List of flagged accounts
        min_size: Minimum ring size
        max_size: Maximum ring size
        score_threshold: Minimum average score
        already_mapped: Accounts already in rings
        start_ring_id: Starting ring ID number

    Returns:
        List of additional ring dictionaries
    """
    rings = []
    ring_id = start_ring_id

    # Group by similar pattern combinations
    pattern_groups = defaultdict(list)

    for account in suspicious_accounts:
        if account['account_id'] in already_mapped:
            continue

        # Create pattern signature (sorted tuple of patterns)
        pattern_sig = tuple(sorted(account['triggered_patterns']))
        pattern_groups[pattern_sig].append(account['account_id'])

    # Create rings from pattern groups
    for pattern_sig, account_ids in pattern_groups.items():
        if min_size <= len(account_ids) <= max_size and len(pattern_sig) > 0:
            # Calculate average score
            scores = [
                account_scores['suspicion_score']
                for account in suspicious_accounts
                if account['account_id'] in account_ids
                for account_scores in [account]
            ]

            avg_score = sum(scores) / len(scores) if scores else 0

            if avg_score >= score_threshold:
                ring = {
                    'ring_id': ring_id,
                    'ring_size': len(account_ids),
                    'member_count': len(account_ids),
                    'account_ids': sorted(account_ids),
                    'avg_suspicion_score': round(avg_score, 2),
                    'max_suspicion_score': max(scores) if scores else 0,
                    'min_suspicion_score': min(scores) if scores else 0,
                    'total_transaction_amount': 0.0,
                    'common_patterns': list(pattern_sig),
                    'descriptions': f"Pattern-based ring: {', '.join(pattern_sig)}",
                }
                rings.append(ring)
                ring_id += 1

    return rings


def _find_common_patterns(
    account_ids: List[str],
    account_scores: Dict[str, Dict]
) -> Set[str]:
    """
    Find patterns common to all or most accounts in group.

    Time Complexity: O(L * P) where L = accounts, P = patterns per account
    Space Complexity: O(P)

    Args:
        account_ids: Accounts in ring
        account_scores: Mapping of account_id -> score dict

    Returns:
        Set of common pattern names
    """
    if not account_ids:
        return set()

    # Find patterns present in each account
    pattern_sets = []
    for aid in account_ids:
        if aid in account_scores:
            patterns = set(account_scores[aid]['triggered_patterns'])
            pattern_sets.append(patterns)

    if not pattern_sets:
        return set()

    # Find intersection (patterns in all accounts)
    common = pattern_sets[0].copy()
    for pattern_set in pattern_sets[1:]:
        common &= pattern_set

    # If no full intersection, find frequently occurring patterns
    if not common:
        pattern_freq = defaultdict(int)
        for pset in pattern_sets:
            for pattern in pset:
                pattern_freq[pattern] += 1

        threshold = len(account_ids) * 0.5  # Present in >= 50%
        common = {p for p, count in pattern_freq.items() if count >= threshold}

    return common


def _generate_ring_description(
    ring_id: int,
    account_ids: List[str],
    patterns: Set[str],
    avg_score: float
) -> str:
    """
    Generate human-readable description of fraud ring.

    Time Complexity: O(1)
    Space Complexity: O(1)
    """
    pattern_str = ", ".join(sorted(patterns)) if patterns else "unknown"
    return (
        f"Fraud Ring {ring_id}: {len(account_ids)} accounts "
        f"({', '.join(account_ids[:3])}{'...' if len(account_ids) > 3 else ''}) "
        f"with patterns ({pattern_str}) - risk score {avg_score:.1f}"
    )


def _generate_summary(
    graph: nx.DiGraph,
    transactions_df: pd.DataFrame,
    suspicious_accounts: List[Dict],
    fraud_rings: List[Dict],
    all_scores: List[Dict]
) -> Dict[str, Any]:
    """
    Generate summary statistics section of report.

    Time Complexity: O(V + N) where V=accounts, N=transactions
    Space Complexity: O(1)

    Args:
        graph: Transaction graph
        transactions_df: Transaction data
        suspicious_accounts: Flagged accounts
        fraud_rings: Detected rings
        all_scores: All calculated scores

    Returns:
        Summary statistics dictionary
    """
    # Calculate risk tiers
    high_risk = len([s for s in suspicious_accounts if s['suspicion_score'] >= 80])
    medium_risk = len([s for s in suspicious_accounts if 50 <= s['suspicion_score'] < 80])
    low_risk = len([s for s in suspicious_accounts if s['suspicion_score'] < 50])

    # Calculate transaction volume
    total_volume = transactions_df['amount'].sum() if 'amount' in transactions_df.columns else 0.0

    # Calculate average flagged score
    avg_score = (
        sum(s['suspicion_score'] for s in suspicious_accounts) / len(suspicious_accounts)
        if suspicious_accounts else 0.0
    )

    # Pattern distribution
    pattern_counts = defaultdict(int)
    for account in suspicious_accounts:
        for pattern in account['triggered_patterns']:
            pattern_counts[pattern] += 1

    most_common_pattern = (
        max(pattern_counts.items(), key=lambda x: x[1])[0]
        if pattern_counts else None
    )

    return {
        'report_generated': _get_iso_timestamp(),
        'total_accounts_analyzed': graph.number_of_nodes(),
        'total_accounts_flagged': len(suspicious_accounts),
        'total_fraud_rings': len(fraud_rings),
        'high_risk_accounts': high_risk,
        'medium_risk_accounts': medium_risk,
        'low_risk_accounts': low_risk,
        'total_transaction_volume': round(float(total_volume), 2),
        'avg_flagged_account_score': round(avg_score, 2),
        'most_common_pattern': most_common_pattern,
        'pattern_distribution': dict(pattern_counts),
    }


def _get_iso_timestamp() -> str:
    """
    Get current timestamp in ISO 8601 format (JSON serializable).

    Time Complexity: O(1)
    Space Complexity: O(1)
    """
    return datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
