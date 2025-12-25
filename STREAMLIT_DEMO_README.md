# OnSide Streamlit Demo Dashboard

Quick-win demo dashboard for stakeholder presentations and internal testing.

## Features

- **Dashboard Overview**: Key metrics and competitor performance comparison
- **Competitor Analysis**: SEO rankings, content analysis, and technology stack detection
- **SEO Analytics**: Keyword performance tracking and Core Web Vitals monitoring
- **Reports Dashboard**: Report listing, generation, and preview functionality
- **Demo Mode**: Offline presentations with sample data

## Installation

1. Install Streamlit dependencies:
```bash
pip install -r streamlit_requirements.txt
```

## Running the Dashboard

### Demo Mode (Offline with Sample Data)

```bash
export DEMO_MODE=true
streamlit run streamlit_dashboard.py
```

### Live Mode (Connected to API)

```bash
export API_BASE_URL=http://localhost:8000/api/v1
export DEMO_MODE=false
streamlit run streamlit_dashboard.py
```

The dashboard will be available at: http://localhost:8501

## Demo Script for Presentations

### 1. Dashboard Overview (2 minutes)
- Show key metrics: active competitors, total reports, traffic, SEO score
- Highlight competitor performance comparison chart
- Point out recent reports and engagement metrics

### 2. Competitor Analysis (3 minutes)
- Select competitors from sidebar
- Show keyword rankings comparison chart
- Explain SEO position tracking (lower is better)
- Preview content analysis and technology stack features

### 3. SEO Analytics (2 minutes)
- Display keyword performance trends over time
- Show Core Web Vitals metrics (LCP, FID, CLS)
- Highlight PageSpeed scores for mobile and desktop

### 4. Reports Dashboard (2 minutes)
- List recent reports
- Demonstrate report generation workflow
- Show download and sharing options

### 5. Settings & Configuration (1 minute)
- API configuration options
- Notification preferences
- Export settings

## Sample Data

Demo mode includes sample data for:
- 3 competitors (Competitor A, B, C)
- SEO rankings for key AI/analytics keywords
- Engagement metrics (session duration, bounce rate, page views)
- 2 completed reports

## API Integration

When running in live mode, the dashboard connects to:
- `/api/v1/auth/login` - Authentication
- `/api/v1/competitors` - Competitor data
- `/api/v1/seo` - SEO analytics
- `/api/v1/reports` - Reports management
- `/api/v1/health` - Health checks

## Customization

### Adding New Visualizations

Edit `streamlit_dashboard.py` and add new chart components using Plotly:

```python
import plotly.graph_objects as go

fig = go.Figure(data=[go.Bar(x=categories, y=values)])
st.plotly_chart(fig, use_container_width=True)
```

### Extending Demo Data

Update the `DEMO_DATA` dictionary in `streamlit_dashboard.py`:

```python
DEMO_DATA = {
    "competitors": [...],
    "seo_rankings": {...},
    # Add your custom data here
}
```

## Deployment

### Deploy to Streamlit Cloud

1. Push the repository to GitHub
2. Go to https://share.streamlit.io
3. Connect your repository
4. Select `streamlit_dashboard.py` as the main file
5. Set environment variables in Streamlit Cloud settings

### Deploy with Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY streamlit_requirements.txt .
RUN pip install -r streamlit_requirements.txt

COPY streamlit_dashboard.py .

EXPOSE 8501

CMD ["streamlit", "run", "streamlit_dashboard.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

Build and run:
```bash
docker build -t onside-streamlit .
docker run -p 8501:8501 -e DEMO_MODE=true onside-streamlit
```

## Next Steps

This Streamlit dashboard is a quick-win solution for demos while the main React/Next.js UI is being developed. Key integration points:

1. **WebSocket Progress Tracking**: Add real-time report generation progress
2. **Enhanced Competitor Views**: Integrate with competitor management API
3. **Advanced SEO Analytics**: Connect to SEO analytics endpoints
4. **Report Generation**: Implement full report generation workflow
5. **User Authentication**: Enhance login with OAuth support

## Support

For issues or questions about the demo dashboard:
- Check API connectivity with health endpoint
- Verify environment variables are set correctly
- Review Streamlit logs for errors
- Test in demo mode first to isolate API issues
