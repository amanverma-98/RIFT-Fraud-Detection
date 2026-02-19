# RIFT 2026 Money Muling Detection - React Frontend

Professional React dashboard for the RIFT 2026 Hackathon Money Muling Detection Challenge.

## 🎯 Features

✅ **CSV File Upload** - Drag-and-drop CSV file upload with real-time validation
✅ **Interactive Graph Visualization** - Visualize transaction networks with d3-force-graph
✅ **Fraud Ring Detection** - Display detected fraud rings with detailed statistics
✅ **Suspicious Accounts List** - Sort and filter by suspicion score and patterns
✅ **Real-time Analysis** - Live processing with progress indicators
✅ **JSON Report Download** - Export RIFT-compliant JSON reports
✅ **Dark Theme UI** - Professional, modern dashboard with gradient effects
✅ **Fully Responsive** - Mobile-friendly design
✅ **Performance Optimized** - Efficient rendering for large datasets

## 🏗️ Architecture

```
frontend/
├── public/
│   └── index.html
├── src/
│   ├── components/
│   │   ├── FileUpload.jsx           # CSV drag-and-drop uploader
│   │   ├── GraphVisualization.jsx   # D3 force-directed graph
│   │   ├── FraudRingTable.jsx       # Fraud rings summary table
│   │   ├── SuspiciousAccountsList.jsx # Account cards with sorting
│   │   ├── Header.jsx               # Navigation header
│   │   └── LoadingSpinner.jsx       # Loading state indicator
│   ├── services/
│   │   └── api.js                   # Axios API wrapper
│   ├── styles/
│   │   ├── App.css                  # Main layout styles
│   │   └── components.css           # Component-specific styles
│   ├── App.jsx                      # Main app component
│   ├── main.jsx                     # React entry point
│   └── index.css                    # Global CSS variables
├── package.json
├── vite.config.js
├── .env.example
└── .gitignore
```

## 🚀 Quick Start

### Prerequisites
- Node.js 16+
- npm or yarn
- Python FastAPI backend running on localhost:10000

### Installation

1. **Clone and navigate to frontend directory**
```bash
cd fraud-detection-system/frontend
```

2. **Install dependencies**
```bash
npm install
```

3. **Create `.env.local` from `.env.example`**
```bash
cp .env.example .env.local
```

**For local development:**
```
VITE_API_URL=http://localhost:10000/api
```

**For production:**
```
VITE_API_URL=https://rift-fraud-detection.onrender.com/api
```

4. **Start development server**
```bash
npm run dev
```

The app will open at `http://localhost:5173`

## 📦 Build for Production

```bash
npm run build
```

This creates an optimized production build in the `dist/` directory.

### Deploy to Vercel
```bash
npm install -g vercel
vercel
```

### Deploy to Netlify
```bash
npm install -g netlify-cli
netlify deploy --prod --dir=dist
```

## 🔌 API Integration

The frontend communicates with your FastAPI backend:

### Endpoints Used
- `POST /api/fraud/upload` - Upload CSV file
- `POST /api/fraud/analyze?filename=X` - Analyze transactions
- `GET /api/fraud/report/{report_id}` - Fetch full report
- `GET /api/fraud/report/{report_id}/download-json` - Download JSON
- `GET /api/fraud/reports` - List all reports
- `GET /api/health` - Health check

See `src/services/api.js` for complete implementation.

## 🎨 UI/UX Components

### FileUpload
Drag-and-drop CSV uploader with validation
- Accepts `.csv` files only
- Shows file size and name
- Displays validation error messages

### GraphVisualization
Interactive force-directed graph showing account relationships
- **Node Colors:**
  - 🔵 Blue: Normal accounts
  - 🔴 Red: Very suspicious (score > 80)
  - 🟡 Yellow: Medium suspicious (score > 50)
  - 🟣 Purple: Low suspicious
  - 🟢 Green: Selected account

- **Interactions:**
  - Drag nodes to reposition
  - Hover to highlight relationships
  - Click to select and view details
  - Zoom and pan enabled

