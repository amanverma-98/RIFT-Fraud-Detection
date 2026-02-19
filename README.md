# Money Muling Detection System - RIFT 2026 Hackathon

**Graph-based financial crime detection engine for identifying money muling networks**

Built for the RIFT 2026 Hackathon - Graph Theory / Financial Crime Detection Track

---

## 📋 Table of Contents

- [Quick Start](#quick-start)
- [Tech Stack](#tech-stack)
- [System Architecture](#system-architecture)
- [Detection Algorithms](#detection-algorithms)
- [API Documentation](#api-documentation)
- [Installation & Deployment](#installation--deployment)
- [Performance Metrics](#performance-metrics)
- [Known Limitations](#known-limitations)
- [Team Members](#team-members)

---

## 🚀 Quick Start

### Local Development

```bash
# Clone repository
git clone [your-repo-url]
cd fraud-detection-system

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run application
python run.py
```

Application available at: **http://localhost:10000**

### Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f fraud-detection
```

---

## 🏗️ Tech Stack

| Component | Technology |
|-----------|-----------|
| Web Framework | FastAPI |
| Graph Analysis | NetworkX |
| Data Processing | Pandas, NumPy |
| Data Validation | Pydantic |
| Database (Reports) | SQLite |
| Server | Uvicorn (ASGI) |
| Deployment | Docker, Render |

---

## 📐 System Architecture

```
fraud-detection-system/
├── app/
│   ├── main.py                      # FastAPI application
│   ├── config.py                    # Configuration settings
│   ├── routers/
│   │   ├── fraud_detection.py      # API endpoints (RIFT compliance)
│   │   ├── health.py               # Health check
│   │   └── transactions.py         # Transaction endpoints
│   ├── services/
│   │   ├── csv_processor.py        # CSV parsing (YYYY-MM-DD HH:MM:SS)
│   │   ├── graph_detection.py      # Graph construction (O(E))
│   │   ├── cycle_detection.py      # Cycle detection (3-5 length)
│   │   ├── fan_pattern_detection.py # Smurfing patterns (10+ threshold)
│   │   ├── shell_chain_detection.py # Shell networks (3+ hops)
│   │   ├── suspicion_scoring.py    # Unified scoring (0-100)
│   │   ├── compliance_reporting.py # Standard report generation
│   │   ├── rift_report_generator.py # RIFT-compliant JSON output
│   │   └── report_storage.py       # SQLite persistence
│   ├── models/
│   │   └── schemas.py              # Pydantic models
│   ├── middleware/
│   │   └── error_handler.py        # Error handling
│   ├── utils/
│   │   ├── logger.py               # Logging
│   │   ├── exceptions.py           # Custom exceptions
│   │   └── validators.py           # Input validation
│   └── __init__.py
├── logs/                            # Application logs
├── uploads/                         # Uploaded CSV files
├── .env.example                     # Environment template
├── .gitignore                       # Git rules
├── requirements.txt                 # Dependencies
├── Dockerfile                       # Docker image
├── docker-compose.yml               # Docker Compose
├── run.py                           # Development runner
└── README.md
```

---

## 🔍 Detection Algorithms

### 1. Circular Fund Routing (Cycles)

**Pattern**: Money flows in loops through accounts → obscures origin

**Example**: A → B → C → A

**Implementation**:
- Detects cycles of length **3, 4, or 5 nodes**
- Algorithm: DFS-based cycle detection
- **Time Complexity**: O(V + E)
- **Space Complexity**: O(V + E)
- Output Pattern: `cycle_length_3`, `cycle_length_4`, `cycle_length_5`
- Key: All accounts in detected cycle → same fraud ring

---

### 2. Smurfing Patterns (Fan-in / Fan-out)

**Pattern**: Breaks large transactions into small deposits to avoid thresholds

**Implementation**:
- **Fan-in**: 10+ accounts send to 1 receiver
- **Fan-out**: 1 sender sends to 10+ receivers
- **Temporal Window**: 72-hour window for related transactions
- Algorithm: Sliding window aggregation
- **Time Complexity**: O(N log N) sorting + O(N) window scan
- Output Patterns: `fan_in_pattern`, `fan_out_pattern`

---

### 3. Layered Shell Networks

**Pattern**: Money passes through low-activity intermediate accounts

**Implementation**:
- Detects chains of **3+ hops** (source → intermediaries → destination)
- Intermediate nodes have **2-3 total transactions**
- Algorithm: BFS with aggressive pruning
- **Time Complexity**: O(V + E) per search
- Output Pattern: `shell_chain_pattern`

---

### 4. Velocity Analysis

**Pattern**: Unusually high transaction frequency

**Implementation**:
- Threshold: **≥10 transactions** per account
- Identifies accounts with rapid transaction cycling
- Output Pattern: `high_velocity`

---

## 📊 Suspicion Score Methodology

### Score Calculation (Normalized 0-100)

| Pattern Type | Weight | Condition |
|-------------|--------|-----------|
| Cycle Participation | +40 | Account in 3-5 node cycle |
| Fan-in Pattern | +30 | Receives from ≥10 accounts (72h window) |
| Fan-out Pattern | +30 | Sends to ≥10 accounts (72h window) |
| Shell Chain | +20 | Part of 3+ hop chain w/ low-activity intermediates |
| High Velocity | +10 | ≥10 transactions in dataset |

**Raw Score**: Sum of triggered weights (max 130)
**Normalized Score**: min(100, (raw / 130) × 100)

---

## 📤 Output Format (RIFT Specification)

### Exact JSON Structure Required

```json
{
  "suspicious_accounts": [
    {
      "account_id": "ACC_00123",
      "suspicion_score": 87.5,
      "detected_patterns": ["cycle_length_3", "high_velocity"],
      "ring_id": "RING_001"
    }
  ],
  "fraud_rings": [
    {
      "ring_id": "RING_001",
      "member_accounts": ["ACC_00123", "ACC_00456"],
      "pattern_type": "cycle",
      "risk_score": 95.3
    }
  ],
  "summary": {
    "total_accounts_analyzed": 500,
    "suspicious_accounts_flagged": 15,
    "fraud_rings_detected": 4,
    "processing_time_seconds": 2.3
  }
}
```

---

## 🔌 API Documentation

### 1. Upload Transact CSV

**Endpoint**: `POST /api/fraud/upload`

**CSV Format** (RIFT Specification):
```
transaction_id,sender_id,receiver_id,amount,timestamp
TXN001,Alice,Bob,1000.00,2026-02-19 10:00:00
TXN002,Bob,Charlie,1500.00,2026-02-19 10:15:00
```

**Request**:
```bash
curl -X POST -F "file=@transactions.csv" http://localhost:10000/api/fraud/upload
```

**Response**:
```json
{
  "filename": "transactions.csv",
  "total_records": 30,
  "processed_records": 30,
  "failed_records": 0,
  "upload_timestamp": "2026-02-19T10:30:00",
  "status": "success"
}
```

---

### 2. Analyze Uploaded CSV

**Endpoint**: `POST /api/fraud/analyze?filename=transactions.csv`

**Response**:
```json
{
  "status": "success",
  "report_id": "REPORT_001",
  "suspicious_accounts_flagged": 15,
  "fraud_rings_detected": 4,
  "download_json_url": "/api/fraud/report/REPORT_001/download-json"
}
```

**Processing Time**: < 30 seconds (for up to 10K transactions)

---

### 3. Get Report (Standard Format)

**Endpoint**: `GET /api/fraud/report/{report_id}`

Returns comprehensive report with all metadata.

---

### 4. Download RIFT JSON

**Endpoint**: `GET /api/fraud/report/{report_id}/download-json`

Downloads report in exact RIFT-compliant JSON format.

```bash
curl -O http://localhost:10000/api/fraud/report/REPORT_001/download-json
```

---

### 5. Health Check

**Endpoint**: `GET /api/health`

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "app_name": "Fraud Detection System"
}
```

---

## 📦 Installation & Deployment

### Local Development

```bash
# Virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Run application
python run.py
```

Visit: http://localhost:10000

### Docker

```bash
# Build image
docker build -t fraud-detection-system .

# Run container
docker-compose up -d

# View logs
docker-compose logs -f fraud-detection

# Stop container
docker-compose down
```

### Deploy to Render

1. **Push to GitHub**
   ```bash
   git push origin main
   ```

2. **Create Web Service on Render**
   - Connect GitHub repository
   - Set build command: `pip install -r requirements.txt`
   - Set start command: `uvicorn app.main:app --host 0.0.0.0 --port 10000`
   - Environment: Set PORT=10000

3. **Access** via provided Render URL

---

## 📈 Performance Metrics

| Metric | Target | Implementation |
|--------|--------|-----------------|
| Processing Time (10K txn) | ≤ 30 seconds | Streaming + efficient algorithms |
| Precision | ≥ 70% | Weighted pattern detection |
| Recall | ≥ 60% | Multiple algorithm coverage |
| False Positive Control | Minimize | Heuristic thresholds + clustering |

---

## ⚠️ Known Limitations

### 1. False Positive Sensitivity
- **Issue**: High-volume merchants may be flagged due to transaction volume
- **Mitigation**: Implement merchant whitelist in production
- **Future**: ML-based legitimate account classifier

### 2. Fixed Temporal Windows
- **Issue**: 72-hour window for smurfing is rigid
- **Assumption**: Criminal networks move funds quickly
- **Limitation**: Sophisticated laundering may exceed 72 hours
- **Future**: Adaptive windows based on account profiles

### 3. Shell Node Heuristics
- **Issue**: 2-3 transaction threshold for shell nodes is heuristic
- **Limitation**: May miss sophisticated networks using active intermediaries
- **Future**: Behavioral anomaly detection

### 4. Cycle Length Bounds
- **Current**: Only 3-5 node cycles
- **Limitation**: Longer cycles not detected
- **Rationale**: Precision vs recall trade-off
- **Future**: Configurable based on data characteristics

### 5. Memory-Based Processing
- **Current**: All analysis in RAM
- **Limitation**: Large datasets may exceed memory
- **Future**: Stream processing for scalability

### 6. Static Thresholds
- **Current**: Fan-in/out: 10, Velocity: 10 transactions
- **Limitation**: One-size-fits-all approach
- **Future**: Adaptive thresholds per baseline

---

## 👥 Team Members

- [Your Name] - Project Lead & Development
- [Additional members if any]

---

## 📝 License

[Your License Information]

---

## 📧 Contact

For questions or support: [your-email]

---

## 🏆 Acknowledgments

Built for **RIFT 2026 Hackathon** - Graph Theory / Financial Crime Detection Track

---

**Version**: 1.0.0
**Last Updated**: February 19, 2026
**Deployment Status**: Ready for Render
#   r i f t p r o j e c t  
 