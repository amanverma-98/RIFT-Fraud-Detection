import networkx as nx
import pandas as pd
from typing import Dict, List, Any
from app.utils.logger import setup_logger
from app.utils.exceptions import GraphDetectionError
from app.config import get_settings

logger = setup_logger(__name__)


class GraphDetectionService:
    """Service for graph-based fraud detection"""

    def __init__(self):
        self.settings = get_settings()
        self.fraud_threshold = self.settings.fraud_threshold
        self.graph = nx.DiGraph()

    def build_graph(self, transactions: pd.DataFrame) -> nx.DiGraph:
        """
        Build a directed graph from transactions

        Args:
            transactions: DataFrame with columns: sender_id, receiver_id, amount, timestamp

        Returns:
            NetworkX DiGraph
        """
        try:
            logger.info("Building transaction graph...")
            self.graph.clear()

            for _, row in transactions.iterrows():
                sender = row["sender_id"]
                receiver = row["receiver_id"]
                amount = float(row["amount"])

                # Add nodes if not exists
                if sender not in self.graph:
                    self.graph.add_node(sender, type="account")
                if receiver not in self.graph:
                    self.graph.add_node(receiver, type="account")

                # Add edge with transaction amount
                if self.graph.has_edge(sender, receiver):
                    self.graph[sender][receiver]["amount"] += amount
                    self.graph[sender][receiver]["count"] += 1
                else:
                    self.graph.add_edge(
                        sender, receiver, amount=amount, count=1
                    )

            logger.info(
                f"Graph built: {self.graph.number_of_nodes()} nodes, "
                f"{self.graph.number_of_edges()} edges"
            )
            return self.graph

        except Exception as e:
            logger.error(f"Error building graph: {str(e)}")
            raise GraphDetectionError(f"Failed to build graph: {str(e)}")

    def detect_fraud_patterns(self) -> Dict[str, Any]:
        """
        Detect fraud patterns in the graph

        Returns:
            Dictionary containing detected patterns and metrics
        """
        try:
            logger.info("Detecting fraud patterns...")

            fraud_scores = self._calculate_fraud_scores()
            suspicious_nodes = self._identify_suspicious_nodes(fraud_scores)
            suspicious_cycles = self._detect_cycles()
            suspicious_transactions = self._identify_suspicious_transactions(
                fraud_scores
            )

            patterns = {
                "fraud_scores": fraud_scores,
                "suspicious_nodes": suspicious_nodes,
                "cycles": suspicious_cycles,
                "suspicious_transactions": suspicious_transactions,
            }

            logger.info(
                f"Fraud detection complete: {len(suspicious_nodes)} suspicious nodes"
            )
            return patterns

        except Exception as e:
            logger.error(f"Error detecting fraud patterns: {str(e)}")
            raise GraphDetectionError(f"Failed to detect patterns: {str(e)}")

    def _calculate_fraud_scores(self) -> Dict[str, float]:
        """Calculate fraud scores for each node"""
        fraud_scores = {}

        for node in self.graph.nodes():
            in_degree = self.graph.in_degree(node)
            out_degree = self.graph.out_degree(node)
            in_amount = sum(
                self.graph[u][node]["amount"]
                for u in self.graph.predecessors(node)
            )
            out_amount = sum(
                self.graph[node][v]["amount"]
                for v in self.graph.successors(node)
            )

            # Simple fraud score calculation
            # Higher score if high in-degree, high out-degree, high transaction amounts
            degree_score = (in_degree + out_degree) / max(self.graph.number_of_nodes(), 1)
            amount_score = min((in_amount + out_amount) / 1000000, 1.0)  # Normalize
            circulation_score = min(in_amount * out_amount / 1e12, 1.0)

            fraud_score = (degree_score * 0.3 + amount_score * 0.4 +
                          circulation_score * 0.3)
            fraud_scores[node] = min(fraud_score, 1.0)

        return fraud_scores

    def _identify_suspicious_nodes(self, fraud_scores: Dict[str, float]) -> List[Dict]:
        """Identify nodes with high fraud scores"""
        suspicious = []

        for node, score in fraud_scores.items():
            if score >= self.fraud_threshold:
                in_degree = self.graph.in_degree(node)
                out_degree = self.graph.out_degree(node)
                in_amount = sum(
                    self.graph[u][node]["amount"]
                    for u in self.graph.predecessors(node)
                )
                out_amount = sum(
                    self.graph[node][v]["amount"]
                    for v in self.graph.successors(node)
                )

                suspicious.append({
                    "node_id": node,
                    "fraud_score": round(score, 4),
                    "in_degree": in_degree,
                    "out_degree": out_degree,
                    "total_in": round(in_amount, 2),
                    "total_out": round(out_amount, 2),
                    "severity": self._calculate_severity(score),
                })

        return sorted(suspicious, key=lambda x: x["fraud_score"], reverse=True)

    def _detect_cycles(self) -> List[List[str]]:
        """Detect cycles in the transaction graph"""
        try:
            cycles = list(nx.simple_cycles(self.graph))
            cycles = [cycle for cycle in cycles if len(cycle) > 1]
            return cycles[:10]  # Return top 10 cycles
        except Exception as e:
            logger.warning(f"Error detecting cycles: {str(e)}")
            return []

    def _identify_suspicious_transactions(
        self, fraud_scores: Dict[str, float]
    ) -> List[Dict]:
        """Identify suspicious individual transactions"""
        suspicious = []

        for sender, receiver, data in self.graph.edges(data=True):
            # Transaction is suspicious if either node has high fraud score
            sender_score = fraud_scores.get(sender, 0)
            receiver_score = fraud_scores.get(receiver, 0)
            edge_score = max(sender_score, receiver_score)

            if edge_score >= self.fraud_threshold:
                suspicious.append({
                    "sender_id": sender,
                    "receiver_id": receiver,
                    "amount": round(data["amount"], 2),
                    "count": data["count"],
                    "fraud_score": round(edge_score, 4),
                })

        return sorted(suspicious, key=lambda x: x["amount"], reverse=True)[:20]

    def _calculate_severity(self, score: float) -> str:
        """Calculate severity level based on fraud score"""
        if score >= 0.9:
            return "CRITICAL"
        elif score >= 0.7:
            return "HIGH"
        elif score >= 0.5:
            return "MEDIUM"
        else:
            return "LOW"
