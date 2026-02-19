class FraudDetectionException(Exception):
    """Base exception for fraud detection system"""
    pass


class CSVProcessingError(FraudDetectionException):
    """Exception raised during CSV processing"""
    pass


class InvalidCSVFormat(CSVProcessingError):
    """Exception raised when CSV format is invalid"""
    pass


class FileUploadError(FraudDetectionException):
    """Exception raised during file upload"""
    pass


class GraphDetectionError(FraudDetectionException):
    """Exception raised during graph analysis"""
    pass


class ReportGenerationError(FraudDetectionException):
    """Exception raised during report generation"""
    pass
