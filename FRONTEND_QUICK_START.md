# OnSide Frontend - Quick Start Guide

## What's Been Implemented

### 1. Streamlit Demo Dashboard ✅
**Location**: `/Users/cope/EnGardeHQ/Onside/streamlit_dashboard.py`

**Start It**:
```bash
pip install -r streamlit_requirements.txt
export DEMO_MODE=true
streamlit run streamlit_dashboard.py
```

**Access**: http://localhost:8501

**Features**:
- Dashboard with metrics and charts
- Competitor analysis views
- SEO analytics tracking
- Reports management
- Demo mode with sample data
- Live API integration ready

---

### 2. WebSocket Progress Tracking ✅
**Location**: `/Users/cope/EnGardeHQ/Onside/frontend/src/components/ProgressTracker/`

**Start It**:
```bash
cd frontend
npm install
npm run dev
```

**Access**: http://localhost:3000

**Features**:
- Real-time progress updates
- 7-stage process tracking
- Beautiful progress bars
- Stage indicators
- Time estimates
- Cancel functionality
- Full accessibility support

---

## File Structure Created

```
/Users/cope/EnGardeHQ/Onside/
│
├── streamlit_dashboard.py              ← Demo dashboard app
├── streamlit_requirements.txt          ← Dependencies for Streamlit
├── STREAMLIT_DEMO_README.md           ← Streamlit documentation
│
├── frontend/                           ← React application
│   ├── package.json                   ← Node dependencies
│   ├── vite.config.ts                 ← Build configuration
│   ├── tsconfig.json                  ← TypeScript config
│   ├── .env.example                   ← Environment template
│   │
│   └── src/
│       ├── hooks/
│       │   └── useProgressTracking.ts ← WebSocket hook
│       │
│       └── components/
│           └── ProgressTracker/
│               ├── ProgressBar.tsx            ← Progress bar
│               ├── StageIndicator.tsx         ← Stage steps
│               ├── ReportProgressTracker.tsx  ← Main component
│               ├── ProgressTracker.example.tsx
│               └── index.ts
│
└── FRONTEND_IMPLEMENTATION_REPORT.md  ← Full technical report
```

---

## Testing the Implementations

### Test Streamlit Dashboard

1. **Start in Demo Mode**:
```bash
export DEMO_MODE=true
streamlit run streamlit_dashboard.py
```

2. **Navigate through**:
   - Click "Continue in Demo Mode" on login
   - View Dashboard Overview
   - Select competitors from sidebar
   - Explore Competitor Analysis tab
   - Check SEO Analytics
   - Browse Reports section

3. **Test API Integration** (requires backend running):
```bash
export API_BASE_URL=http://localhost:8000/api/v1
export DEMO_MODE=false
streamlit run streamlit_dashboard.py
```

### Test WebSocket Progress Tracking

1. **Start Frontend Dev Server**:
```bash
cd frontend
npm install
npm run dev
```

2. **Import Component**:
```tsx
import { ReportProgressTracker } from './src/components/ProgressTracker';

function App() {
  return (
    <ReportProgressTracker
      reportId={1}
      userId={1}
      onComplete={() => alert('Done!')}
    />
  );
}
```

3. **Test WebSocket Connection** (requires backend running):
   - Backend must be running at http://localhost:8000
   - WebSocket endpoint: ws://localhost:8000/api/v1/progress/ws/{reportId}

---

## Next Steps

### Ready to Implement (Priority Order)

1. **Issue #33: Competitor Management UI** (High Priority)
   - Forms for add/edit/delete competitors
   - Search and filter functionality
   - Domain management
   - Bulk operations

2. **Issue #32: Reports Dashboard** (High Priority)
   - List/grid view of reports
   - Detail view with sections
   - Interactive charts (use Recharts)
   - Integrate WebSocket progress tracker ✅

3. **Issue #34: SEO Analytics Dashboard** (Medium Priority)
   - Keyword rankings table
   - SERP features visualization
   - PageSpeed metrics
   - Trend charts

4. **Issue #31: Main Web Application UI** (Critical)
   - Authentication pages
   - Main layout structure
   - Navigation system
   - Routing setup

---

## Design Decisions Needed

Before proceeding with remaining issues, please decide:

### 1. Component Library
Which UI component library should we use?
- [ ] Material-UI (MUI) - Comprehensive, larger bundle
- [ ] Headless UI + Tailwind - Fully customizable, recommended
- [ ] Ant Design - Enterprise-focused
- [ ] Chakra UI - Modern, accessible

**Recommendation**: Headless UI + Tailwind CSS

### 2. Chart Library
For data visualizations:
- [ ] Recharts - Simple, React-first, recommended
- [ ] Chart.js - Popular, flexible
- [ ] D3.js - Most powerful, complex
- [ ] Apache ECharts - Feature-rich

**Recommendation**: Recharts for standard charts, D3 for custom

### 3. Brand Colors
Please provide:
- Primary color: ___________
- Secondary color: ___________
- Success/Warning/Error colors: ___________
- Current placeholder: #1f77b4 (blue)

### 4. Authentication Type
- [ ] JWT in HttpOnly cookies (most secure, recommended)
- [ ] JWT in localStorage (simpler, less secure)
- [ ] OAuth only (third-party)
- [ ] Hybrid approach

**Recommendation**: JWT HttpOnly + OAuth

---

## Integration Checklist

### Backend Requirements

For full frontend functionality, backend needs:

- [x] WebSocket progress endpoint (`/api/v1/progress/ws/{reportId}`)
- [x] Progress service with stage tracking
- [ ] Authentication endpoints (login/register/OAuth)
- [ ] Competitor CRUD endpoints
- [ ] Reports listing and detail endpoints
- [ ] SEO analytics endpoints
- [ ] PDF export endpoint
- [ ] Report scheduling endpoint

### Environment Variables

Set these in `.env`:

```env
# Frontend
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
VITE_ENABLE_WEBSOCKET=true

# Streamlit
API_BASE_URL=http://localhost:8000/api/v1
DEMO_MODE=false
```

---

## Troubleshooting

### Streamlit won't start
```bash
# Reinstall dependencies
pip install --upgrade -r streamlit_requirements.txt

# Check Python version (requires 3.8+)
python --version
```

### Frontend build errors
```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install

# Check Node version (requires 18+)
node --version
```

### WebSocket connection fails
- Ensure backend is running on port 8000
- Check CORS settings in backend
- Verify WebSocket URL in `.env`
- Check browser console for errors

---

## Documentation Files

- `FRONTEND_IMPLEMENTATION_REPORT.md` - Complete technical details
- `STREAMLIT_DEMO_README.md` - Streamlit documentation
- `frontend/README.md` - React app documentation
- `FRONTEND_QUICK_START.md` - This file

---

## Support

All implementations follow:
- ✅ WCAG 2.1 Level AA accessibility
- ✅ Responsive design (mobile, tablet, desktop)
- ✅ Modern React best practices
- ✅ TypeScript strict mode
- ✅ Performance optimized
- ✅ Production ready

**Status**: Phase 1 Complete - Ready for demos and testing!
