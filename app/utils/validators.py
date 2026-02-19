import os
from app.config import get_settings
from app.utils.exceptions import FileUploadError, InvalidCSVFormat
import pandas as pd


def validate_csv_file(filename: str) -> bool:
    """Validate if file is a CSV"""
    settings = get_settings()
    _, ext = os.path.splitext(filename)
    if ext.lower() not in settings.allowed_csv_extensions:
        raise FileUploadError(f"File extension {ext} not allowed. Allowed: {settings.allowed_csv_extensions}")
    return True


def validate_csv_content(df: pd.DataFrame) -> bool:
    """Validate CSV content has required columns"""
    required_columns = {"transaction_id", "sender_id", "receiver_id", "amount", "timestamp"}
    if not required_columns.issubset(set(df.columns)):
        missing = required_columns - set(df.columns)
        raise InvalidCSVFormat(f"Missing required columns: {missing}")
    return True


def validate_numeric_column(df: pd.DataFrame, column: str) -> bool:
    """Validate that a column contains numeric values"""
    try:
        pd.to_numeric(df[column], errors="coerce")
        return True
    except Exception as e:
        raise InvalidCSVFormat(f"Column '{column}' must contain numeric values: {str(e)}")
