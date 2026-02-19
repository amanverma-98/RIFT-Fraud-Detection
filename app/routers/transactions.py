from fastapi import APIRouter, UploadFile, File, HTTPException
import os
import uuid
from app.utils.logger import setup_logger
from app.utils.exceptions import FraudDetectionException, CSVProcessingError, InvalidCSVFormat
from app.services.transaction_csv_parser import TransactionCSVParser
from app.services.transaction_store import get_transaction_store
from app.models.transaction_models import (
    UploadTransactionsSummary,
    TransactionUploadError,
    TransactionBatch,
)
from app.config import get_settings

logger = setup_logger(__name__)
router = APIRouter(prefix="/api/transactions", tags=["transactions"])

# Get the transaction data store
transaction_store = get_transaction_store()


@router.post("/upload-transactions", response_model=UploadTransactionsSummary, status_code=201)
async def upload_transactions(file: UploadFile = File(...)):
    """
    Upload and parse a CSV file containing transactions.

    Expected CSV format with required columns:
    - transaction_id: Unique transaction identifier
    - sender_id: Account sending money
    - receiver_id: Account receiving money
    - amount: Transaction amount (numeric, must be > 0)
    - timestamp: Transaction timestamp (multiple formats supported)

    Supported timestamp formats:
    - ISO format: 2024-01-15T10:30:00
    - ISO with Z: 2024-01-15T10:30:00Z
    - Standard format: 2024-01-15 10:30:00
    - Date only: 2024-01-15

    Returns:
        UploadTransactionsSummary: Upload status with statistics

    Status Codes:
        201: Created - File successfully processed
        400: Bad Request - Invalid CSV format or content
        422: Unprocessable Entity - File validation failed
        500: Internal Server Error - Unexpected error
    """
    temp_file_path = None

    try:
        settings = get_settings()
        logger.info(f"Received transaction upload: {file.filename}")

        # Validate file extension
        if not file.filename.endswith(".csv"):
            logger.error(f"Invalid file extension: {file.filename}")
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Expected CSV file, got {file.filename}",
            )

        # Create temp file path
        temp_dir = settings.upload_path
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)

        temp_file_path = os.path.join(temp_dir, f"{uuid.uuid4()}_{file.filename}")

        # Save uploaded file
        logger.info(f"Saving uploaded file to: {temp_file_path}")
        with open(temp_file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        # Check file size
        file_size_mb = os.path.getsize(temp_file_path) / (1024 * 1024)
        if file_size_mb > settings.max_upload_size_mb:
            logger.error(f"File too large: {file_size_mb}MB > {settings.max_upload_size_mb}MB")
            raise HTTPException(
                status_code=413,
                detail=f"File too large ({file_size_mb:.2f}MB). Maximum size: {settings.max_upload_size_mb}MB",
            )

        logger.info(f"File saved. Size: {file_size_mb:.2f}MB")

        # Parse CSV
        logger.info("Parsing CSV file...")
        valid_transactions, errors = TransactionCSVParser.parse_csv(temp_file_path)

        # Calculate summary
        summary = TransactionCSVParser.calculate_summary(valid_transactions)

        # Generate upload ID
        upload_id = transaction_store.add_batch(valid_transactions)

        logger.info(
            f"Upload complete: {len(valid_transactions)} valid, "
            f"{len(errors)} rejected (Upload ID: {upload_id})"
        )

        # Build response
        response = UploadTransactionsSummary(
            status="success",
            total_transactions=summary["total_transactions"],
            unique_accounts=summary["unique_accounts"],
            unique_senders=summary["unique_senders"],
            unique_receivers=summary["unique_receivers"],
            rejected_rows=len(errors),
            errors=[error.dict() for error in errors] if errors else [],
            upload_id=upload_id,
        )

        return response

    except InvalidCSVFormat as e:
        logger.error(f"Invalid CSV format: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Invalid CSV format: {str(e)}")

    except CSVProcessingError as e:
        logger.error(f"CSV processing error: {str(e)}")
        raise HTTPException(status_code=400, detail=f"CSV processing error: {str(e)}")

    except FraudDetectionException as e:
        logger.error(f"Application error: {str(e)}")
        raise HTTPException(status_code=422, detail=str(e))

    except Exception as e:
        logger.error(f"Unexpected error during upload: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal server error during file processing",
        )

    finally:
        # Clean up temporary file
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
                logger.info(f"Cleaned up temp file: {temp_file_path}")
            except Exception as e:
                logger.warning(f"Failed to clean up temp file: {str(e)}")


@router.get("/batch/{upload_id}", response_model=TransactionBatch)
async def get_transaction_batch(upload_id: str):
    """
    Retrieve a previously uploaded transaction batch.

    Args:
        upload_id: The unique identifier returned from upload endpoint

    Returns:
        TransactionBatch: The batch with all transactions

    Status Codes:
        200: OK - Batch found and returned
        404: Not Found - Batch with this ID doesn't exist
    """
    logger.info(f"Retrieving batch: {upload_id}")

    batch = transaction_store.get_batch(upload_id)
    if not batch:
        logger.warning(f"Batch not found: {upload_id}")
        raise HTTPException(
            status_code=404,
            detail=f"Batch {upload_id} not found",
        )

    return TransactionBatch(
        upload_id=batch["upload_id"],
        transaction_count=batch["transaction_count"],
        transactions=batch["transactions"],
        created_at=batch["created_at"],
    )


@router.get("/batches")
async def list_transaction_batches():
    """
    List all stored transaction batches.

    Returns statistics about each batch currently in memory.

    Status Codes:
        200: OK - List returned (may be empty)
    """
    logger.info("Listing all transaction batches")

    stats = transaction_store.get_statistics()

    return {
        "status": "success",
        "total_batches": stats["total_batches"],
        "total_transactions": stats["total_transactions"],
        "batches": stats["batches"],
    }


@router.delete("/batch/{upload_id}")
async def delete_transaction_batch(upload_id: str):
    """
    Delete a transaction batch from memory.

    Args:
        upload_id: The batch ID to delete

    Returns:
        Deletion status

    Status Codes:
        200: OK - Batch deleted
        404: Not Found - Batch doesn't exist
    """
    logger.info(f"Deleting batch: {upload_id}")

    deleted = transaction_store.delete_batch(upload_id)
    if not deleted:
        logger.warning(f"Batch not found for deletion: {upload_id}")
        raise HTTPException(
            status_code=404,
            detail=f"Batch {upload_id} not found",
        )

    return {
        "status": "success",
        "message": f"Batch {upload_id} deleted",
        "upload_id": upload_id,
    }


@router.post("/clear-all")
async def clear_all_batches():
    """
    Clear all transaction batches from memory.

    WARNING: This operation is destructive and cannot be undone.

    Returns:
        Number of batches cleared

    Status Codes:
        200: OK - All batches cleared
    """
    logger.warning("Clearing all transaction batches")

    count = transaction_store.clear_all()

    return {
        "status": "success",
        "message": "All transaction batches cleared",
        "batches_cleared": count,
    }
