"""
Suspicion Scoring System for Fraud Detection.

Aggregates multiple fraud detection patterns into a unified suspicion score
for each account. Combines cycle detection, fan patterns, shell chains, and
velocity analysis into a normalized 0-100 score with pattern attribution.

Mathematical Framework:
======================

SCORING MODEL:
  S_raw(a) = Σ w_i * I_i(a)

  Where:
    S_raw(a)  = Raw score for account a
    w_i       = Weight for pattern type i
    I_i(a)    = Indicator variable (1 if pattern i detected for account a, 0 otherwise)

WEIGHTS (Points):
  - Cycle Detection (participates in circular flow):      +40
  - Fan-in Pattern (receives many transactions):          +30
  - Fan-out Pattern (sends many transactions):            +30
  - Shell Chain Detection (part of obfuscation chain):    +20
  - Velocity Bonus (rapid transaction activity):          +10
  ────────────────────────────────────────────────────────────
  Maximum Raw Score: 130 points

NORMALIZATION:
  S_norm(a) = min(100, (S_raw(a) / 130) * 100)

  Ensures:
  - Score ∈ [0, 100]
  - Linear scaling up to 130 raw points
  - Cap at 100 for practical interpretation
  - Score of 130+ raw → 100 normalized (maximum suspicion)

DOUBLE COUNTING PREVENTION:
  Each pattern type contributes AT MOST once per account:
  - I_i(a) ∈ {0, 1} (binary indicator)
  - No multiplicative effects
  - No compound scoring
  - Patterns are mutually independent in scoring

COMPLEXITY:
  Time:  O(V + E) for detection + O(V + P*L) for scoring
         where V=vertices, E=edges, P=patterns, L=pattern_length
  Space: O(V + P) for storing scores and pattern matches

Example Raw Scores:
  No patterns detected:        0 raw → 0 normalized
  Only cycle:                 40 raw → 31 normalized
  Cycle + fan-in + fan-out:  100 raw → 77 normalized
  All patterns detected:     130 raw → 100 normalized (capped)

OUTPUT FORMAT:
  [
    {
      'account_id': 'ACC001',
      'suspicion_score': 77,
      'raw_score': 100,
      'triggered_patterns': ['cycle', 'fan_in', 'fan_out'],
      'pattern_breakdown': {
        'cycle': True,
        'fan_in': True,
        'fan_out': False,
        'shell_chain': False,
        'velocity': False
      }
    },
    ...
  ]
"""

import networkx as nx
import pandas as pd
from typing import List, Dict, Set, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import logging

from app.utils.logger import setup_logger
from app.utils.exceptions import GraphDetectionError
from app.services.cycle_detection import detect_cycles
from app.services.fan_pattern_detection import detect_fan_patterns
from app.services.shell_chain_detection import detect_shell_chains

logger = setup_logger(__name__)

# Scoring weights (points)
WEIGHTS = {
    'cycle': 40,
    'fan_in': 30,
    'fan_out': 30,
    'shell_chain': 20,
    'velocity': 10,
}

# Maximum possible raw score
MAX_RAW_SCORE = sum(WEIGHTS.values())  # 130

# Normalization ceiling
MAX_NORMALIZED_SCORE = 100


