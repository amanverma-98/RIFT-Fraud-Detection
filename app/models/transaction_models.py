from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import List, Optional


class TransactionData(BaseModel):
    """Individual transaction data model"""
    transaction_id: str = Field(..., description="Unique transaction identifier")
    sender_id: str = Field(..., description="ID of the account sending money")
    receiver_id: str = Field(..., description="ID of the account receiving money")
    amount: float = Field(..., gt=0, description="Transaction amount (must be > 0)")
    timestamp: datetime = Field(..., description="Transaction timestamp")

    class Config:
        from_attributes = True

    @validator("transaction_id")
    def validate_transaction_id(cls, v):
        if not v or not str(v).strip():
            raise ValueError("transaction_id cannot be empty")
        return str(v).strip()

    @validator("sender_id")
    def validate_sender_id(cls, v):
        if not v or not str(v).strip():
            raise ValueError("sender_id cannot be empty")
        return str(v).strip()

    @validator("receiver_id")
    def validate_receiver_id(cls, v):
        if not v or not str(v).strip():
            raise ValueError("receiver_id cannot be empty")
        return str(v).strip()

    @validator("amount")
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError("amount must be greater than 0")
        try:
            return float(v)
        except (ValueError, TypeError):
            raise ValueError("amount must be a valid number")


class UploadTransactionsSummary(BaseModel):
    """Response model for transaction upload"""
    status: str = Field(default="success", description="Upload status")
    total_transactions: int = Field(..., description="Total number of valid transactions")
    unique_accounts: int = Field(..., description="Number of unique sender and receiver accounts")
    unique_senders: int = Field(..., description="Number of unique senders")
    unique_receivers: int = Field(..., description="Number of unique receivers")
    rejected_rows: int = Field(default=0, description="Number of rows with errors")
    errors: List[dict] = Field(default_factory=list, description="Error details for rejected rows")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Upload timestamp")
    upload_id: str = Field(..., description="Unique identifier for this upload")

    class Config:
        from_attributes = True


class TransactionUploadError(BaseModel):
    """Error details for a rejected transaction"""
    row_number: int = Field(..., description="Row number in CSV (1-indexed)")
    error: str = Field(..., description="Error message")
    values: Optional[dict] = Field(None, description="Raw values from the row")


class TransactionBatch(BaseModel):
    """Response for retrieved transaction batch"""
    upload_id: str
    transaction_count: int
    transactions: List[TransactionData]
    created_at: datetime
