import uuid
from datetime import datetime
from typing import Dict, List, Optional
from app.models.transaction_models import TransactionData
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class TransactionDataStore:
    """In-memory transaction data store"""

    def __init__(self):
        """Initialize the data store"""
        self._store: Dict[str, Dict] = {}
        logger.info("TransactionDataStore initialized")

    def add_batch(self, transactions: List[TransactionData]) -> str:
        """
        Add a batch of transactions to the store

        Args:
            transactions: List of validated transaction objects

        Returns:
            upload_id: Unique identifier for this batch
        """
        upload_id = str(uuid.uuid4())

        batch = {
            "upload_id": upload_id,
            "transactions": transactions,
            "created_at": datetime.utcnow(),
            "transaction_count": len(transactions),
        }

        self._store[upload_id] = batch
        logger.info(
            f"Batch {upload_id} stored: {len(transactions)} transactions"
        )

        return upload_id

    def get_batch(self, upload_id: str) -> Optional[Dict]:
        """
        Retrieve a transaction batch by upload_id

        Args:
            upload_id: Unique batch identifier

        Returns:
            Batch data or None if not found
        """
        batch = self._store.get(upload_id)
        if batch:
            logger.info(f"Retrieved batch {upload_id}")
        else:
            logger.warning(f"Batch {upload_id} not found")
        return batch

    def get_all_batches(self) -> Dict[str, Dict]:
        """
        Get all stored batches

        Returns:
            Dictionary of all batches
        """
        logger.info(f"Retrieved {len(self._store)} batches")
        return self._store.copy()

    def delete_batch(self, upload_id: str) -> bool:
        """
        Delete a transaction batch

        Args:
            upload_id: Batch identifier

        Returns:
            True if deleted, False if not found
        """
        if upload_id in self._store:
            del self._store[upload_id]
            logger.info(f"Deleted batch {upload_id}")
            return True
        logger.warning(f"Attempted to delete non-existent batch {upload_id}")
        return False

    def clear_all(self) -> int:
        """
        Clear all stored batches

        Returns:
            Number of batches cleared
        """
        count = len(self._store)
        self._store.clear()
        logger.info(f"Cleared {count} transaction batches")
        return count

    def get_statistics(self) -> Dict:
        """
        Get statistics about stored transactions

        Returns:
            Statistics dictionary
        """
        total_transactions = sum(
            batch["transaction_count"] for batch in self._store.values()
        )
        total_batches = len(self._store)

        stats = {
            "total_batches": total_batches,
            "total_transactions": total_transactions,
            "batches": [
                {
                    "upload_id": batch["upload_id"],
                    "transaction_count": batch["transaction_count"],
                    "created_at": batch["created_at"].isoformat(),
                }
                for batch in self._store.values()
            ],
        }

        logger.info(f"Statistics: {total_batches} batches, {total_transactions} transactions")
        return stats


# Global singleton instance
_transaction_store: Optional[TransactionDataStore] = None


def get_transaction_store() -> TransactionDataStore:
    """Get or create the global transaction store instance"""
    global _transaction_store
    if _transaction_store is None:
        _transaction_store = TransactionDataStore()
    return _transaction_store
