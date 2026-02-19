"""
Fan-in and Fan-out fraud detection patterns.

Detects suspicious transaction patterns where an account receives (fan-in)
or sends (fan-out) many transactions in a short time window.

Time Complexity: O(N log N) where N = number of transactions
- Sorting: O(N log N)
- Sliding window: O(N) single pass per account
- Total: O(N log N) dominated by sorting
"""

import pandas as pd
from typing import List, Dict, Tuple, DefaultDict
from collections import defaultdict
from datetime import datetime, timedelta
import logging

from app.utils.logger import setup_logger
from app.utils.exceptions import GraphDetectionError

logger = setup_logger(__name__)


class FanPatternDetector:
    """
    Detects fan-in and fan-out patterns in transaction data.

    A fan-in pattern occurs when an account receives many transactions
    in a short time window (suspicious account aggregation).

    A fan-out pattern occurs when an account sends many transactions
    in a short time window (suspicious distribution/money laundering).

    Uses efficient sliding window technique with pre-sorted timestamps.

    Time Complexity: O(N log N) for sorting + O(N) for detection
    Space Complexity: O(N) for storing transactions and results
    """

    def __init__(
        self,
        transaction_threshold: int = 10,
        time_window_hours: int = 72
    ):
        """
        Initialize the detector.

        Args:
            transaction_threshold: Minimum transactions to flag pattern (default: 10)
            time_window_hours: Time window in hours (default: 72 = 3 days)
        """
        if transaction_threshold < 2:
            raise ValueError(f"transaction_threshold must be >= 2, got {transaction_threshold}")
        if time_window_hours <= 0:
            raise ValueError(f"time_window_hours must be > 0, got {time_window_hours}")

        self.threshold = transaction_threshold
        self.window = timedelta(hours=time_window_hours)
        self.window_hours = time_window_hours

        logger.info(
            f"FanPatternDetector initialized: threshold={transaction_threshold}, "
            f"window={time_window_hours}h"
        )

    def detect_patterns(
        self,
        transactions_df: pd.DataFrame
    ) -> List[Dict]:
        """
        Detect fan-in and fan-out patterns in transaction data.

        Main entry point for pattern detection. Uses sliding window technique
        with efficient timestamp sorting.

        Time Complexity: O(N log N) where N = number of transactions
        - Sorting by timestamp: O(N log N)
        - Sliding window processing: O(N) amortized
        - Overall: O(N log N) dominated by sorting

        Space Complexity: O(N) for storing transactions and results

        Args:
            transactions_df: DataFrame with columns:
                - sender_id: Source account
                - receiver_id: Destination account
                - timestamp: Transaction timestamp (datetime)

        Returns:
            List[Dict] with detected patterns:
            [{
                'account_id': 'ACC001',
                'pattern_type': 'fan_in' or 'fan_out',
                'transaction_count': 15,
                'time_window_hours': 72,
                'first_timestamp': datetime(...),
                'last_timestamp': datetime(...),
                'transactions': [...]  # Transaction details
            }]

        Raises:
            GraphDetectionError: If validation fails
        """
        try:
            logger.info(
                f"Starting pattern detection: {len(transactions_df)} transactions"
            )

            # Validate input
            self._validate_input(transactions_df)

            # Detect both patterns
            fan_in_patterns = self._detect_fan_in(transactions_df)
            fan_out_patterns = self._detect_fan_out(transactions_df)

            # Combine results
            all_patterns = fan_in_patterns + fan_out_patterns

            # Sort by transaction count (descending) for severity ranking
            all_patterns.sort(
                key=lambda x: x['transaction_count'],
                reverse=True
            )

            logger.info(
                f"Detection complete: {len(fan_in_patterns)} fan-in, "
                f"{len(fan_out_patterns)} fan-out patterns"
            )

            return all_patterns

        except GraphDetectionError:
            raise
        except Exception as e:
            logger.error(f"Error detecting patterns: {str(e)}", exc_info=True)
            raise GraphDetectionError(f"Failed to detect patterns: {str(e)}")

    def _validate_input(self, df: pd.DataFrame) -> None:
        """Validate input DataFrame structure."""
        required = {'sender_id', 'receiver_id', 'timestamp'}

        if df.empty:
            raise GraphDetectionError("Input DataFrame is empty")

        missing = required - set(df.columns)
        if missing:
            raise GraphDetectionError(f"Missing columns: {missing}")

        # Validate timestamp column
        if not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
            try:
                pd.to_datetime(df['timestamp'])
            except Exception as e:
                raise GraphDetectionError(f"Invalid timestamp column: {str(e)}")

        logger.debug(f"Input validation passed: {len(df)} transactions")

    def _detect_fan_in(self, df: pd.DataFrame) -> List[Dict]:
        """
        Detect fan-in patterns (many incoming transactions).

        Time Complexity: O(N log N) for sorting + O(N) for sliding window
        Space Complexity: O(U) where U = unique receivers

        Args:
            df: Transaction DataFrame

        Returns:
            List of fan-in patterns detected
        """
        logger.debug("Detecting fan-in patterns...")

        # Group by receiver and sort by timestamp
        # Time: O(N log N) for sorting
        receiver_txns: DefaultDict[str, List[Tuple[datetime, int]]] = defaultdict(list)

        for idx, row in df.iterrows():
            receiver = str(row['receiver_id']).strip()
            timestamp = row['timestamp']
            receiver_txns[receiver].append((timestamp, idx))

        # Sort each receiver's transactions by timestamp
        # Time: O(N log N) total across all receivers
        for receiver in receiver_txns:
            receiver_txns[receiver].sort(key=lambda x: x[0])

        # Apply sliding window to each receiver
        # Time: O(N) amortized
        patterns = []

        for receiver, txn_list in receiver_txns.items():
            detected_windows = self._find_patterns_sliding_window(
                txn_list,
                "fan_in"
            )

            for window_pattern in detected_windows:
                patterns.append({
                    'account_id': receiver,
                    'pattern_type': 'fan_in',
                    'transaction_count': window_pattern['count'],
                    'time_window_hours': self.window_hours,
                    'first_timestamp': window_pattern['first'],
                    'last_timestamp': window_pattern['last'],
                    'window_duration_hours': (
                        (window_pattern['last'] - window_pattern['first']).total_seconds() / 3600
                    ),
                })

        logger.info(f"Found {len(patterns)} fan-in patterns")
        return patterns

    def _detect_fan_out(self, df: pd.DataFrame) -> List[Dict]:
        """
        Detect fan-out patterns (many outgoing transactions).

        Time Complexity: O(N log N) for sorting + O(N) for sliding window
        Space Complexity: O(U) where U = unique senders

        Args:
            df: Transaction DataFrame

        Returns:
            List of fan-out patterns detected
        """
        logger.debug("Detecting fan-out patterns...")

        # Group by sender and sort by timestamp
        # Time: O(N log N) for sorting
        sender_txns: DefaultDict[str, List[Tuple[datetime, int]]] = defaultdict(list)

        for idx, row in df.iterrows():
            sender = str(row['sender_id']).strip()
            timestamp = row['timestamp']
            sender_txns[sender].append((timestamp, idx))

        # Sort each sender's transactions by timestamp
        # Time: O(N log N) total across all senders
        for sender in sender_txns:
            sender_txns[sender].sort(key=lambda x: x[0])

        # Apply sliding window to each sender
        # Time: O(N) amortized
        patterns = []

        for sender, txn_list in sender_txns.items():
            detected_windows = self._find_patterns_sliding_window(
                txn_list,
                "fan_out"
            )

            for window_pattern in detected_windows:
                patterns.append({
                    'account_id': sender,
                    'pattern_type': 'fan_out',
                    'transaction_count': window_pattern['count'],
                    'time_window_hours': self.window_hours,
                    'first_timestamp': window_pattern['first'],
                    'last_timestamp': window_pattern['last'],
                    'window_duration_hours': (
                        (window_pattern['last'] - window_pattern['first']).total_seconds() / 3600
                    ),
                })

        logger.info(f"Found {len(patterns)} fan-out patterns")
        return patterns

    def _find_patterns_sliding_window(
        self,
        sorted_txns: List[Tuple[datetime, int]],
        pattern_type: str
    ) -> List[Dict]:
        """
        Find patterns using sliding window technique.

        ALGORITHM (Sliding Window):
        1. Start with left pointer at first transaction
        2. Move right pointer forward while within time window
        3. Count transactions in window
        4. If count >= threshold, record pattern
        5. Slide left pointer forward by 1
        6. Repeat until end of transactions

        Time Complexity: O(N) - single pass with two pointers
        Space Complexity: O(K) where K = patterns found

        Args:
            sorted_txns: Pre-sorted list of (timestamp, index) tuples
            pattern_type: 'fan_in' or 'fan_out' for logging

        Returns:
            List of detected patterns (may be multiple per account)
        """
        patterns = []
        n = len(sorted_txns)

        if n < self.threshold:
            return patterns  # Not enough transactions

        # Sliding window: O(N) time, two pointers
        left = 0

        while left < n:
            right = left
            window_end = sorted_txns[left][0] + self.window

            # Expand right pointer to include all txns within window
            while right < n and sorted_txns[right][0] <= window_end:
                right += 1

            # Count transactions in window [left, right)
            count = right - left

            # If threshold met, record pattern
            if count >= self.threshold:
                patterns.append({
                    'count': count,
                    'first': sorted_txns[left][0],
                    'last': sorted_txns[right - 1][0],
                })

                logger.debug(
                    f"{pattern_type} window: {count} transactions "
                    f"in {(sorted_txns[right-1][0] - sorted_txns[left][0]).total_seconds()/3600:.1f}h"
                )

                # Move left pointer past first transaction of current window
                left += 1
            else:
                # Move left pointer to try next position
                left += 1

        return patterns

    def detect_patterns_fast(
        self,
        transactions_df: pd.DataFrame
    ) -> List[Dict]:
        """
        Optimized version for very large datasets.

        Uses vectorized operations where possible for better performance
        on datasets with millions of transactions.

        Time Complexity: Still O(N log N) but with better constants
        Space Complexity: O(N)

        Args:
            transactions_df: Transaction DataFrame

        Returns:
            List of detected patterns (simplified output)
        """
        try:
            logger.info(f"Starting fast pattern detection: {len(transactions_df)} transactions")

            self._validate_input(transactions_df)

            # Ensure timestamps are datetime
            df = transactions_df.copy()
            df['timestamp'] = pd.to_datetime(df['timestamp'])

            patterns = []

            # Fan-in patterns
            fan_in = self._detect_fan_in_fast(df)
            patterns.extend(fan_in)

            # Fan-out patterns
            fan_out = self._detect_fan_out_fast(df)
            patterns.extend(fan_out)

            logger.info(
                f"Fast detection complete: {len(fan_in)} fan-in, {len(fan_out)} fan-out"
            )

            return patterns

        except Exception as e:
            logger.error(f"Error in fast detection: {str(e)}")
            raise GraphDetectionError(f"Fast detection failed: {str(e)}")

    def _detect_fan_in_fast(self, df: pd.DataFrame) -> List[Dict]:
        """Fast fan-in detection using pandas groupby and rolling window."""
        patterns = []

        for receiver in df['receiver_id'].unique():
            receiver_txns = df[df['receiver_id'] == receiver].copy()
            receiver_txns = receiver_txns.sort_values('timestamp')

            # Use pandas rolling window
            rolling_count = (
                receiver_txns.set_index('timestamp')
                .rolling(self.window, min_periods=1)
                .size()
            )

            # Find windows with >= threshold transactions
            suspicious_windows = rolling_count[rolling_count >= self.threshold]

            if len(suspicious_windows) > 0:
                # Get the maximum window
                max_window_size = suspicious_windows.max()
                pattern_timestamps = receiver_txns['timestamp'].values

                # Find first and last timestamp in the pattern
                first_ts = pattern_timestamps[0]
                last_ts = pattern_timestamps[min(max_window_size - 1, len(pattern_timestamps) - 1)]

                patterns.append({
                    'account_id': receiver,
                    'pattern_type': 'fan_in',
                    'transaction_count': max_window_size,
                    'time_window_hours': self.window_hours,
                    'first_timestamp': first_ts,
                    'last_timestamp': last_ts,
                })

        return patterns

    def _detect_fan_out_fast(self, df: pd.DataFrame) -> List[Dict]:
        """Fast fan-out detection using pandas groupby and rolling window."""
        patterns = []

        for sender in df['sender_id'].unique():
            sender_txns = df[df['sender_id'] == sender].copy()
            sender_txns = sender_txns.sort_values('timestamp')

            # Use pandas rolling window
            rolling_count = (
                sender_txns.set_index('timestamp')
                .rolling(self.window, min_periods=1)
                .size()
            )

            # Find windows with >= threshold transactions
            suspicious_windows = rolling_count[rolling_count >= self.threshold]

            if len(suspicious_windows) > 0:
                # Get the maximum window
                max_window_size = suspicious_windows.max()
                pattern_timestamps = sender_txns['timestamp'].values

                # Find first and last timestamp in the pattern
                first_ts = pattern_timestamps[0]
                last_ts = pattern_timestamps[min(max_window_size - 1, len(pattern_timestamps) - 1)]

                patterns.append({
                    'account_id': sender,
                    'pattern_type': 'fan_out',
                    'transaction_count': max_window_size,
                    'time_window_hours': self.window_hours,
                    'first_timestamp': first_ts,
                    'last_timestamp': last_ts,
                })

        return patterns