### FraudRingTable
Displays detected fraud rings with:
- Ring ID (RING_001, RING_002, etc.)
- Pattern type (cycle, fan_in, fan_out, shell)
- Member count and accounts
- Risk score with visual bar

### SuspiciousAccountsList
Account cards with:
- Suspicion score (0-100)
- Detected patterns with color coding
- Ring assignment
- Sort by score or pattern count
- Filter by specific ring

## 🎨 Customization

### Change Colors
Edit `src/index.css` CSS variables:
```css
:root {
  --primary-color: #00d4ff;
  --secondary-color: #ff006e;
  --warning-color: #ffd60a;
  --danger-color: #e63946;
  /* ... */
}
```

### Modify Layout
Main layout styles in `src/styles/App.css`:
- `.upload-section` - File upload page
- `.results-section` - Analysis results page
- `.summary-cards` - Statistics cards grid

### Add Features
Extend components in `src/components/`:
- Add new chart types
- Export additional formats
- Implement account timeline
- Add transaction details modal

## 📊 Data Flow

```
CSV Upload
    ↓
API: /api/fraud/upload → Backend saves file
    ↓
API: /api/fraud/analyze → Backend processes transactions
    ↓
API: /api/fraud/report/{id} → Fetch full RIFT report
    ↓
GraphVisualization ← Suspicious accounts
FraudRingTable    ← Fraud rings
SuspiciousAccounts ← Account details
    ↓
Download JSON → /api/fraud/report/{id}/download-json
```

## ⚡ Performance Optimizations

- **React.memo** for component memoization
- **Lazy loading** for large datasets
- **CSS Grid/Flexbox** efficient layout
- **Canvas rendering** for graph (via react-force-graph-2d)
- **Debounced sorting/filtering**

## 🧪 Testing

### Manual Testing Checklist
- [ ] CSV upload with valid file
- [ ] CSV upload with invalid format
- [ ] Graph visualization renders
- [ ] Click node to select account
- [ ] Hover node for highlight
- [ ] Sort suspicious accounts
- [ ] Filter by fraud ring
- [ ] Download JSON report
- [ ] View report on mobile
- [ ] Test all error states

## 📱 Browser Support

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
- Mobile browsers (iOS Safari, Chrome Mobile)

## 🔧 Troubleshooting

### API Connection Error
**Problem:** "Failed to connect to API"
**Solution:** Check `.env.local` API URL matches backend, ensure backend is running

### Graph Not Rendering
**Problem:** Graph container shows but no nodes
**Solution:** Check browser console for errors, ensure data has nodes array

### File Upload Fails
**Problem:** Upload button disabled or shows error
**Solution:** Check file is valid CSV with required columns, < 50MB file size

## 📚 Dependencies

### Core
- **react** - UI framework
- **react-dom** - React DOM rendering

### Data & Visualization
- **react-force-graph-2d** - 2D graph visualization
- **axios** - HTTP client for API calls

### UI/UX
- **lucide-react** - Icon library
- **react-modal** - Modal component (optional, for future use)

### Build Tools
- **vite** - Build tool
- **@vitejs/plugin-react** - Vite React plugin

## 📄 Environment Variables

```
VITE_API_URL       # Backend API base URL (default: http://localhost:10000/api)
```

## 🚀 Deployment Checklist

- [ ] Update `VITE_API_URL` to production backend
- [ ] Test all API endpoints on production
- [ ] Enable CORS on backend
- [ ] Build optimized production bundle
- [ ] Deploy to hosting (Vercel, Netlify, etc.)
- [ ] Set up custom domain
- [ ] Enable SSL/HTTPS
- [ ] Monitor error logs
- [ ] Test live application

## 📞 Support

For issues or questions:
1. Check browser console for error messages
2. Verify backend is running and accessible
3. Check network tab in DevTools for failed requests
4. Review README and SYSTEM_ARCHITECTURE_AND_FLOW.md

## 📝 License

RIFT 2026 Hackathon Project

## 👥 Team

Built for RIFT 2026 Hackathon - Graph Theory / Financial Crime Detection Track
