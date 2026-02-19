import json
import uuid
from datetime import datetime
from typing import Dict, Any, List
from app.utils.logger import setup_logger
from app.utils.exceptions import ReportGenerationError

logger = setup_logger(__name__)


class ReportGenerator:
    """Service for generating fraud detection reports"""

    def __init__(self):
        pass

    def generate_report(
        self,
        graph_data: Any,
        fraud_patterns: Dict[str, Any],
        filename: str,
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive fraud detection report

        Args:
            graph_data: NetworkX graph
            fraud_patterns: Dictionary of detected fraud patterns
            filename: Name of the processed CSV file

        Returns:
            Dictionary containing the fraud report
        """
        try:
            logger.info("Generating fraud detection report...")

            report_id = str(uuid.uuid4())
            timestamp = datetime.utcnow().isoformat()

            report = {
                "report_id": report_id,
                "timestamp": timestamp,
                "source_file": filename,
                "graph_metrics": self._generate_graph_metrics(graph_data),
                "fraud_summary": self._generate_fraud_summary(fraud_patterns),
                "suspicious_nodes": fraud_patterns.get("suspicious_nodes", []),
                "suspicious_transactions": fraud_patterns.get(
                    "suspicious_transactions", []
                ),
                "detected_cycles": fraud_patterns.get("cycles", []),
            }

            logger.info(f"Report generated: {report_id}")
            return report

        except Exception as e:
            logger.error(f"Error generating report: {str(e)}")
            raise ReportGenerationError(f"Failed to generate report: {str(e)}")

    def _generate_graph_metrics(self, graph_data: Any) -> Dict[str, Any]:
        """Generate graph-related metrics"""
        import networkx as nx

        return {
            "total_nodes": graph_data.number_of_nodes(),
            "total_edges": graph_data.number_of_edges(),
            "density": float(graph_data.number_of_edges()) / max(
                graph_data.number_of_nodes() * (graph_data.number_of_nodes() - 1), 1
            ),
            "num_weakly_connected_components": len(
                list(nx.strongly_connected_components(graph_data))
            ),
        }


    def _generate_fraud_summary(self, fraud_patterns: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary statistics about fraud patterns"""
        suspicious_nodes = fraud_patterns.get("suspicious_nodes", [])
        suspicious_transactions = fraud_patterns.get("suspicious_transactions", [])
        cycles = fraud_patterns.get("cycles", [])

        total_suspicious_amount = sum(
            t.get("amount", 0) for t in suspicious_transactions
        )

        severity_counts = {
            "CRITICAL": sum(
                1 for n in suspicious_nodes if n.get("severity") == "CRITICAL"
            ),
            "HIGH": sum(1 for n in suspicious_nodes if n.get("severity") == "HIGH"),
            "MEDIUM": sum(
                1 for n in suspicious_nodes if n.get("severity") == "MEDIUM"
            ),
            "LOW": sum(1 for n in suspicious_nodes if n.get("severity") == "LOW"),
        }

        return {
            "total_suspicious_nodes": len(suspicious_nodes),
            "total_suspicious_transactions": len(suspicious_transactions),
            "detected_cycles": len(cycles),
            "total_suspicious_amount": round(total_suspicious_amount, 2),
            "severity_distribution": severity_counts,
            "average_fraud_score": (
                round(
                    sum(n.get("fraud_score", 0) for n in suspicious_nodes)
                    / max(len(suspicious_nodes), 1),
                    4,
                )
                if suspicious_nodes
                else 0.0
            ),
        }

    def export_to_json(self, report: Dict[str, Any], filepath: str) -> str:
        """
        Export report to JSON file

        Args:
            report: Report dictionary
            filepath: Path to save the JSON file

        Returns:
            Path to the saved file
        """
        try:
            logger.info(f"Exporting report to JSON: {filepath}")

            with open(filepath, "w") as f:
                json.dump(report, f, indent=2, default=str)

            logger.info(f"Report exported successfully: {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"Error exporting report: {str(e)}")
            raise ReportGenerationError(f"Failed to export report: {str(e)}")

    def format_report_summary(self, report: Dict[str, Any]) -> str:
        """Format report as human-readable string"""
        summary = f"""
=== FRAUD DETECTION REPORT ===
Report ID: {report['report_id']}
Timestamp: {report['timestamp']}
Source File: {report['source_file']}

Graph Metrics:
- Total Nodes: {report['graph_metrics']['total_nodes']}
- Total Edges: {report['graph_metrics']['total_edges']}
- Graph Density: {report['graph_metrics']['density']:.4f}

Fraud Summary:
- Suspicious Nodes: {report['fraud_summary']['total_suspicious_nodes']}
- Suspicious Transactions: {report['fraud_summary']['total_suspicious_transactions']}
- Detected Cycles: {report['fraud_summary']['detected_cycles']}
- Total Suspicious Amount: ${report['fraud_summary']['total_suspicious_amount']:,.2f}
- Average Fraud Score: {report['fraud_summary']['average_fraud_score']:.4f}

Severity Distribution:
- CRITICAL: {report['fraud_summary']['severity_distribution']['CRITICAL']}
- HIGH: {report['fraud_summary']['severity_distribution']['HIGH']}
- MEDIUM: {report['fraud_summary']['severity_distribution']['MEDIUM']}
- LOW: {report['fraud_summary']['severity_distribution']['LOW']}
=============================
"""
        return summary
