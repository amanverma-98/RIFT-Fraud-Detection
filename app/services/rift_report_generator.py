"""
RIFT 2026 Hackathon - Money Muling Detection Challenge
RIFT-Compliant Report Generator

Generates reports in the EXACT format specified by RIFT problem statement.
Output format is validated line-by-line against expected test case results.
"""

import json
from typing import Dict, List, Set, Any, Tuple
from datetime import datetime
from collections import defaultdict
import time
import networkx as nx
import pandas as pd

from app.utils.logger import setup_logger

logger = setup_logger(__name__)


def generate_rift_report(
    graph: nx.DiGraph,
    transactions_df: pd.DataFrame,
    cycles: List[List[str]] = None,
    fan_patterns: Dict[str, Any] = None,
    shell_chains: List[List[str]] = None,
    suspicious_scores: List[Dict] = None,
    processing_time: float = 0.0
) -> Dict[str, Any]:
    """
    Generate RIFT-compliant fraud detection report.

    EXACT OUTPUT FORMAT (as per RIFT specification):
    {
      "suspicious_accounts": [
        {
          "account_id": "ACC_00123",
          "suspicion_score": 87.5,
          "detected_patterns": ["cycle_length_3", "high_velocity"],
          "ring_id": "RING_001"
        }
      ],
      "fraud_rings": [
        {
          "ring_id": "RING_001",
          "member_accounts": ["ACC_00123", ...],
          "pattern_type": "cycle",
          "risk_score": 95.3
        }
      ],
      "summary": {
        "total_accounts_analyzed": 500,
        "suspicious_accounts_flagged": 15,
        "fraud_rings_detected": 4,
        "processing_time_seconds": 2.3
      }
    }

    Args:
        graph: NetworkX DiGraph with transaction network
        transactions_df: DataFrame with columns: sender_id, receiver_id, amount, timestamp
        cycles: List of cycles detected (each cycle is list of account IDs)
        fan_patterns: Dict with fan_in and fan_out accounts
        shell_chains: List of shell chains detected
        suspicious_scores: List of dicts with suspicion scores
        processing_time: Processing time in seconds

    Returns:
        Dict in RIFT-compliant format
    """
    start_time = time.time()
    try:
        # Initialize collections
        account_patterns = defaultdict(set)  # account_id -> set of patterns
        account_ring_map = {}  # account_id -> ring_id
        ring_members = defaultdict(set)  # ring_id -> set of account_ids
        ring_pattern_type = {}  # ring_id -> primary pattern
        ring_scores = {}  # ring_id -> score

        ring_counter = 1

        # Process cycles (Pattern: cycle_length_X)
        if cycles:
            logger.info(f"Processing {len(cycles)} cycles")
            for cycle in cycles:
                if len(cycle) >= 3 and len(cycle) <= 5:
                    pattern_name = f"cycle_length_{len(cycle)}"
                    ring_id = f"RING_{ring_counter:03d}"
                    ring_counter += 1

                    # Add all members to this ring
                    for account in cycle:
                        account_patterns[account].add(pattern_name)
                        ring_members[ring_id].add(account)
                        account_ring_map[account] = ring_id

                    ring_pattern_type[ring_id] = "cycle"
                    ring_scores[ring_id] = 85.0  # Cycles are high priority

        # Process fan patterns (fan_in_pattern, fan_out_pattern)
        if fan_patterns:
            logger.info(f"Processing fan patterns")

            # Fan-in patterns
            if "fan_in" in fan_patterns:
                for account in fan_patterns.get("fan_in", {}).keys():
                    account_patterns[account].add("fan_in_pattern")

            # Fan-out patterns
            if "fan_out" in fan_patterns:
                for account in fan_patterns.get("fan_out", {}).keys():
                    account_patterns[account].add("fan_out_pattern")

        # Process shell chains
        if shell_chains:
            logger.info(f"Processing {len(shell_chains)} shell chains")
            for chain in shell_chains:
                if len(chain) >= 3:
                    for account in chain:
                        account_patterns[account].add("shell_chain_pattern")

        # Add high velocity pattern (high transaction frequency)
        if transactions_df is not None:
            transaction_counts = (
                transactions_df['sender_id'].value_counts().to_dict()
            )
            for account, count in transaction_counts.items():
                if count >= 10:  # High velocity threshold
                    account_patterns[account].add("high_velocity")

        # Get all unique accounts from graph
        all_accounts = set(graph.nodes())

        # Build suspicious accounts list with required fields ONLY
        suspicious_accounts_list = []
        account_suspicion_map = {}

        if suspicious_scores:
            for score_dict in suspicious_scores:
                account_id = score_dict.get('account_id')
                if account_id:
                    suspicion_score = float(score_dict.get('suspicion_score', 0))
                    account_suspicion_map[account_id] = suspicion_score

        # Create suspicious accounts with EXACT RIFT format
        for account in all_accounts:
            patterns = list(account_patterns.get(account, []))

            # Only include if has patterns or high suspicion score
            suspicion_score = account_suspicion_map.get(account, 0.0)

            if patterns or suspicion_score > 50:
                suspicious_account = {
                    "account_id": account,
                    "suspicion_score": round(suspicion_score, 1),
                    "detected_patterns": sorted(patterns),  # Deterministic order
                    "ring_id": account_ring_map.get(account, None)
                }
                suspicious_accounts_list.append(suspicious_account)

        # Sort by suspicion_score descending, then by account_id ascending
        suspicious_accounts_list.sort(
            key=lambda x: (-x['suspicion_score'], x['account_id'])
        )

        # Build fraud rings with EXACT RIFT format
        fraud_rings_list = []
        for ring_id, members in ring_members.items():
            members_list = sorted(list(members))  # Deterministic order
            pattern_type = ring_pattern_type.get(ring_id, "unknown")
            risk_score = ring_scores.get(ring_id, 75.0)

            fraud_ring = {
                "ring_id": ring_id,
                "member_accounts": members_list,
                "pattern_type": pattern_type,
                "risk_score": round(risk_score, 1)
            }
            fraud_rings_list.append(fraud_ring)

        # Sort rings by ring_id (deterministic)
        fraud_rings_list.sort(key=lambda x: x['ring_id'])

        # Build summary with EXACT RIFT fields ONLY
        summary = {
            "total_accounts_analyzed": len(all_accounts),
            "suspicious_accounts_flagged": len(suspicious_accounts_list),
            "fraud_rings_detected": len(fraud_rings_list),
            "processing_time_seconds": round(processing_time + (time.time() - start_time), 1)
        }

        # Assemble final report
        report = {
            "suspicious_accounts": suspicious_accounts_list,
            "fraud_rings": fraud_rings_list,
            "summary": summary
        }

        # Validate JSON serializability
        json.dumps(report)

        logger.info(
            f"RIFT report generated: {summary['suspicious_accounts_flagged']} "
            f"suspicious accounts, {summary['fraud_rings_detected']} rings"
        )

        return report

    except Exception as e:
        logger.error(f"Error generating RIFT report: {str(e)}", exc_info=True)
        raise