def calculate_suspicion_scores(
    graph: nx.DiGraph,
    transactions_df: pd.DataFrame,
    min_cycle_length: int = 3,
    max_cycle_length: int = 5,
    fan_threshold: int = 10,
    fan_window_hours: int = 72,
    shell_threshold: int = 3,
    velocity_threshold: int = 10,
    velocity_window_hours: int = 24
) -> List[Dict]:
    """
    Calculate suspicion scores for all accounts based on multiple fraud patterns.

    Detects and aggregates:
    1. Cycle participation (circular money flows)
    2. Fan-in patterns (receiving many transactions)
    3. Fan-out patterns (sending many transactions)
    4. Shell chain involvement (paths through suspected shell companies)
    5. Velocity bonus (rapid transaction activity)

    Time Complexity: O(V + E + N log N)
      - Cycle detection: O(C*L) with NetworkX
      - Fan pattern: O(N log N) sorting + O(N) sliding window
      - Shell chains: O(V+E) BFS with pruning
      - Score aggregation: O(V + P*L) where P = patterns, L = length
      - Overall dominated by fan pattern sorting

    Space Complexity: O(V + E + P + N)
      - Graph storage: O(V + E)
      - Pattern results: O(P)
      - Transaction storage: O(N)
      - Score dictionary: O(V)

    Args:
        graph: networkx.DiGraph with transaction edges
        transactions_df: DataFrame with columns: sender_id, receiver_id, timestamp
        min_cycle_length: Minimum cycle nodes (default: 3)
        max_cycle_length: Maximum cycle nodes (default: 5)
        fan_threshold: Minimum transactions for fan pattern (default: 10)
        fan_window_hours: Time window for fan patterns in hours (default: 72)
        shell_threshold: Maximum degree for shell node (default: 3)
        velocity_threshold: Minimum transactions for velocity bonus (default: 10)
        velocity_window_hours: Time window for velocity in hours (default: 24)

    Returns:
        List[Dict] sorted by suspicion_score descending:
        [
            {
                'account_id': str,
                'suspicion_score': int,  # Normalized [0, 100]
                'raw_score': int,        # [0, 130]
                'triggered_patterns': List[str],  # Pattern names
                'pattern_breakdown': {   # Per-pattern details
                    'cycle': bool,
                    'fan_in': bool,
                    'fan_out': bool,
                    'shell_chain': bool,
                    'velocity': bool
                },
                'score_breakdown': {     # Points per pattern
                    'cycle': int,
                    'fan_in': int,
                    'fan_out': int,
                    'shell_chain': int,
                    'velocity': int
                }
            },
            ...
        ]

    Raises:
        GraphDetectionError: If validation fails
        TypeError: If input types are invalid
        ValueError: If parameters are invalid

    Example:
        >>> scores = calculate_suspicion_scores(
        ...     graph, transactions_df,
        ...     fan_threshold=10,
        ...     shell_threshold=3
        ... )
        >>> for score_dict in scores[:5]:
        ...     print(f"{score_dict['account_id']}: {score_dict['suspicion_score']}/100")
        ...     print(f"  Patterns: {', '.join(score_dict['triggered_patterns'])}")
    """
    try:
        logger.info(
            f"Starting suspicion scoring: nodes={graph.number_of_nodes()}, "
            f"edges={graph.number_of_edges()}, transactions={len(transactions_df)}"
        )

        # Validate inputs
        _validate_scoring_inputs(graph, transactions_df)

        # Initialize score tracking for all nodes
        all_accounts = set(graph.nodes())
        scores = {
            account: {
                'account_id': account,
                'cycle': False,
                'fan_in': False,
                'fan_out': False,
                'shell_chain': False,
                'velocity': False,
                'raw_score': 0,
            }
            for account in all_accounts
        }

        # Detect each pattern type
        logger.debug("Detecting cycles...")
        cycle_accounts = _detect_cycle_accounts(graph, min_cycle_length, max_cycle_length)
        for account in cycle_accounts:
            if account in scores:
                scores[account]['cycle'] = True

        logger.debug("Detecting fan patterns...")
        fan_in_accounts, fan_out_accounts = _detect_fan_accounts(
            transactions_df, fan_threshold, fan_window_hours
        )
        for account in fan_in_accounts:
            if account in scores:
                scores[account]['fan_in'] = True
        for account in fan_out_accounts:
            if account in scores:
                scores[account]['fan_out'] = True

        logger.debug("Detecting shell chains...")
        shell_chain_accounts = _detect_shell_chain_accounts(
            graph, shell_threshold
        )
        for account in shell_chain_accounts:
            if account in scores:
                scores[account]['shell_chain'] = True

        logger.debug("Calculating velocity bonus...")
        velocity_accounts = _detect_velocity_accounts(
            transactions_df, velocity_threshold, velocity_window_hours
        )
        for account in velocity_accounts:
            if account in scores:
                scores[account]['velocity'] = True

        # Calculate raw scores
        for account, patterns in scores.items():
            raw_score = 0
            if patterns['cycle']:
                raw_score += WEIGHTS['cycle']
            if patterns['fan_in']:
                raw_score += WEIGHTS['fan_in']
            if patterns['fan_out']:
                raw_score += WEIGHTS['fan_out']
            if patterns['shell_chain']:
                raw_score += WEIGHTS['shell_chain']
            if patterns['velocity']:
                raw_score += WEIGHTS['velocity']

            patterns['raw_score'] = raw_score

        # Normalize scores and build results
        results = []
        for account, patterns in scores.items():
            # Skip accounts with zero raw score
            if patterns['raw_score'] == 0:
                continue

            normalized_score = _normalize_score(patterns['raw_score'])
            triggered_patterns = [
                name for name, triggered in patterns.items()
                if triggered and name != 'raw_score' and name != 'account_id'
            ]

            result = {
                'account_id': account,
                'suspicion_score': normalized_score,
                'raw_score': patterns['raw_score'],
                'triggered_patterns': sorted(triggered_patterns),
                'pattern_breakdown': {
                    'cycle': patterns['cycle'],
                    'fan_in': patterns['fan_in'],
                    'fan_out': patterns['fan_out'],
                    'shell_chain': patterns['shell_chain'],
                    'velocity': patterns['velocity'],
                },
                'score_breakdown': {
                    'cycle': WEIGHTS['cycle'] if patterns['cycle'] else 0,
                    'fan_in': WEIGHTS['fan_in'] if patterns['fan_in'] else 0,
                    'fan_out': WEIGHTS['fan_out'] if patterns['fan_out'] else 0,
                    'shell_chain': WEIGHTS['shell_chain'] if patterns['shell_chain'] else 0,
                    'velocity': WEIGHTS['velocity'] if patterns['velocity'] else 0,
                },
            }
            results.append(result)

        # Sort by suspicion score descending
        results.sort(key=lambda x: x['suspicion_score'], reverse=True)

        logger.info(
            f"Suspicion scoring complete: {len(results)} accounts with suspicious patterns\n"
            f"  High risk (80+): {len([r for r in results if r['suspicion_score'] >= 80])}\n"
            f"  Medium risk (50-79): {len([r for r in results if 50 <= r['suspicion_score'] < 80])}\n"
            f"  Low risk (0-49): {len([r for r in results if r['suspicion_score'] < 50])}"
        )

        return results

    except (TypeError, ValueError, GraphDetectionError):
        raise
    except Exception as e:
        logger.error(f"Error calculating suspicion scores: {str(e)}", exc_info=True)
        raise GraphDetectionError(f"Suspicion scoring failed: {str(e)}")


