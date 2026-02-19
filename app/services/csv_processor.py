import os
import pandas as pd
from datetime import datetime
from app.utils.logger import setup_logger
from app.utils.exceptions import CSVProcessingError, InvalidCSVFormat
from app.utils.validators import validate_csv_file, validate_csv_content, validate_numeric_column
from app.config import get_settings

logger = setup_logger(__name__)


class CSVProcessor:
    """Service for processing CSV files"""

    def __init__(self):
        self.settings = get_settings()
        self.upload_path = self.settings.upload_path

        # Create upload directory if it doesn't exist
        if not os.path.exists(self.upload_path):
            os.makedirs(self.upload_path)

    async def process_csv(self, file_path: str) -> dict:
        """
        Process a CSV file and return transaction data

        Args:
            file_path: Path to the CSV file

        Returns:
            Dictionary containing processed data and metadata
        """
        try:
            filename = os.path.basename(file_path)
            logger.info(f"Processing CSV file: {filename}")

            # Validate file
            validate_csv_file(filename)

            # Read CSV
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")

            df = pd.read_csv(file_path)
            logger.info(f"Loaded {len(df)} records from {filename}")

            # Validate content
            validate_csv_content(df)
            validate_numeric_column(df, "amount")

            # Clean data
            df = self._clean_data(df)

            total_records = len(df)
            failed_records = df.isnull().any(axis=1).sum()
            processed_records = total_records - failed_records

            logger.info(
                f"CSV processing complete: {processed_records}/{total_records} records"
            )

            return {
                "filename": filename,
                "data": df.dropna(),
                "total_records": total_records,
                "processed_records": processed_records,
                "failed_records": failed_records,
                "timestamp": datetime.utcnow().isoformat(),
            }

        except (InvalidCSVFormat, FileNotFoundError) as e:
            logger.error(f"CSV processing error: {str(e)}")
            raise CSVProcessingError(str(e))
        except Exception as e:
            logger.error(f"Unexpected error processing CSV: {str(e)}")
            raise CSVProcessingError(f"Failed to process CSV: {str(e)}")

    def _clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and normalize CSV data"""
        df = df.copy()

        # Convert sender_id/receiver_id to string
        df["sender_id"] = df["sender_id"].astype(str).str.strip()
        df["receiver_id"] = df["receiver_id"].astype(str).str.strip()

        # Convert amount to float
        df["amount"] = pd.to_numeric(df["amount"], errors="coerce")

        # Parse timestamp to datetime (ISO 8601 format like "2026-02-19T11:56:10.008Z")
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")

        # Remove rows with null values
        df = df.dropna()

        # Remove duplicate transactions (based on transaction_id)
        df = df.drop_duplicates(subset=["transaction_id"])

        # Filter by minimum amount
        df = df[df["amount"] >= self.settings.min_transaction_amount]

        logger.info(f"Data cleaned: {len(df)} records remaining")
        return df

    def get_transaction_list(self, df: pd.DataFrame) -> list:
        """Convert dataframe to list of transaction dictionaries"""
        return [
            {
                "transaction_id": row["transaction_id"],
                "sender_id": row["sender_id"],
                "receiver_id": row["receiver_id"],
                "amount": float(row["amount"]),
                "timestamp": row["timestamp"].isoformat() if pd.notnull(row["timestamp"]) else None,
            }
            for _, row in df.iterrows()
        ]
