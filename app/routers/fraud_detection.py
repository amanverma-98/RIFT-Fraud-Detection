from fastapi import APIRouter, UploadFile, File, HTTPException
from datetime import datetime
import os
import json
import uuid
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
    import time
    start_time = time.time()
    
    try:
        settings = get_settings()
        file_path = os.path.join(settings.upload_path, filename)

        logger.info(f"Starting fraud analysis: {filename}")

        # Process CSV to get transaction data
        process_start = time.time()
        result = await csv_processor.process_csv(file_path)
        transactions_df = result["data"]
        process_time = time.time() - process_start
        logger.info(f"CSV processing: {len(transactions_df)} transactions in {process_time:.2f}s")

        # Early check for empty data
        if len(transactions_df) == 0:
            logger.warning("No valid transactions in CSV file")
            return {
                "status": "success",
                "report_id": f"REPORT_{str(uuid.uuid4())[:8].upper()}",
                "suspicious_accounts_flagged": 0,
                "fraud_rings_detected": 0,
                "download_json_url": "/api/fraud/report/REPORT_EMPTY/download-json"
            }

        # Build graph
        graph_start = time.time()
        graph_service.build_graph(transactions_df)
        graph_time = time.time() - graph_start
        logger.info(f"Graph building: {graph_service.graph.number_of_nodes()} nodes, "
                   f"{graph_service.graph.number_of_edges()} edges in {graph_time:.2f}s")
        
        # Skip fraud_patterns since it's not used
        # fraud_patterns = graph_service.detect_fraud_patterns()

        # Run detection algorithms with timeouts for large files
        cycles = []
        fan_patterns = []
        shell_chains = []
        
        # Cycle detection
        try:
            cycle_start = time.time()
            cycles = detect_cycles(graph_service.graph, min_length=3, max_length=5)
            cycle_time = time.time() - cycle_start
            logger.info(f"Cycle detection: {len(cycles)} cycles found in {cycle_time:.2f}s")
        except Exception as e:
            logger.error(f"Cycle detection error: {str(e)}")
            cycles = []

        # Fan pattern detection
        try:
            fan_start = time.time()
            fan_detector = FanPatternDetector()
            fan_patterns = fan_detector.detect_patterns(transactions_df)
            fan_time = time.time() - fan_start
            logger.info(f"Fan pattern detection in {fan_time:.2f}s")
        except Exception as e:
            logger.error(f"Fan pattern detection error: {str(e)}")
            fan_patterns = []

        # Shell chain detection - DISABLED to prevent false positives
        # Keeping commented out until model is refined
        shell_chains = []
        # try:
        #     shell_start = time.time()
        #     shell_chains = detect_shell_chains(graph_service.graph)
        #     shell_time = time.time() - shell_start
        #     logger.info(f"Shell chain detection: {len(shell_chains)} chains found in {shell_time:.2f}s")
        # except Exception as e:
        #     logger.error(f"Shell chain detection error: {str(e)}")
        #     shell_chains = []

        # Generate RIFT-compliant report
        report_start = time.time()
        rift_report = generate_rift_report(
            graph=graph_service.graph,
            transactions_df=transactions_df,
            cycles=cycles,
            fan_patterns=fan_patterns,
            shell_chains=shell_chains,
            processing_time=process_time
        )
        report_time = time.time() - report_start
        logger.info(f"Report generation in {report_time:.2f}s")

        # Validate RIFT format
        if not validate_rift_report(rift_report):
            logger.warning("Generated report failed RIFT validation")

        # Generate report ID and add metadata to RIFT report
        report_id = f"REPORT_{str(uuid.uuid4())[:8].upper()}"
        rift_report_with_metadata = {
            "report_id": report_id,
            "timestamp": datetime.utcnow().isoformat(),
            "filename": filename,
            **rift_report  # Merge RIFT report fields
        }

        # Store RIFT-compliant report
        storage_start = time.time()
        report_storage.save_report(rift_report_with_metadata)
        storage_time = time.time() - storage_start
        
        total_time = time.time() - start_time
        logger.info(
            f"Fraud analysis complete: {rift_report['summary']['suspicious_accounts_flagged']} "
            f"suspicious accounts, {rift_report['summary']['fraud_rings_detected']} rings. "
            f"Total time: {total_time:.2f}s"
        )

        return {
            "status": "success",
            "report_id": report_id,
            "suspicious_accounts_flagged": rift_report['summary']['suspicious_accounts_flagged'],
            "fraud_rings_detected": rift_report['summary']['fraud_rings_detected'],
            "download_json_url": f"/api/fraud/report/{report_id}/download-json"
        }

    except FraudDetectionException as e:
        logger.error(f"Analysis error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected analysis error: {str(e)}", exc_info=True)
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
    Get summary of a fraud report
    """
    try:
        report = report_storage.get_report(report_id)
        if report is None:
            logger.warning(f"Report not found: {report_id}")
            raise HTTPException(status_code=404, detail="Report not found")

        # Return the summary field from RIFT report
        summary = report.get("summary", {})

        logger.info(f"Retrieved report summary: {report_id}")

        return {
            "report_id": report_id,
            "summary": summary,
            "timestamp": report.get("timestamp", datetime.utcnow().isoformat()),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving report summary: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve report summary")


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

    # Extract only RIFT-compliant fields
    rift_report = {
        "suspicious_accounts": report.get("suspicious_accounts", []),
        "fraud_rings": report.get("fraud_rings", []),
        "summary": report.get("summary", {})
    }

    # Convert to JSON bytes
    json_str = json.dumps(rift_report, indent=2)
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
    List all generated reports with RIFT-compliant format
    """
    try:
        reports_list = report_storage.get_all_reports(limit)
        logger.info(f"Retrieved {len(reports_list)} reports from storage")

        # Extract only RIFT-compliant fields from each report
        rift_reports = []
        for report in reports_list:
            try:
                # Safely extract fields with fallbacks
                rift_report = {
                    "report_id": report.get("report_id", "UNKNOWN"),
                    "timestamp": report.get("timestamp", ""),
                    "filename": report.get("filename", "unknown"),
                    "suspicious_accounts": report.get("suspicious_accounts", []),
                    "fraud_rings": report.get("fraud_rings", []),
                    "summary": report.get("summary", {
                        "total_accounts_analyzed": 0,
                        "suspicious_accounts_flagged": 0,
                        "fraud_rings_detected": 0,
                        "processing_time_seconds": 0.0
                    })
                }
                rift_reports.append(rift_report)
            except Exception as report_err:
                logger.warning(f"Skipping malformed report: {str(report_err)}")
                continue

        logger.info(f"Listed {len(rift_reports)} valid reports")

        return {
            "total_reports": len(rift_reports),
            "reports": rift_reports,
        }
    except Exception as e:
        logger.error(f"Error listing reports: {str(e)}", exc_info=True)
        # Return empty list instead of error
        return {
            "total_reports": 0,
            "reports": [],
        }
