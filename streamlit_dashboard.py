"""
OnSide Streamlit Demo Dashboard
================================
Quick demo dashboard for stakeholder presentations and internal testing.

Features:
- Data from all API sources
- Competitor comparison views
- Interactive filtering and customization
- Report preview functionality
- Demo mode with sample data for offline presentations
"""

import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, Any, List, Optional
import os
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

# Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")
DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() == "true"

# Page config
st.set_page_config(
    page_title="OnSide - Competitive Intelligence Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .competitor-card {
        border-left: 4px solid #1f77b4;
        padding-left: 1rem;
        margin-bottom: 1rem;
    }
    .success-badge {
        background-color: #28a745;
        color: white;
        padding: 0.25rem 0.5rem;
        border-radius: 0.25rem;
        font-size: 0.875rem;
    }
    .warning-badge {
        background-color: #ffc107;
        color: black;
        padding: 0.25rem 0.5rem;
        border-radius: 0.25rem;
        font-size: 0.875rem;
    }
</style>
""", unsafe_allow_html=True)

# Demo data for offline presentations
DEMO_DATA = {
    "competitors": [
        {"id": 1, "name": "Competitor A", "domain": "competitora.com", "status": "active"},
        {"id": 2, "name": "Competitor B", "domain": "competitorb.com", "status": "active"},
        {"id": 3, "name": "Competitor C", "domain": "competitorc.com", "status": "monitoring"}
    ],
    "seo_rankings": {
        "competitora.com": {
            "keywords": ["AI analytics", "business intelligence", "data insights"],
            "rankings": [3, 5, 8],
            "traffic_estimate": 12500
        },
        "competitorb.com": {
            "keywords": ["AI analytics", "business intelligence", "data insights"],
            "rankings": [5, 7, 12],
            "traffic_estimate": 8900
        },
        "competitorc.com": {
            "keywords": ["AI analytics", "business intelligence", "data insights"],
            "rankings": [2, 4, 6],
            "traffic_estimate": 15200
        }
    },
    "engagement_metrics": {
        "competitora.com": {"avg_session": "3:45", "bounce_rate": "42%", "page_views": 23000},
        "competitorb.com": {"avg_session": "2:30", "bounce_rate": "55%", "page_views": 15000},
        "competitorc.com": {"avg_session": "4:20", "bounce_rate": "35%", "page_views": 28000}
    },
    "recent_reports": [
        {
            "id": 1,
            "title": "Competitive Analysis - Q4 2024",
            "created_at": "2024-12-15T10:30:00",
            "status": "completed",
            "type": "comprehensive"
        },
        {
            "id": 2,
            "title": "SEO Performance Report",
            "created_at": "2024-12-20T14:20:00",
            "status": "completed",
            "type": "seo"
        }
    ]
}

# Session state initialization
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = DEMO_MODE
if 'api_token' not in st.session_state:
    st.session_state.api_token = None
if 'selected_competitors' not in st.session_state:
    st.session_state.selected_competitors = []

def make_api_request(endpoint: str, method: str = "GET", data: Optional[Dict] = None) -> Optional[Dict]:
    """Make API request with authentication"""
    if DEMO_MODE:
        return None

    headers = {}
    if st.session_state.api_token:
        headers["Authorization"] = f"Bearer {st.session_state.api_token}"

    try:
        url = f"{API_BASE_URL}/{endpoint}"
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data)
        else:
            return None

        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API Error: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Connection Error: {str(e)}")
        return None

def login_page():
    """Login page for API authentication"""
    st.markdown('<div class="main-header">OnSide Login</div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown("### Access the Dashboard")

        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login")

            if submit:
                # Authenticate with API
                response = make_api_request("auth/login", method="POST",
                                          data={"username": username, "password": password})
                if response and "access_token" in response:
                    st.session_state.api_token = response["access_token"]
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("Invalid credentials")

        st.markdown("---")
        if st.button("Continue in Demo Mode"):
            st.session_state.authenticated = True
            st.rerun()

def sidebar_navigation():
    """Sidebar navigation and filters"""
    with st.sidebar:
        st.markdown("### Navigation")

        page = st.radio(
            "Select View",
            ["Dashboard Overview", "Competitor Analysis", "SEO Analytics",
             "Reports", "Settings"],
            label_visibility="collapsed"
        )

        st.markdown("---")
        st.markdown("### Filters")

        # Date range filter
        date_range = st.date_input(
            "Date Range",
            value=(datetime.now() - timedelta(days=30), datetime.now()),
            max_value=datetime.now()
        )

        # Competitor selection
        if DEMO_MODE:
            competitors = [c["name"] for c in DEMO_DATA["competitors"]]
        else:
            # Fetch from API
            comp_data = make_api_request("competitors")
            competitors = [c["name"] for c in comp_data] if comp_data else []

        selected_competitors = st.multiselect(
            "Select Competitors",
            options=competitors,
            default=competitors[:2] if competitors else []
        )
        st.session_state.selected_competitors = selected_competitors

        st.markdown("---")
        st.markdown("### Demo Mode")
        if DEMO_MODE:
            st.success("Demo Mode Active")
            st.caption("Using sample data for offline demo")
        else:
            st.info("Connected to Live API")

        return page

def dashboard_overview():
    """Main dashboard overview page"""
    st.markdown('<div class="main-header">📊 Dashboard Overview</div>', unsafe_allow_html=True)

    # Key metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="Active Competitors",
            value=len(DEMO_DATA["competitors"]) if DEMO_MODE else 0,
            delta="+2 this month"
        )

    with col2:
        st.metric(
            label="Total Reports",
            value=len(DEMO_DATA["recent_reports"]) if DEMO_MODE else 0,
            delta="+5 this week"
        )

    with col3:
        st.metric(
            label="Avg. Traffic",
            value="12.2K",
            delta="+8.5%"
        )

    with col4:
        st.metric(
            label="SEO Score",
            value="78/100",
            delta="+3"
        )

    st.markdown("---")

    # Competitor comparison
    st.markdown("### Competitor Performance Comparison")

    if DEMO_MODE:
        # Create comparison chart
        competitors = [c["name"] for c in DEMO_DATA["competitors"]]
        traffic = [DEMO_DATA["seo_rankings"][c["domain"]]["traffic_estimate"]
                   for c in DEMO_DATA["competitors"]]

        fig = go.Figure(data=[
            go.Bar(name='Traffic Estimate', x=competitors, y=traffic)
        ])
        fig.update_layout(
            title="Monthly Traffic Estimates",
            xaxis_title="Competitor",
            yaxis_title="Monthly Visitors",
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)

    # Recent activity
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Recent Reports")
        if DEMO_MODE:
            for report in DEMO_DATA["recent_reports"]:
                with st.container():
                    st.markdown(f"**{report['title']}**")
                    st.caption(f"Created: {report['created_at'][:10]}")
                    st.markdown(f'<span class="success-badge">{report["status"]}</span>',
                              unsafe_allow_html=True)
                    st.markdown("---")

    with col2:
        st.markdown("### Engagement Metrics")
        if DEMO_MODE:
            metrics_data = []
            for comp in DEMO_DATA["competitors"]:
                domain = comp["domain"]
                if domain in DEMO_DATA["engagement_metrics"]:
                    metrics = DEMO_DATA["engagement_metrics"][domain]
                    metrics_data.append({
                        "Competitor": comp["name"],
                        "Avg Session": metrics["avg_session"],
                        "Bounce Rate": metrics["bounce_rate"],
                        "Page Views": metrics["page_views"]
                    })

            df = pd.DataFrame(metrics_data)
            st.dataframe(df, use_container_width=True, hide_index=True)

def competitor_analysis():
    """Competitor analysis page"""
    st.markdown('<div class="main-header">🎯 Competitor Analysis</div>', unsafe_allow_html=True)

    if not st.session_state.selected_competitors:
        st.warning("Please select competitors from the sidebar to view analysis")
        return

    st.markdown(f"### Analyzing: {', '.join(st.session_state.selected_competitors)}")

    # Tabs for different analyses
    tab1, tab2, tab3 = st.tabs(["SEO Rankings", "Content Analysis", "Technology Stack"])

    with tab1:
        st.markdown("#### Keyword Rankings Comparison")

        if DEMO_MODE:
            # Create rankings comparison
            keywords = DEMO_DATA["seo_rankings"]["competitora.com"]["keywords"]

            fig = go.Figure()

            for comp in DEMO_DATA["competitors"][:3]:
                domain = comp["domain"]
                if domain in DEMO_DATA["seo_rankings"]:
                    rankings = DEMO_DATA["seo_rankings"][domain]["rankings"]
                    fig.add_trace(go.Scatter(
                        x=keywords,
                        y=rankings,
                        mode='lines+markers',
                        name=comp["name"]
                    ))

            fig.update_layout(
                title="Keyword Rankings (Lower is Better)",
                xaxis_title="Keywords",
                yaxis_title="Ranking Position",
                height=400,
                yaxis=dict(autorange="reversed")
            )
            st.plotly_chart(fig, use_container_width=True)

    with tab2:
        st.markdown("#### Content Performance")
        st.info("Content analysis coming soon - integrates with AI Insights API")

    with tab3:
        st.markdown("#### Technology Stack Detection")
        st.info("Technology stack analysis coming soon - integrates with Web Scraper API")

def seo_analytics():
    """SEO Analytics page"""
    st.markdown('<div class="main-header">🔍 SEO Analytics</div>', unsafe_allow_html=True)

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("### Keyword Performance Over Time")

        # Sample time series data
        dates = pd.date_range(start='2024-11-01', end='2024-12-22', freq='D')
        rankings = [5 + (i % 10) - 5 for i in range(len(dates))]

        df = pd.DataFrame({
            'Date': dates,
            'Ranking': rankings
        })

        fig = px.line(df, x='Date', y='Ranking', title='Keyword Ranking Trend')
        fig.update_yaxes(autorange="reversed")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("### Core Web Vitals")
        st.metric("LCP", "2.1s", delta="-0.3s", delta_color="normal")
        st.metric("FID", "45ms", delta="-10ms", delta_color="normal")
        st.metric("CLS", "0.08", delta="-0.02", delta_color="normal")

        st.markdown("---")
        st.markdown("### PageSpeed Score")
        st.metric("Mobile", "78/100", delta="+5")
        st.metric("Desktop", "92/100", delta="+3")

def reports_view():
    """Reports listing and preview"""
    st.markdown('<div class="main-header">📑 Reports Dashboard</div>', unsafe_allow_html=True)

    # Action buttons
    col1, col2, col3 = st.columns([1, 1, 4])
    with col1:
        if st.button("Generate New Report", type="primary"):
            st.info("Report generation initiated - WebSocket progress tracking will appear here")
    with col2:
        if st.button("Schedule Report"):
            st.info("Report scheduling interface coming soon")

    st.markdown("---")

    # Reports list
    if DEMO_MODE:
        st.markdown("### Recent Reports")

        for report in DEMO_DATA["recent_reports"]:
            with st.expander(f"{report['title']} - {report['created_at'][:10]}"):
                st.markdown(f"**Type:** {report['type']}")
                st.markdown(f"**Status:** {report['status']}")
                st.markdown(f"**Created:** {report['created_at']}")

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.button("View Details", key=f"view_{report['id']}")
                with col2:
                    st.button("Download PDF", key=f"pdf_{report['id']}")
                with col3:
                    st.button("Share", key=f"share_{report['id']}")

def settings_page():
    """Settings and configuration"""
    st.markdown('<div class="main-header">⚙️ Settings</div>', unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["API Configuration", "Notifications", "Export Settings"])

    with tab1:
        st.markdown("### API Configuration")

        api_url = st.text_input("API Base URL", value=API_BASE_URL)

        if st.button("Test Connection"):
            response = make_api_request("health")
            if response:
                st.success("Connection successful!")
            else:
                st.error("Connection failed")

    with tab2:
        st.markdown("### Notification Preferences")

        st.checkbox("Email notifications for new reports", value=True)
        st.checkbox("Weekly digest", value=True)
        st.checkbox("Competitor alerts", value=False)

    with tab3:
        st.markdown("### Export Settings")

        st.selectbox("Default export format", ["PDF", "Excel", "CSV", "JSON"])
        st.checkbox("Include charts in exports", value=True)
        st.checkbox("Include raw data", value=False)

def main():
    """Main application entry point"""

    # Check authentication
    if not st.session_state.authenticated:
        login_page()
        return

    # Show navigation and get selected page
    page = sidebar_navigation()

    # Route to appropriate page
    if page == "Dashboard Overview":
        dashboard_overview()
    elif page == "Competitor Analysis":
        competitor_analysis()
    elif page == "SEO Analytics":
        seo_analytics()
    elif page == "Reports":
        reports_view()
    elif page == "Settings":
        settings_page()

    # Footer
    st.markdown("---")
    st.caption("OnSide - Competitive Intelligence Platform | Demo Dashboard v1.0")

if __name__ == "__main__":
    main()
