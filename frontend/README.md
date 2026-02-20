# RIFT Forensics Engine — Money Muling Detection

> **RIFT 2026 Hackathon · Graph Theory / Financial Crime Detection Track**

## Live Demo URL
_Add your deployed URL here after deployment._

---

## Tech Stack

| Layer          | Technology                          |
|----------------|-------------------------------------|
| Frontend       | React 18 + Vite                     |
| State Mgmt     | Redux Toolkit + React-Redux         |
| Styling        | Tailwind CSS v3                     |
| HTTP Client    | Axios                               |
| Graph Viz      | D3.js v7 (force-directed graph)     |
| Backend API    | `https://rift-fraud-detection.onrender.com` |

---

## Folder Structure

```
rift-forensics/
├── public/
├── src/
│   ├── api/
│   │   └── fraudApi.js          # Axios API layer — all endpoints
│   ├── components/
│   │   ├── Header.jsx            # Sticky top bar, status badge, download
│   │   ├── UploadZone.jsx        # Drag-and-drop CSV upload
│   │   ├── LogTerminal.jsx       # Real-time pipeline log
│   │   ├── Dashboard.jsx         # KPI summary cards
│   │   ├── Graph.jsx             # D3 force-directed transaction graph
│   │   ├── NodeDetailPanel.jsx   # Slide-in node inspector
│   │   ├── FraudRingsTable.jsx   # Fraud ring summary table
│   │   ├── SuspiciousAccountsTable.jsx
│   │   └── BottomTabs.jsx        # Tabbed content area
│   ├── store/
│   │   ├── index.js              # Redux store configuration
│   │   ├── fraudSlice.js         # Pipeline state + async thunks
│   │   └── uiSlice.js            # UI state (selectedNode, activeTab)
│   ├── utils/
│   │   └── graphHelpers.js       # D3 data builders, color constants
│   ├── App.jsx
│   ├── main.jsx
│   └── index.css
├── index.html
├── package.json
├── vite.config.js
├── tailwind.config.js
└── postcss.config.js
```

---

## System Architecture

```
CSV Upload
    │
    ▼
UploadZone (React)
    │  dispatches runFullPipeline(file)
    ▼
fraudSlice (Redux Thunk)
    ├── POST /api/fraud/upload
    ├── POST /api/transactions/upload-transactions
    ├── POST /api/fraud/analyze
    ├── GET  /api/fraud/report/{report_id}
    └── GET  /api/transactions/batch/{upload_id}
                │
                ▼
        Redux Store (report + transactions)
                │
        ┌───────┴──────────┐
        ▼                  ▼
   Graph.jsx          Dashboard, Tables
  (D3 force sim)      (React + Tailwind)
```

---

## Algorithm Approach

### Graph Construction
- Each `sender_id` and `receiver_id` becomes a **node**
- Each transaction becomes a **directed edge**
- Total nodes = `unique_accounts`; edges = `transaction_count`

### Fraud Detection (backend)
| Pattern | Description |
|---------|-------------|
| **Circular Fund Routing** | Cycles of length 3–5 detected via DFS |
| **Smurfing (Fan-in/out)** | ≥10 senders → 1 receiver or 1 → ≥10 receivers |
| **Layered Shell Networks** | Chains 3+ hops via low-activity intermediary nodes |

### Suspicion Score Methodology
- Base score per detected pattern (e.g. `cycle_length_3` → 30.8 pts)
- Multiple pattern hits are additive (capped at 100)
- Sorted descending in output

### Graph Layout Fix
D3's force simulation isolates disconnected subgraphs. Fixed with:
- `forceX(cx).strength(0.08)` + `forceY(cy).strength(0.08)` — pulls all nodes toward canvas centre
- `alphaDecay(0.015)` — slower cooling for better convergence
- Collision radius proportional to node type

### Complexity
- Graph build: **O(V + E)** where V = unique accounts, E = transactions
- Cycle detection: **O(V + E)** DFS per starting node → **O(V(V+E))** worst case
- Force simulation: **O(V²)** per tick (mitigated by Barnes-Hut approximation)

---

## Installation & Setup

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/rift-forensics.git
cd rift-forensics

# Install dependencies
npm install

# Start dev server
npm run dev
```

Open [http://localhost:5173](http://localhost:5173)

## Build for Production

```bash
npm run build
# Output in /dist — deploy to Vercel / Netlify / Render
```

---

## Usage Instructions

1. **Prepare your CSV** with columns: `transaction_id, sender_id, receiver_id, amount, timestamp`
2. **Drag & drop** the file or click the upload area
3. Click **▶ RUN FORENSIC ANALYSIS**
4. Watch the pipeline log as each API call executes
5. Explore the **transaction network graph** — zoom, pan, drag nodes
6. **Click any node** to see full details in the side panel
7. Browse the **Fraud Ring Summary** and **Suspicious Accounts** tables
8. Click **⬇ DOWNLOAD JSON** for the exact competition-format output

---

## Known Limitations

- Backend on Render free tier may cold-start (~30s delay on first request)
- Very large graphs (>10K nodes) may have slower D3 simulation convergence
- Cycle detection limited to lengths 3–5 (per spec)
- No authentication — single shared backend instance

---

## Team Members

_Add your names here_