def validate_rift_report(report: Dict[str, Any]) -> bool:
    """
    Validate that report matches RIFT format specification.

    Checks:
    - suspicious_accounts has required fields
    - fraud_rings has required fields
    - summary has required fields
    - JSON serializable
    """
    try:
        # Validate structure
        if not isinstance(report, dict):
            return False

        if not all(k in report for k in ['suspicious_accounts', 'fraud_rings', 'summary']):
            return False

        # Validate suspicious_accounts
        for account in report.get('suspicious_accounts', []):
            required = {'account_id', 'suspicion_score', 'detected_patterns', 'ring_id'}
            if not all(k in account for k in required):
                return False
            if not isinstance(account['suspicion_score'], (int, float)):
                return False
            if not isinstance(account['detected_patterns'], list):
                return False

        # Validate fraud_rings
        for ring in report.get('fraud_rings', []):
            required = {'ring_id', 'member_accounts', 'pattern_type', 'risk_score'}
            if not all(k in ring for k in required):
                return False
            if not isinstance(ring['member_accounts'], list):
                return False
            if not isinstance(ring['risk_score'], (int, float)):
                return False

        # Validate summary
        summary = report.get('summary', {})
        required_summary = {
            'total_accounts_analyzed',
            'suspicious_accounts_flagged',
            'fraud_rings_detected',
            'processing_time_seconds'
        }
        if not all(k in summary for k in required_summary):
            return False

        # Validate JSON serializability
        json.dumps(report)

        logger.info("RIFT report validation passed")
        return True

    except Exception as e:
        logger.error(f"RIFT report validation failed: {str(e)}")
        return False
