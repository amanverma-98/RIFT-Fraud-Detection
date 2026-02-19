from fastapi import APIRouter, UploadFile, File, HTTPException
from datetime import datetime
import os
from app.utils.logger import setup_logger
from app.utils.exceptions import FraudDetectionException
from app.services.csv_processor import CSVProcessor
from app.services.graph_detection import GraphDetectionService
from app.services.report_generator import ReportGenerator
from app.services.report_storage import ReportStorage
from app.models.schemas import CSVUploadResponse, FraudReport
from app.config import get_settings

logger = setup_logger(__name__)
router = APIRouter(prefix="/api/fraud", tags=["fraud-detection"])

# Initialize services
csv_processor = CSVProcessor()
graph_service = GraphDetectionService()
report_generator = ReportGenerator()
report_storage = ReportStorage()  # Persistent SQLite storage


@router.post("/upload", response_model=CSVUploadResponse)
async def upload_csv(file: UploadFile = File(...)):
    """
    Upload a CSV file containing transaction data

    Expected CSV format:
    - transaction_id: Unique identifier for the transaction (string)
    - sender_id: Account/entity sending money (string)
    - receiver_id: Account/entity receiving money (string)
    - amount: Transaction amount (numeric)
    - timestamp: Transaction timestamp in ISO 8601 format (e.g., "2026-02-19T11:56:10.008Z")
    """
    try:
        settings = get_settings()
        logger.info(f"Received file upload: {file.filename}")

        # Save uploaded file
        file_path = os.path.join(settings.upload_path, file.filename)
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        # Process CSV
        result = await csv_processor.process_csv(file_path)

        response = CSVUploadResponse(
            filename=result["filename"],
            total_records=result["total_records"],
            processed_records=result["processed_records"],
            failed_records=result["failed_records"],
            upload_timestamp=result["timestamp"],
            status="success",
        )

        logger.info(f"CSV upload successful: {file.filename}")
        return response

    except FraudDetectionException as e:
        logger.error(f"Upload error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected upload error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process upload")


@router.post("/analyze")
async def analyze_fraud(filename: str):
    """
    Analyze a previously uploaded CSV file for fraud patterns

    Args:
        filename: Name of the uploaded CSV file
    """
    try:
        settings = get_settings()
        file_path = os.path.join(settings.upload_path, filename)

        logger.info(f"Starting fraud analysis: {filename}")

        # Process CSV to get transaction data
        result = await csv_processor.process_csv(file_path)
        transactions_df = result["data"]

        # Build graph and detect fraud
        graph_service.build_graph(transactions_df)
        fraud_patterns = graph_service.detect_fraud_patterns()

        # Generate report
        report = report_generator.generate_report(
            graph_service.graph, fraud_patterns, filename
        )

        # Save report to persistent storage
        report_storage.save_report(report)

        logger.info(f"Fraud analysis complete: {report['report_id']}")

        return {
            "status": "success",
            "report_id": report["report_id"],
            "message": "Fraud analysis completed",
        }

    except FraudDetectionException as e:
        logger.error(f"Analysis error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to analyze fraud")


@router.get("/report/{report_id}")
async def get_report(report_id: str):
    """
    Retrieve a previously generated fraud detection report

    Args:
        report_id: ID of the report to retrieve
    """
    report = report_storage.get_report(report_id)
    if report is None:
        logger.warning(f"Report not found: {report_id}")
        raise HTTPException(status_code=404, detail="Report not found")

    logger.info(f"Retrieved report: {report_id}")
    return report


@router.get("/report/{report_id}/summary")
async def get_report_summary(report_id: str):
    """
    Get a human-readable summary of a fraud report
    """
    report = report_storage.get_report(report_id)
    if report is None:
        logger.warning(f"Report not found: {report_id}")
        raise HTTPException(status_code=404, detail="Report not found")

    summary = report_generator.format_report_summary(report)
    logger.info(f"Retrieved report summary: {report_id}")

    return {
        "report_id": report_id,
        "summary": summary,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/reports")
async def list_reports(limit: int = 10):
    """
    List all generated reports
    """
    reports_list = report_storage.get_all_reports(limit)
    logger.info(f"Listed {len(reports_list)} reports")

    return {
        "total_reports": report_storage.get_report_count(),
        "reports": reports_list,
    }