def _validate_scoring_inputs(graph: nx.DiGraph, transactions_df: pd.DataFrame) -> None:
    """
    Validate inputs for suspicion scoring.

    Time Complexity: O(N) for column checking
    Space Complexity: O(1)
    """
    if not isinstance(graph, nx.DiGraph):
        raise TypeError("Graph must be networkx.DiGraph")

    if not isinstance(transactions_df, pd.DataFrame):
        raise TypeError("Transactions must be pandas DataFrame")

    if transactions_df.empty:
        raise ValueError("Transactions DataFrame is empty")

    required_cols = {'sender_id', 'receiver_id', 'timestamp'}
    missing = required_cols - set(transactions_df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    logger.debug(f"Input validation passed: graph nodes={graph.number_of_nodes()}, "
                 f"transactions={len(transactions_df)}")


def _detect_cycle_accounts(
    graph: nx.DiGraph,
    min_length: int,
    max_length: int
) -> Set[str]:
    """
    Detect accounts that participate in cycles.

    Time Complexity: O(C*L) for cycle detection + O(C*L) for account extraction
      where C = number of cycles, L = average cycle length
    Space Complexity: O(C*L) for storing cycles

    Args:
        graph: Transaction graph
        min_length: Minimum cycle length
        max_length: Maximum cycle length

    Returns:
        Set of account IDs that appear in any detected cycle
    """
    try:
        cycles = detect_cycles(graph, min_length=min_length, max_length=max_length)
        cycle_accounts = set()

        for cycle in cycles:
            cycle_accounts.update(cycle)

        logger.debug(f"Found {len(cycles)} cycles with {len(cycle_accounts)} unique accounts")
        return cycle_accounts

    except Exception as e:
        logger.warning(f"Error detecting cycles: {str(e)}")
        return set()


def _detect_fan_accounts(
    transactions_df: pd.DataFrame,
    threshold: int,
    window_hours: int
) -> Tuple[Set[str], Set[str]]:
    """
    Detect accounts with fan-in or fan-out patterns.

    Time Complexity: O(N log N + P) where N = transactions, P = patterns
    Space Complexity: O(N + P)

    Args:
        transactions_df: Transaction DataFrame
        threshold: Minimum transactions for pattern detection
        window_hours: Time window in hours

    Returns:
        Tuple of (fan_in_accounts, fan_out_accounts) sets
    """
    try:
        patterns = detect_fan_patterns(
            transactions_df,
            transaction_threshold=threshold,
            time_window_hours=window_hours
        )

        fan_in = set()
        fan_out = set()

        for pattern in patterns:
            if pattern['pattern_type'] == 'fan_in':
                fan_in.add(pattern['account_id'])
            elif pattern['pattern_type'] == 'fan_out':
                fan_out.add(pattern['account_id'])

        logger.debug(f"Fan patterns: {len(fan_in)} fan-in, {len(fan_out)} fan-out accounts")
        return fan_in, fan_out

    except Exception as e:
        logger.warning(f"Error detecting fan patterns: {str(e)}")
        return set(), set()


def _detect_shell_chain_accounts(
    graph: nx.DiGraph,
    shell_threshold: int
) -> Set[str]:
    """
    Detect accounts that participate in shell chains.

    Time Complexity: O(V + E) BFS with pruning
    Space Complexity: O(V + E + P*L) for queue and chains

    Args:
        graph: Transaction graph
        shell_threshold: Maximum degree for shell node

    Returns:
        Set of account IDs that appear in any detected shell chain
    """
    try:
        chains = detect_shell_chains(
            graph,
            shell_threshold=shell_threshold,
            max_chains=1000
        )

        shell_accounts = set()
        for chain_dict in chains:
            chain = chain_dict['chain']
            shell_accounts.update(chain)

        logger.debug(f"Found {len(chains)} shell chains with {len(shell_accounts)} unique accounts")
        return shell_accounts

    except Exception as e:
        logger.warning(f"Error detecting shell chains: {str(e)}")
        return set()


def _detect_velocity_accounts(
    transactions_df: pd.DataFrame,
    threshold: int,
    window_hours: int
) -> Set[str]:
    """
    Detect accounts with high transaction velocity (rapid activity).

    Identifies accounts sending OR receiving >= threshold transactions
    within window_hours.

    Time Complexity: O(N log N) for sorting + O(N) for sliding window
    Space Complexity: O(N)

    Args:
        transactions_df: Transaction DataFrame
        threshold: Minimum transactions for velocity bonus
        window_hours: Time window in hours

    Returns:
        Set of account IDs with high transaction velocity
    """
    try:
        if transactions_df.empty:
            return set()

        df = transactions_df.copy()
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        window = timedelta(hours=window_hours)

        velocity_accounts = set()

        # Check sender velocity
        sender_txns = df.groupby('sender_id')['timestamp'].apply(list).to_dict()
        for sender, timestamps in sender_txns.items():
            if _has_velocity(timestamps, threshold, window):
                velocity_accounts.add(sender)

        # Check receiver velocity
        receiver_txns = df.groupby('receiver_id')['timestamp'].apply(list).to_dict()
        for receiver, timestamps in receiver_txns.items():
            if _has_velocity(timestamps, threshold, window):
                velocity_accounts.add(receiver)

        logger.debug(f"Found {len(velocity_accounts)} accounts with high transaction velocity")
        return velocity_accounts

    except Exception as e:
        logger.warning(f"Error detecting velocity: {str(e)}")
        return set()


def _has_velocity(
    timestamps: List[datetime],
    threshold: int,
    window: timedelta
) -> bool:
    """
    Check if timestamp list has >= threshold timestamps within window.

    Uses sliding window technique: O(N) time after sorting.

    Time Complexity: O(N log N) for sort + O(N) for window scan
    Space Complexity: O(1)

    Args:
        timestamps: List of transaction timestamps
        threshold: Minimum transaction count
        window: Time window duration

    Returns:
        True if velocity threshold exceeded, False otherwise
    """
    if len(timestamps) < threshold:
        return False

    sorted_ts = sorted(timestamps)

    # Sliding window
    for i in range(len(sorted_ts)):
        window_end = sorted_ts[i] + window
        count = 0

        for j in range(i, len(sorted_ts)):
            if sorted_ts[j] <= window_end:
                count += 1
            else:
                break

        if count >= threshold:
            return True

    return False


def _normalize_score(raw_score: int) -> int:
    """
    Normalize raw score [0, 130] to [0, 100].

    Mathematical Formula:
      S_norm = min(100, (S_raw / 130) * 100)

    Properties:
    - Linear scaling from 0 to 100 as raw_score goes from 0 to 130
    - Any raw_score >= 130 maps to 100 (maximum suspicion)
    - Preserves ordering: if S1 > S2, then norm(S1) >= norm(S2)

    Time Complexity: O(1)
    Space Complexity: O(1)

    Args:
        raw_score: Score from pattern weights [0, 130]

    Returns:
        Normalized score [0, 100]
    """
    if raw_score <= 0:
        return 0

    normalized = int((raw_score / MAX_RAW_SCORE) * MAX_NORMALIZED_SCORE)
    return min(normalized, MAX_NORMALIZED_SCORE)


def get_suspicion_score_summary(scores: List[Dict]) -> Dict:
    """
    Calculate summary statistics about suspicion scores.

    Time Complexity: O(S) where S = number of scores
    Space Complexity: O(1)

    Args:
        scores: List of score dicts from calculate_suspicion_scores()

    Returns:
        Dictionary with statistics
    """
    if not scores:
        return {
            'total_accounts_scored': 0,
            'high_risk_count': 0,
            'medium_risk_count': 0,
            'low_risk_count': 0,
            'avg_suspicion_score': 0,
            'max_suspicion_score': 0,
            'min_suspicion_score': 0,
            'most_common_pattern': None,
            'pattern_distribution': {},
        }

    suspicion_scores = [s['suspicion_score'] for s in scores]

    pattern_counts = defaultdict(int)
    for score_dict in scores:
        for pattern in score_dict['triggered_patterns']:
            pattern_counts[pattern] += 1

    high_risk = len([s for s in scores if s['suspicion_score'] >= 80])
    medium_risk = len([s for s in scores if 50 <= s['suspicion_score'] < 80])
    low_risk = len([s for s in scores if s['suspicion_score'] < 50])

    most_common = max(pattern_counts.items(), key=lambda x: x[1])[0] if pattern_counts else None

    return {
        'total_accounts_scored': len(scores),
        'high_risk_count': high_risk,
        'medium_risk_count': medium_risk,
        'low_risk_count': low_risk,
        'avg_suspicion_score': round(sum(suspicion_scores) / len(suspicion_scores), 2),
        'max_suspicion_score': max(suspicion_scores),
        'min_suspicion_score': min(suspicion_scores),
        'most_common_pattern': most_common,
        'pattern_distribution': dict(pattern_counts),
    }