def detect_fan_patterns(
    transactions_df: pd.DataFrame,
    transaction_threshold: int = 10,
    time_window_hours: int = 72
) -> List[Dict]:
    """
    Convenience function to detect fan-in/fan-out patterns.

    Time Complexity: O(N log N) where N = number of transactions
    Space Complexity: O(N)

    Args:
        transactions_df: Transaction data with sender_id, receiver_id, timestamp
        transaction_threshold: Minimum transactions to flag (default: 10)
        time_window_hours: Time window in hours (default: 72)

    Returns:
        List of detected patterns with account_id, pattern_type, transaction_count

    Example:
        patterns = detect_fan_patterns(df, transaction_threshold=10, time_window_hours=72)
        for pattern in patterns:
            print(f"{pattern['account_id']}: {pattern['pattern_type']} "
                  f"({pattern['transaction_count']} txns)")
    """
    detector = FanPatternDetector(
        transaction_threshold=transaction_threshold,
        time_window_hours=time_window_hours
    )
    return detector.detect_patterns(transactions_df)


def get_fan_pattern_statistics(patterns: List[Dict]) -> Dict:
    """
    Calculate statistics about detected fan patterns.

    Time Complexity: O(P) where P = number of patterns
    Space Complexity: O(1)

    Args:
        patterns: List of detected patterns from detect_fan_patterns()

    Returns:
        Dictionary with statistics:
        {
            'total_patterns': int,
            'fan_in_count': int,
            'fan_out_count': int,
            'avg_transaction_count': float,
            'max_transaction_count': int,
            'min_transaction_count': int,
            'by_pattern_type': {type: count}
        }
    """
    if not patterns:
        return {
            'total_patterns': 0,
            'fan_in_count': 0,
            'fan_out_count': 0,
            'avg_transaction_count': 0,
            'max_transaction_count': 0,
            'min_transaction_count': 0,
            'by_pattern_type': {},
        }

    fan_in = [p for p in patterns if p['pattern_type'] == 'fan_in']
    fan_out = [p for p in patterns if p['pattern_type'] == 'fan_out']

    txn_counts = [p['transaction_count'] for p in patterns]

    return {
        'total_patterns': len(patterns),
        'fan_in_count': len(fan_in),
        'fan_out_count': len(fan_out),
        'avg_transaction_count': sum(txn_counts) / len(txn_counts),
        'max_transaction_count': max(txn_counts),
        'min_transaction_count': min(txn_counts),
        'by_pattern_type': {
            'fan_in': len(fan_in),
            'fan_out': len(fan_out),
        },
    }
