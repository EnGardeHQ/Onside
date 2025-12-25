# OnSide Frontend - Quick Start Guide

## Get Started in 3 Minutes

### 1. Install Dependencies
```bash
cd /Users/cope/EnGardeHQ/Onside/frontend
npm install
```

### 2. Configure Environment
```bash
# The .env.example is already set up correctly
# Just copy it if needed:
cp .env.example .env
```

### 3. Start Development Server
```bash
npm run dev
```

Application will open at **http://localhost:3000**

## Default Login (After Backend Setup)

Create an account at `/register` or use backend-created credentials.

## Available Pages

Once logged in, you'll have access to:

- **Dashboard** (`/dashboard`) - Overview with quick stats
- **Competitors** (`/competitors`) - Manage competitor tracking
- **Reports** (`/reports`) - Generate and view intelligence reports
- **SEO Analytics** (`/seo-analytics`) - Keyword rankings and metrics
- **Settings** (`/settings`) - Coming soon

## Key Features to Try

### Competitor Management
1. Click "Add Competitor"
2. Fill in competitor details
3. Add domains for tracking
4. Use bulk selection for comparison

### Report Generation
1. Click "Generate Report"
2. Select report type
3. Monitor real-time progress
4. View and export when complete

### SEO Analytics
1. View keyword rankings table
2. Check SERP features chart
3. Monitor Core Web Vitals
4. Compare competitor rankings

## Build Commands

```bash
# Development
npm run dev

# Type checking
npm run type-check

# Linting
npm run lint

# Format code
npm run format

# Production build
npm run build

# Preview production build
npm run preview
```

## Troubleshooting

**Port 3000 in use?**
```bash
# Vite will automatically try port 3001, 3002, etc.
# Or specify a port:
npm run dev -- --port 3005
```

**API not connecting?**
- Verify backend is running on port 8000
- Check `.env` has correct `VITE_API_URL`

**TypeScript errors?**
```bash
npm run type-check
```

## Project Features

✅ **4 Complete Dashboard Views**
- Dashboard home with metrics
- Competitor management with CRUD
- Reports with charts and PDF export
- SEO analytics with rankings

✅ **Modern Stack**
- React 18 + TypeScript
- Vite for fast dev
- Tailwind CSS for styling
- React Query for data

✅ **Production Ready**
- Form validation (Zod)
- Error boundaries
- Loading states
- Dark mode
- Responsive design
- WCAG AA accessible

## Next Steps

1. Ensure backend API is running
2. Register a new account
3. Add your first competitor
4. Generate a report
5. Explore SEO analytics

## Documentation

See `FRONTEND_IMPLEMENTATION.md` for complete technical documentation.

---

**Questions?** Check the troubleshooting section or review the full documentation.
