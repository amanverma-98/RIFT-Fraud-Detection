"""
Report Storage Service - Persists reports to SQLite
"""
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class ReportStorage:
    """Manages persistent storage of fraud detection reports"""

    def __init__(self, db_path: str = "fraud_detection_reports.db"):
        """
        Initialize report storage

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize database schema"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS reports (
                        report_id TEXT PRIMARY KEY,
                        filename TEXT NOT NULL,
                        data TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    )
                """)
                conn.commit()
            logger.info(f"Report storage initialized: {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to initialize report storage: {str(e)}")
            raise

    def save_report(self, report: Dict[str, Any]) -> bool:
        """
        Save report to database

        Args:
            report: Report dictionary to save

        Returns:
            True if successful, False otherwise
        """
        try:
            report_id = report.get("report_id")
            filename = report.get("filename", "unknown")
            created_at = report.get("timestamp", datetime.utcnow().isoformat())

            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO reports
                    (report_id, filename, data, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    report_id,
                    filename,
                    json.dumps(report),
                    created_at,
                    datetime.utcnow().isoformat()
                ))
                conn.commit()

            logger.info(f"Report saved: {report_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to save report: {str(e)}")
            return False

    def get_report(self, report_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve report from database

        Args:
            report_id: ID of report to retrieve

        Returns:
            Report dictionary or None if not found
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT data FROM reports WHERE report_id = ?",
                    (report_id,)
                )
                row = cursor.fetchone()

                if row:
                    logger.info(f"Report retrieved: {report_id}")
                    return json.loads(row[0])
                else:
                    logger.warning(f"Report not found: {report_id}")
                    return None
        except Exception as e:
            logger.error(f"Failed to retrieve report: {str(e)}")
            return None

    def get_all_reports(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Retrieve all reports, sorted by creation date

        Args:
            limit: Maximum number of reports to return

        Returns:
            List of report dictionaries
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT data FROM reports ORDER BY created_at DESC LIMIT ?",
                    (limit,)
                )
                rows = cursor.fetchall()
                reports = [json.loads(row[0]) for row in rows]
                logger.info(f"Retrieved {len(reports)} reports")
                return reports
        except Exception as e:
            logger.error(f"Failed to retrieve reports: {str(e)}")
            return []

    def delete_report(self, report_id: str) -> bool:
        """
        Delete report from database

        Args:
            report_id: ID of report to delete

        Returns:
            True if successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "DELETE FROM reports WHERE report_id = ?",
                    (report_id,)
                )
                conn.commit()

                if cursor.rowcount > 0:
                    logger.info(f"Report deleted: {report_id}")
                    return True
                else:
                    logger.warning(f"Report not found for deletion: {report_id}")
                    return False
        except Exception as e:
            logger.error(f"Failed to delete report: {str(e)}")
            return False

    def report_exists(self, report_id: str) -> bool:
        """
        Check if report exists

        Args:
            report_id: ID to check

        Returns:
            True if exists, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT 1 FROM reports WHERE report_id = ? LIMIT 1",
                    (report_id,)
                )
                return cursor.fetchone() is not None
        except Exception as e:
            logger.error(f"Failed to check report existence: {str(e)}")
            return False

    def get_report_count(self) -> int:
        """
        Get total number of reports

        Returns:
            Number of reports in database
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT COUNT(*) FROM reports")
                count = cursor.fetchone()[0]
                return count
        except Exception as e:
            logger.error(f"Failed to get report count: {str(e)}")
            return 0
