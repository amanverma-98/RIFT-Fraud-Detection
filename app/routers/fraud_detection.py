from fastapi import APIRouter, UploadFile, File, HTTPException
from datetime import datetime
import os
import json
from io import BytesIO
from fastapi.responses import StreamingResponse
from app.utils.logger import setup_logger
from app.utils.exceptions import FraudDetectionException
from app.services.csv_processor import CSVProcessor
from app.services.graph_detection import GraphDetectionService
from app.services.report_generator import ReportGenerator
from app.services.rift_report_generator import generate_rift_report, validate_rift_report
from app.services.report_storage import ReportStorage
from app.services.cycle_detection import detect_cycles
from app.services.fan_pattern_detection import FanPatternDetector
from app.services.shell_chain_detection import detect_shell_chains
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
    Upload a CSV file containing transaction data (RIFT Format).

    Expected CSV format (EXACT):
    - transaction_id: Unique identifier for the transaction (string)
    - sender_id: Account ID of sender (string)
    - receiver_id: Account ID of receiver (string)
    - amount: Transaction amount in currency units (float)
    - timestamp: DateTime in format YYYY-MM-DD HH:MM:SS
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
    Analyze a previously uploaded CSV file for money muling patterns.

    Detects:
    - Circular fund routing (cycles 3-5 nodes)
    - Smurfing patterns (fan-in/fan-out 10+ accounts)
    - Shell networks (3+ hop chains with low-activity intermediaries)

    Args:
        filename: Name of the uploaded CSV file

    Returns:
        {
          "status": "success",
          "report_id": "REPORT_XXX",
          "suspicious_accounts_flagged": 15,
          "fraud_rings_detected": 4,
          "download_json_url": "/api/fraud/report/REPORT_XXX/download-json"
        }
    """
    try:
        settings = get_settings()
        file_path = os.path.join(settings.upload_path, filename)

        logger.info(f"Starting fraud analysis: {filename}")

        # Process CSV to get transaction data
        result = await csv_processor.process_csv(file_path)
        transactions_df = result["data"]

        # Build graph
        graph_service.build_graph(transactions_df)
        fraud_patterns = graph_service.detect_fraud_patterns()

        # Run all detection algorithms for RIFT compliance
        cycles = detect_cycles(graph_service.graph, min_length=3, max_length=5)

        fan_detector = FanPatternDetector()
        fan_patterns = fan_detector.detect_patterns(transactions_df)

        shell_chains = detect_shell_chains(graph_service.graph)

        # Generate RIFT-compliant report
        rift_report = generate_rift_report(
            graph=graph_service.graph,
            transactions_df=transactions_df,
            cycles=cycles,
            fan_patterns=fan_patterns,
            shell_chains=shell_chains,
            processing_time=result.get("processing_time", 0.0)
        )

        # Validate RIFT format
        if not validate_rift_report(rift_report):
            logger.warning("Generated report failed RIFT validation")

        # Also generate standard report for storage
        standard_report = report_generator.generate_report(
            graph_service.graph, fraud_patterns, filename
        )

        # Store standard report
        report_storage.save_report(standard_report)

        logger.info(
            f"Fraud analysis complete: {rift_report['summary']['suspicious_accounts_flagged']} "
            f"suspicious accounts, {rift_report['summary']['fraud_rings_detected']} rings"
        )

        return {
            "status": "success",
            "report_id": standard_report.get("report_id", "REPORT_001"),
            "suspicious_accounts_flagged": rift_report['summary']['suspicious_accounts_flagged'],
            "fraud_rings_detected": rift_report['summary']['fraud_rings_detected'],
            "download_json_url": f"/api/fraud/report/{standard_report.get('report_id', 'REPORT_001')}/download-json"
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


@router.get("/report/{report_id}/download-json")
async def download_report_json(report_id: str):
    """
    Download fraud detection report as RIFT-compliant JSON file.

    Returns the report in exact RIFT format:
    {
      "suspicious_accounts": [...],
      "fraud_rings": [...],
      "summary": {...}
    }
    """
    report = report_storage.get_report(report_id)
    if report is None:
        logger.warning(f"Report not found for download: {report_id}")
        raise HTTPException(status_code=404, detail="Report not found")

    logger.info(f"Downloading report as JSON: {report_id}")

    # Convert to JSON bytes
    json_str = json.dumps(report, indent=2)
    json_bytes = json_str.encode('utf-8')

    return StreamingResponse(
        iter([json_bytes]),
        media_type="application/json",
        headers={
            "Content-Disposition": f"attachment; filename=fraud_report_{report_id}.json"
        }
    )


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
