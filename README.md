"""
Financial Fraud Detection System
=================================

A production-ready FastAPI-based fraud detection platform with
6 detection algorithms, unified scoring, and compliance reporting
for financial institutions.

------------------------------------------------------------
ENTERPRISE FRAUD DETECTION
------------------------------------------------------------

Multi-Algorithm Approach:
- Cycle Detection (A→B→C→A circular flows)
- Fan-in / Fan-out Detection
- Shell Chain Detection
- Velocity Analysis
- Unified Risk Scoring (0–100)
- Compliance Reporting (Fraud rings, risk tiers, JSON export)

------------------------------------------------------------
KEY FEATURES
------------------------------------------------------------

Enterprise-Grade Architecture:
- 100% type hints and docstrings
- Structured logging
- Clean service-layer separation
- Validation and error handling

Deterministic & Reproducible:
- Same input → identical output
- ISO 8601 UTC timestamps
- Sorted deterministic results
- Regulatory audit compliant

High Performance:
- O(V + E + N log N) complexity
- Handles 100K+ transactions
- Fraud ring detection via SCC clustering
- Fully JSON serializable output

Regulatory Compliance:
- Pattern attribution
- Risk-tier classification
- Audit trail support
- AML/CFT compliant

------------------------------------------------------------
PROJECT STRUCTURE
------------------------------------------------------------

fraud-detection-system/
│
├── app/
│   ├── main.py
│   ├── config.py
│   ├── middleware/error_handler.py
│   ├── routers/
│   │   ├── transactions.py
│   │   ├── fraud_detection.py
│   │   └── health.py
│   ├── models/transaction_models.py
│   ├── services/
│   │   ├── transaction_csv_parser.py
│   │   ├── transaction_store.py
│   │   ├── transaction_graph_builder.py
│   │   ├── cycle_detection.py
│   │   ├── fan_pattern_detection.py
│   │   ├── shell_chain_detection.py
│   │   ├── suspicion_scoring.py
│   │   ├── compliance_reporting.py
│   └── utils/
│       ├── exceptions.py
│       ├── logger.py
│       └── validators.py
│
├── .env.example
├── requirements.txt
├── docker-compose.yml
├── Dockerfile
├── sample_transactions.csv
└── README.md

------------------------------------------------------------
INSTALLATION
------------------------------------------------------------

1. Create virtual environment:
    python -m venv venv
    source venv/bin/activate

2. Install dependencies:
    pip install -r requirements.txt

3. Configure environment:
    cp .env.example .env

4. Run development server:
    python -m uvicorn app.main:app --reload

------------------------------------------------------------
API ENDPOINTS
------------------------------------------------------------

Transaction Management:
POST   /api/transactions/upload-transactions
GET    /api/transactions/batch/{batch_id}
GET    /api/transactions/batches
DELETE /api/transactions/batch/{batch_id}
POST   /api/transactions/clear-all

Health:
GET    /health

Documentation:
GET    /docs
GET    /redoc

------------------------------------------------------------
CSV FORMAT
------------------------------------------------------------

Required Columns:
- transaction_id
- sender_id
- receiver_id
- amount
- timestamp

Example:

transaction_id,sender_id,receiver_id,amount,timestamp
TXN001,ACC001,ACC002,1000.00,2025-02-19T10:00:00
TXN002,ACC002,ACC003,2500.50,2025-02-19T10:15:00
TXN003,ACC003,ACC001,1200.00,2025-02-19T10:30:00

Supported Timestamp Formats:
- ISO 8601
- ISO Compact (Z)
- DateTime
- Date Only

------------------------------------------------------------
FRAUD DETECTION ALGORITHMS
------------------------------------------------------------

1. Cycle Detection
   - Detects circular money flows
   - Complexity: O(C*L)

2. Fan-in / Fan-out Detection
   - Detects aggregation and distribution hubs
   - Complexity: O(N log N)

3. Shell Chain Detection
   - Detects obfuscation via low-degree nodes
   - Complexity: O(V + E)

4. Velocity Analysis
   - Detects rapid transaction bursts
   - Complexity: O(N log N)

5. Unified Scoring
   - Score = min(100, (raw_score / 130) * 100)

------------------------------------------------------------
CONFIGURATION VARIABLES
------------------------------------------------------------

APP_NAME=Financial Fraud Detection System
VERSION=1.0.0
HOST=0.0.0.0
PORT=8000
DEBUG=False

SUSPICIOUS_ACCOUNT_THRESHOLD=30
HIGH_RISK_THRESHOLD=80
MEDIUM_RISK_THRESHOLD=50

FAN_THRESHOLD=10
FAN_WINDOW_HOURS=72

VELOCITY_THRESHOLD=10
VELOCITY_WINDOW_HOURS=24

MIN_CYCLE_LENGTH=3
MAX_CYCLE_LENGTH=5

SHELL_THRESHOLD=3
MIN_RING_SIZE=2
RING_SCORE_THRESHOLD=30

------------------------------------------------------------
PRODUCTION RECOMMENDATIONS
------------------------------------------------------------

- Replace in-memory store with PostgreSQL or MongoDB
- Add JWT/OAuth2 authentication
- Add rate limiting
- Use Redis caching
- Add CI/CD pipeline
- Add containerization
- Add monitoring tools

------------------------------------------------------------
SECURITY NOTES
------------------------------------------------------------

- Restrict CORS in production
- Add authentication
- Add file size limits
- Use secrets management

------------------------------------------------------------
LICENSE
------------------------------------------------------------

Proprietary – All rights reserved.
"""
