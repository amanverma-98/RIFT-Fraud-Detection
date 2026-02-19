from pydantic import BaseModel, Field
from typing import List, Dict, Any


class TransactionBase(BaseModel):
    """Base transaction schema"""
    source: str = Field(..., description="Source account/entity")
    destination: str = Field(..., description="Destination account/entity")
    amount: float = Field(..., gt=0, description="Transaction amount")


class TransactionCreate(TransactionBase):
    """Transaction creation schema"""
    pass


class Transaction(TransactionBase):
    """Transaction response schema"""
    class Config:
        from_attributes = True


class CSVUploadResponse(BaseModel):
    """Response schema for CSV upload"""
    filename: str
    total_records: int
    processed_records: int
    failed_records: int
    upload_timestamp: str
    status: str = "success"


class FraudNode(BaseModel):
    """Fraudulent node in graph"""
    node_id: str
    fraud_score: float
    transaction_count: int
    total_amount: float


class FraudPattern(BaseModel):
    """Detected fraud pattern"""
    pattern_id: str
    nodes: List[FraudNode]
    edges: List[Dict[str, Any]]
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    confidence: float


class FraudReport(BaseModel):
    """Fraud detection report"""
    report_id: str
    timestamp: str
    total_nodes: int
    total_edges: int
    fraud_nodes_count: int
    fraud_patterns: List[FraudPattern]
    suspicious_transactions: List[Dict[str, Any]]
    summary: Dict[str, Any]


class HealthCheckResponse(BaseModel):
    """Health check response"""
    status: str
    version: str
    app_name: str
