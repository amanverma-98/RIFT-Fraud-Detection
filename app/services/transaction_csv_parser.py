import pandas as pd
from typing import List, Tuple, Dict
from datetime import datetime
from app.models.transaction_models import TransactionData, TransactionUploadError
from app.utils.logger import setup_logger
from app.utils.exceptions import CSVProcessingError, InvalidCSVFormat

logger = setup_logger(__name__)

# Required columns for transaction CSV
REQUIRED_COLUMNS = {"transaction_id", "sender_id", "receiver_id", "amount", "timestamp"}


class TransactionCSVParser:
    """Service for parsing and validating transaction CSV files"""

    @staticmethod
    def parse_csv(file_path: str) -> Tuple[List[TransactionData], List[TransactionUploadError]]:
        """
        Parse and validate a CSV file containing transactions

        Args:
            file_path: Path to the CSV file

        Returns:
            Tuple of (valid_transactions, errors)
        """
        try:
            logger.info(f"Parsing CSV file: {file_path}")

            # Read CSV
            df = pd.read_csv(file_path, dtype=str)
            logger.info(f"Loaded {len(df)} rows from CSV")

            # Validate columns
            TransactionCSVParser._validate_columns(df)

            # Parse rows
            valid_transactions = []
            errors = []

            for row_number, (_, row) in enumerate(df.iterrows(), start=2):  # Start at 2 (header is row 1)
                try:
                    transaction = TransactionCSVParser._parse_row(row)
                    valid_transactions.append(transaction)
                except ValueError as e:
                    error = TransactionUploadError(
                        row_number=row_number,
                        error=str(e),
                        values=row.to_dict(),
                    )
                    errors.append(error)
                    logger.warning(f"Row {row_number} parsing error: {str(e)}")

            logger.info(
                f"CSV parsing complete: {len(valid_transactions)} valid, "
                f"{len(errors)} rejected"
            )

            return valid_transactions, errors

        except CSVProcessingError:
            raise
        except InvalidCSVFormat:
            raise
        except Exception as e:
            logger.error(f"Unexpected error parsing CSV: {str(e)}")
            raise CSVProcessingError(f"Failed to parse CSV: {str(e)}")

    @staticmethod
    def _validate_columns(df: pd.DataFrame) -> None:
        """Validate that all required columns are present"""
        missing_columns = REQUIRED_COLUMNS - set(df.columns)
        if missing_columns:
            error_msg = f"Missing required columns: {missing_columns}"
            logger.error(error_msg)
            raise InvalidCSVFormat(error_msg)

        logger.info("CSV columns validated successfully")

    @staticmethod
    def _parse_row(row: pd.Series) -> TransactionData:
        """
        Parse a single CSV row into a TransactionData object

        Args:
            row: Pandas Series representing a CSV row

        Returns:
            TransactionData object
        """
        try:
            # Extract and clean values
            transaction_id = str(row.get("transaction_id", "")).strip()
            sender_id = str(row.get("sender_id", "")).strip()
            receiver_id = str(row.get("receiver_id", "")).strip()

            # Parse amount
            try:
                amount = float(row.get("amount", 0))
            except (ValueError, TypeError):
                raise ValueError(f"Invalid amount: '{row.get('amount')}' is not a valid number")

            # Parse timestamp
            timestamp_str = row.get("timestamp", "")
            try:
                timestamp = TransactionCSVParser._parse_timestamp(timestamp_str)
            except ValueError as e:
                raise ValueError(f"Invalid timestamp: {str(e)}")

            # Create transaction object (validation happens in Pydantic model)
            return TransactionData(
                transaction_id=transaction_id,
                sender_id=sender_id,
                receiver_id=receiver_id,
                amount=amount,
                timestamp=timestamp,
            )

        except ValueError as e:
            raise
        except Exception as e:
            raise ValueError(f"Failed to parse row: {str(e)}")

    @staticmethod
    def _parse_timestamp(timestamp_str: str) -> datetime:
        """
        Parse timestamp string to datetime

        Supports multiple formats:
        - ISO format: 2024-01-15T10:30:00
        - ISO with Z: 2024-01-15T10:30:00Z
        - Standard format: 2024-01-15 10:30:00
        - Date only: 2024-01-15

        Args:
            timestamp_str: Timestamp string

        Returns:
            datetime object
        """
        if not timestamp_str or not str(timestamp_str).strip():
            raise ValueError("Timestamp cannot be empty")

        timestamp_str = str(timestamp_str).strip()
        formats = [
            "%Y-%m-%dT%H:%M:%S.%f",      # ISO with microseconds
            "%Y-%m-%dT%H:%M:%S",         # ISO format
            "%Y-%m-%dT%H:%M:%SZ",        # ISO with Z
            "%Y-%m-%d %H:%M:%S.%f",      # Standard with microseconds
            "%Y-%m-%d %H:%M:%S",         # Standard format
            "%Y-%m-%d",                  # Date only
        ]

        # Try to parse with different formats
        for fmt in formats:
            try:
                return datetime.strptime(timestamp_str, fmt)
            except ValueError:
                continue

        # If no format matched, raise error
        raise ValueError(
            f"'{timestamp_str}' does not match any supported format. "
            f"Supported formats: YYYY-MM-DD[T ]HH:MM:SS[.ffffff][Z]"
        )

    @staticmethod
    def calculate_summary(transactions: List[TransactionData]) -> Dict:
        """
        Calculate summary statistics from transactions

        Args:
            transactions: List of parsed transactions

        Returns:
            Dictionary with summary statistics
        """
        unique_senders = set()
        unique_receivers = set()

        for transaction in transactions:
            unique_senders.add(transaction.sender_id)
            unique_receivers.add(transaction.receiver_id)

        unique_accounts = len(unique_senders | unique_receivers)  # Union of both sets

        logger.info(
            f"Summary: {len(transactions)} transactions, "
            f"{unique_accounts} unique accounts, "
            f"{len(unique_senders)} senders, {len(unique_receivers)} receivers"
        )

        return {
            "total_transactions": len(transactions),
            "unique_accounts": unique_accounts,
            "unique_senders": len(unique_senders),
            "unique_receivers": len(unique_receivers),
        }
