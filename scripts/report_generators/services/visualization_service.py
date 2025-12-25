#!/usr/bin/env python
"""
Visualization Service for OnSide Reports

This service provides data visualization capabilities including:
- Financial charts
- Market share visualizations
- Sentiment analysis charts
- Geographic maps
"""

import logging
from typing import Dict, List, Any, Optional, Tuple, Union
import os
import io
import base64
from datetime import datetime, timedelta
import random

# Try to import matplotlib
MATPLOTLIB_AVAILABLE = True
try:
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    from matplotlib import gridspec
    from mpl_toolkits.axes_grid1 import make_axes_locatable
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("matplotlib not available. Some visualizations may not work.")

# Try to import pandas and numpy
try:
    import pandas as pd
    import numpy as np
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("pandas or numpy not available. Some visualizations may not work.")

# Try to import plotly for interactive charts
try:
    import plotly.graph_objects as go
    import plotly.express as px
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("Plotly not available. Falling back to static matplotlib charts.")

class VisualizationService:
    """Service for creating visualizations for reports."""
    
    def __init__(self, output_dir: str = 'exports/visualizations'):
        """Initialize the visualization service."""
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # Set up colors
        self.colors = {
            'primary': '#3498db',    # Blue
            'secondary': '#2ecc71',  # Green
            'accent': '#e74c3c',     # Red
            'dark': '#2c3e50',       # Dark blue/gray
            'light': '#ecf0f1'       # Light gray
        }
        
        # Set up matplotlib if available
        if MATPLOTLIB_AVAILABLE:
            try:
                available_styles = plt.style.available
                # Try to use a modern style if available, otherwise use default
                if 'seaborn' in available_styles:
                    plt.style.use('seaborn')
                elif 'ggplot' in available_styles:
                    plt.style.use('ggplot')
                elif 'bmh' in available_styles:
                    plt.style.use('bmh')
                else:
                    # Use default style with custom colors
                    plt.style.use('default')
            except Exception as e:
                logger.warning(f"Failed to set matplotlib style: {str(e)}")
        else:
            logger.warning("matplotlib not available. Visualizations will be limited.")
    
    def create_revenue_chart(self, financial_data: Dict[str, Any]) -> str:
        """
        Create a revenue trend chart.
        
        Args:
            financial_data: Dictionary containing financial data with 'revenue_history'
            
        Returns:
            Path to the saved chart image or base64 encoded string for HTML
        """
        if PLOTLY_AVAILABLE and self._is_interactive():
            return self._create_plotly_revenue_chart(financial_data)
        else:
            return self._create_static_revenue_chart(financial_data)
    
    def _create_plotly_revenue_chart(self, financial_data: Dict[str, Any]) -> str:
        """Create an interactive revenue chart using Plotly."""
        try:
            # Prepare data
            df = pd.DataFrame(financial_data.get('revenue_history', []))
            if df.empty:
                return self._generate_placeholder_chart('No revenue data available')
                
            # Create figure
            fig = go.Figure()
            
            # Add revenue line
            fig.add_trace(go.Scatter(
                x=df['date'],
                y=df['revenue'],
                mode='lines+markers',
                name='Revenue',
                line=dict(color=self.colors['primary'], width=3),
                marker=dict(size=8)
            ))
            
            # Add growth rate if available
            if 'growth_rate' in df.columns:
                # Create secondary y-axis for growth rate
                fig.add_trace(go.Scatter(
                    x=df['date'],
                    y=df['growth_rate'] * 100,  # Convert to percentage
                    mode='lines',
                    name='Growth Rate %',
                    line=dict(color=self.colors['accent'], width=2, dash='dot'),
                    yaxis='y2'
                ))
            
            # Update layout
            fig.update_layout(
                title='Revenue Trend Over Time',
                xaxis_title='Date',
                yaxis_title='Revenue ($M)',
                yaxis2=dict(
                    title='Growth Rate (%)',
                    overlaying='y',
                    side='right',
                    range=[0, df['growth_rate'].max() * 120] if 'growth_rate' in df.columns else None
                ),
                legend=dict(orientation='h', y=1.1),
                template='plotly_white',
                hovermode='x unified',
                margin=dict(l=50, r=50, t=80, b=50)
            )
            
            # Save as HTML
            output_path = os.path.join(self.output_dir, 'revenue_chart.html')
            fig.write_html(output_path, include_plotlyjs='cdn')
            
            # Return the HTML content as a string
            with open(output_path, 'r') as f:
                return f.read()
                
        except Exception as e:
            logger.error(f"Error creating Plotly revenue chart: {str(e)}")
            return self._generate_placeholder_chart('Error generating chart')
    
    def _create_static_revenue_chart(self, financial_data: Dict[str, Any]) -> str:
        """Create a static revenue chart using Matplotlib."""
        try:
            # Prepare data
            df = pd.DataFrame(financial_data.get('revenue_history', []))
            if df.empty:
                return self._generate_placeholder_chart('No revenue data available')
            
            # Create figure and axis
            fig, ax1 = plt.subplots(figsize=(10, 6))
            
            # Plot revenue
            ax1.plot(df['date'], df['revenue'], 
                    marker='o', 
                    color=self.colors['primary'], 
                    linewidth=2,
                    label='Revenue')
            
            ax1.set_xlabel('Date')
            ax1.set_ylabel('Revenue ($M)', color=self.colors['dark'])
            ax1.tick_params(axis='y', labelcolor=self.colors['dark'])
            
            # Add growth rate if available
            if 'growth_rate' in df.columns:
                ax2 = ax1.twinx()
                ax2.plot(df['date'], df['growth_rate'] * 100, 
                         color=self.colors['accent'], 
                         linestyle='--', 
                         linewidth=2,
                         label='Growth Rate %')
                ax2.set_ylabel('Growth Rate (%)', color=self.colors['accent'])
                ax2.tick_params(axis='y', labelcolor=self.colors['accent'])
            
            # Customize the plot
            plt.title('Revenue Trend Over Time', pad=20)
            fig.tight_layout()
            
            # Save the plot
            output_path = os.path.join(self.output_dir, 'revenue_chart.png')
            plt.savefig(output_path, bbox_inches='tight', dpi=300)
            plt.close()
            
            # Return base64 encoded image for HTML embedding
            return self._get_image_base64(output_path)
            
        except Exception as e:
            logger.error(f"Error creating static revenue chart: {str(e)}")
            return self._generate_placeholder_chart('Error generating chart')
    
    def create_market_share_chart(self, market_data: Dict[str, Any]) -> str:
        """
        Create a market share visualization.
        
        Args:
            market_data: Dictionary containing market share data with 'companies' list
            
        Returns:
            HTML string, base64 encoded image, or text summary
        """
        try:
            # Check if we have valid data
            companies = market_data.get('companies', [])
            if not companies:
                return self._generate_placeholder_chart('No market share data available')
            
            # If no visualization libraries are available, return a text summary
            if not MATPLOTLIB_AVAILABLE and not PLOTLY_AVAILABLE:
                return self._generate_market_share_text(companies)
            
            # Try to use Plotly if available and interactive mode is enabled
            if PLOTLY_AVAILABLE and self._is_interactive():
                try:
                    return self._create_plotly_market_share_chart(market_data)
                except Exception as e:
                    logger.warning(f"Failed to create Plotly chart: {str(e)}")
            
            # Fall back to static matplotlib chart
            if MATPLOTLIB_AVAILABLE:
                try:
                    return self._create_static_market_share_chart(market_data)
                except Exception as e:
                    logger.warning(f"Failed to create static chart: {str(e)}")
            
            # If all else fails, return a text summary
            return self._generate_market_share_text(companies)
            
        except Exception as e:
            logger.error(f"Error in create_market_share_chart: {str(e)}", exc_info=True)
            return self._generate_placeholder_chart('Error generating market share visualization')
    
    def _generate_market_share_text(self, companies: List[Dict]) -> str:
        """Generate a text-based market share summary."""
        try:
            if not companies:
                return "No market share data available."
                
            # Sort companies by market share (descending)
            companies_sorted = sorted(companies, key=lambda x: x.get('market_share', 0), reverse=True)
            
            # Generate the text summary
            lines = ["Market Share Summary:", "=" * 40]
            for i, company in enumerate(companies_sorted[:10], 1):  # Limit to top 10
                name = company.get('name', 'Unknown')
                share = company.get('market_share', 0)
                lines.append(f"{i}. {name}: {share:.1f}%")
            
            # Add a note if there are more companies
            if len(companies) > 10:
                lines.append(f"\n... and {len(companies) - 10} more companies")
                
            return "\n".join(lines)
            
        except Exception as e:
            logger.error(f"Error generating market share text: {str(e)}", exc_info=True)
            return "Error generating market share summary."
    
    def _create_plotly_market_share_chart(self, market_data: Dict[str, Any]) -> str:
        """Create an interactive market share chart using Plotly."""
        try:
            # Prepare data
            companies = market_data.get('companies', [])
            if not companies:
                return self._generate_placeholder_chart('No market share data available')
            
            # Create figure
            fig = go.Figure(data=[
                go.Pie(
                    labels=[c['name'] for c in companies],
                    values=[c['market_share'] for c in companies],
                    textinfo='percent+label',
                    hoverinfo='label+percent+value',
                    hole=0.3,
                    marker=dict(colors=[self._get_company_color(c['name']) for c in companies])
                )
            ])
            
            # Update layout
            fig.update_layout(
                title='Market Share Distribution',
                showlegend=False,
                template='plotly_white',
                margin=dict(l=20, r=20, t=40, b=20)
            )
            
            # Save as HTML
            output_path = os.path.join(self.output_dir, 'market_share_chart.html')
            fig.write_html(output_path, include_plotlyjs='cdn')
            
            # Return the HTML content as a string
            with open(output_path, 'r') as f:
                return f.read()
                
        except Exception as e:
            logger.error(f"Error creating Plotly market share chart: {str(e)}")
            return self._generate_placeholder_chart('Error generating chart')
    
    def _create_static_market_share_chart(self, market_data: Dict[str, Any]) -> str:
        """Create a static market share chart using Matplotlib."""
        try:
            # Prepare data
            companies = market_data.get('companies', [])
            if not companies:
                return self._generate_placeholder_chart('No market share data available')
            
            # Sort companies by market share
            companies_sorted = sorted(companies, key=lambda x: x['market_share'], reverse=True)
            
            # Create figure
            fig, ax = plt.subplots(figsize=(10, 6))
            
            # Create pie chart
            wedges, texts, autotexts = ax.pie(
                [c['market_share'] for c in companies_sorted],
                labels=[c['name'] for c in companies_sorted],
                autopct='%1.1f%%',
                startangle=90,
                colors=[self._get_company_color(c['name']) for c in companies_sorted],
                wedgeprops=dict(width=0.6, edgecolor='w')
            )
            
            # Customize the plot
            plt.setp(autotexts, size=10, weight='bold', color='white')
            plt.title('Market Share Distribution', pad=20)
            
            # Equal aspect ratio ensures that pie is drawn as a circle
            ax.axis('equal')
            
            # Save the plot
            output_path = os.path.join(self.output_dir, 'market_share_chart.png')
            plt.savefig(output_path, bbox_inches='tight', dpi=300, transparent=True)
            plt.close()
            
            # Return base64 encoded image for HTML embedding
            return self._get_image_base64(output_path)
            
        except Exception as e:
            logger.error(f"Error creating static market share chart: {str(e)}")
            return self._generate_placeholder_chart('Error generating chart')
    
    def create_sentiment_chart(self, sentiment_data: Dict[str, Any]) -> str:
        """Create a sentiment analysis visualization."""
        if PLOTLY_AVAILABLE and self._is_interactive():
            return self._create_plotly_sentiment_chart(sentiment_data)
        else:
            return self._create_static_sentiment_chart(sentiment_data)
    
    def _create_plotly_sentiment_chart(self, sentiment_data: Dict[str, Any]) -> str:
        """Create an interactive sentiment chart using Plotly."""
        try:
            # Prepare data
            sentiment_dist = sentiment_data.get('sentiment_distribution', {})
            if not sentiment_dist:
                return self._generate_placeholder_chart('No sentiment data available')
            
            # Create figure
            fig = go.Figure()
            
            # Add bars for sentiment distribution
            sentiment_colors = {
                'positive': self.colors['secondary'],
                'neutral': self.colors['primary'],
                'negative': self.colors['accent']
            }
            
            for sentiment, value in sentiment_dist.items():
                fig.add_trace(go.Bar(
                    x=[sentiment.capitalize()],
                    y=[value * 100],  # Convert to percentage
                    name=sentiment.capitalize(),
                    marker_color=sentiment_colors.get(sentiment, self.colors['primary']),
                    text=[f'{value*100:.1f}%'],
                    textposition='auto',
                    width=0.6
                ))
            
            # Update layout
            fig.update_layout(
                title='Sentiment Distribution',
                yaxis=dict(
                    title='Percentage',
                    range=[0, 100],
                    tickformat='.0f%'
                ),
                showlegend=False,
                template='plotly_white',
                margin=dict(l=50, r=50, t=80, b=50)
            )
            
            # Save as HTML
            output_path = os.path.join(self.output_dir, 'sentiment_chart.html')
            fig.write_html(output_path, include_plotlyjs='cdn')
            
            # Return the HTML content as a string
            with open(output_path, 'r') as f:
                return f.read()
                
        except Exception as e:
            logger.error(f"Error creating Plotly sentiment chart: {str(e)}")
            return self._generate_placeholder_chart('Error generating chart')
    
    def _create_static_sentiment_chart(self, sentiment_data: Dict[str, Any]) -> str:
        """Create a static sentiment chart using Matplotlib."""
        try:
            # Prepare data
            sentiment_dist = sentiment_data.get('sentiment_distribution', {})
            if not sentiment_dist:
                return self._generate_placeholder_chart('No sentiment data available')
            
            # Create figure
            fig, ax = plt.subplots(figsize=(8, 6))
            
            # Define colors
            colors = [
                self.colors['accent'],    # Negative (red)
                self.colors['primary'],   # Neutral (blue)
                self.colors['secondary']  # Positive (green)
            ]
            
            # Create horizontal bar chart
            sentiments = ['Negative', 'Neutral', 'Positive']
            values = [sentiment_dist.get(s.lower(), 0) * 100 for s in sentiments]  # Convert to percentage
            
            bars = ax.barh(sentiments, values, color=colors, height=0.6)
            
            # Add value labels
            for bar in bars:
                width = bar.get_width()
                ax.text(width + 2, bar.get_y() + bar.get_height()/2.,
                       f'{width:.1f}%',
                       ha='left', va='center',
                       fontsize=10, fontweight='bold')
            
            # Customize the plot
            ax.set_xlim(0, 100)
            ax.set_xlabel('Percentage')
            ax.set_title('Sentiment Distribution', pad=20)
            ax.grid(axis='x', linestyle='--', alpha=0.7)
            
            # Remove borders
            for spine in ['top', 'right', 'bottom', 'left']:
                ax.spines[spine].set_visible(False)
            
            # Save the plot
            output_path = os.path.join(self.output_dir, 'sentiment_chart.png')
            plt.savefig(output_path, bbox_inches='tight', dpi=300, transparent=True)
            plt.close()
            
            # Return base64 encoded image for HTML embedding
            return self._get_image_base64(output_path)
            
        except Exception as e:
            logger.error(f"Error creating static sentiment chart: {str(e)}")
            return self._generate_placeholder_chart('Error generating chart')
    
    def create_geographic_map(self, location_data: Dict[str, Any]) -> str:
        """
        Create a geographic map visualization.
        
        Args:
            location_data: Dictionary containing location data with 'locations' list
            
        Returns:
            Path to the saved map image or base64 encoded string for HTML
        """
        if PLOTLY_AVAILABLE and self._is_interactive():
            return self._create_plotly_map(location_data)
        else:
            return self._create_static_map(location_data)
    
    def _create_plotly_map(self, location_data: Dict[str, Any]) -> str:
        """Create an interactive map using Plotly."""
        try:
            # Prepare data
            locations = location_data.get('locations', [])
            if not locations:
                return self._generate_placeholder_chart('No location data available')
            
            # Create DataFrame
            df = pd.DataFrame(locations)
            
            # Create figure
            fig = go.Figure()
            
            # Add scatter plot for locations
            fig.add_trace(go.Scattergeo(
                lon=df['longitude'],
                lat=df['latitude'],
                text=df['name'],
                mode='markers',
                marker=dict(
                    size=df.get('size', 10),
                    color=self.colors['primary'],
                    opacity=0.8,
                    line=dict(width=1, color='rgba(0, 0, 0, 0.5)')
                ),
                name='Locations'
            ))
            
            # Update layout
            fig.update_geos(
                projection_type='natural earth',
                showcountries=True,
                countrycolor='gray',
                showocean=True,
                oceancolor='#e6f2ff',
                showlakes=True,
                lakecolor='#e6f2ff',
                showland=True,
                landcolor='white',
                showcoastlines=True,
                coastlinecolor='gray'
            )
            
            fig.update_layout(
                title='Global Presence',
                geo=dict(
                    showframe=False,
                    showcoastlines=True,
                    projection_scale=1.5,
                    center=dict(lat=20, lon=0),
                ),
                margin=dict(l=0, r=0, t=40, b=0),
                height=500
            )
            
            # Save as HTML
            output_path = os.path.join(self.output_dir, 'geographic_map.html')
            fig.write_html(output_path, include_plotlyjs='cdn')
            
            # Return the HTML content as a string
            with open(output_path, 'r') as f:
                return f.read()
                
        except Exception as e:
            logger.error(f"Error creating Plotly map: {str(e)}")
            return self._generate_placeholder_chart('Error generating map')
    
    def _create_static_map(self, location_data: Dict[str, Any]) -> str:
        """Create a static map using Basemap or similar."""
        try:
            # This is a simplified version - in a real implementation, you would use Basemap or similar
            # For now, we'll return a placeholder
            return self._generate_placeholder_chart('Interactive map not available in static mode')
            
        except Exception as e:
            logger.error(f"Error creating static map: {str(e)}")
            return self._generate_placeholder_chart('Error generating map')
    
    def _get_company_color(self, company_name: str) -> str:
        """Get a consistent color for a company."""
        # This is a simple hash function to generate consistent colors
        # In a real implementation, you might want to define specific colors for major companies
        color_list = [
            self.colors['primary'],
            self.colors['secondary'],
            self.colors['accent'],
            '#9b59b6',  # Purple
            '#f1c40f',  # Yellow
            '#e67e22',  # Orange
            '#1abc9c',  # Turquoise
            '#d35400'   # Pumpkin
        ]
        
        # Simple hash function to get a consistent index
        hash_val = sum(ord(c) for c in company_name) % len(color_list)
        return color_list[hash_val]
    
    def _is_interactive(self) -> bool:
        """Check if interactive visualizations should be used."""
        # In a real implementation, this could check user preferences or environment
        return PLOTLY_AVAILABLE  # Only use interactive if Plotly is available
        
    def _generate_placeholder_chart(self, message: str) -> str:
        """
        Generate a placeholder chart or text message when visualization is not possible.
        
        Args:
            message: The message to display
            
        Returns:
            HTML string or plain text message
        """
        try:
            # If matplotlib is available, create a simple text plot
            if MATPLOTLIB_AVAILABLE:
                try:
                    fig, ax = plt.subplots(figsize=(8, 4))
                    ax.text(0.5, 0.5, message,
                           horizontalalignment='center',
                           verticalalignment='center',
                           transform=ax.transAxes,
                           fontsize=12,
                           color='gray')
                    ax.axis('off')
                    
                    # Save the plot
                    output_path = os.path.join(self.output_dir, 'placeholder.png')
                    plt.savefig(output_path, bbox_inches='tight', dpi=100)
                    plt.close()
                    
                    return self._get_image_base64(output_path)
                except Exception as e:
                    logger.warning(f"Failed to generate matplotlib placeholder: {str(e)}")
            
            # Fall back to HTML/CSS if we can't generate an image
            return (
                f"<div style='padding:20px;margin:10px;background-color:#f8f9fa;"
                f"border:1px solid #dee2e6;border-radius:4px;color:#6c757d;"
                f"font-family:Arial,sans-serif;text-align:center;'>"
                f"<p style='margin:0;font-size:14px;'>{message}</p>"
                f"</div>"
            )
            
        except Exception as e:
            logger.error(f"Error in _generate_placeholder_chart: {str(e)}", exc_info=True)
            # Last resort: return plain text
            return f"[Visualization Error: {message}]"
    
    def _get_image_base64(self, image_path: str) -> str:
        """Convert an image to base64 for HTML embedding."""
        try:
            with open(image_path, 'rb') as img_file:
                return f"data:image/png;base64,{base64.b64encode(img_file.read()).decode()}"
        except Exception as e:
            logger.error(f"Error converting image to base64: {str(e)}")
            return ''

# Example usage
if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Example data
    financial_data = {
        'revenue_history': [
            {'date': '2023-01-01', 'revenue': 150, 'growth_rate': 0.05},
            {'date': '2023-04-01', 'revenue': 165, 'growth_rate': 0.10},
            {'date': '2023-07-01', 'revenue': 180, 'growth_rate': 0.09},
            {'date': '2023-10-01', 'revenue': 200, 'growth_rate': 0.11},
        ]
    }
    
    market_data = {
        'companies': [
            {'name': 'TCS', 'market_share': 35},
            {'name': 'Infosys', 'market_share': 25},
            {'name': 'Wipro', 'market_share': 20},
            {'name': 'HCL', 'market_share': 15},
            {'name': 'Others', 'market_share': 5}
        ]
    }
    
    sentiment_data = {
        'sentiment_distribution': {
            'positive': 0.6,
            'neutral': 0.3,
            'negative': 0.1
        }
    }
    
    location_data = {
        'locations': [
            {'name': 'Mumbai', 'latitude': 19.0760, 'longitude': 72.8777, 'size': 20},
            {'name': 'Bangalore', 'latitude': 12.9716, 'longitude': 77.5946, 'size': 15},
            {'name': 'New York', 'latitude': 40.7128, 'longitude': -74.0060, 'size': 25},
            {'name': 'London', 'latitude': 51.5074, 'longitude': -0.1278, 'size': 20},
            {'name': 'Singapore', 'latitude': 1.3521, 'longitude': 103.8198, 'size': 15}
        ]
    }
    
    # Create visualizations
    viz = VisualizationService()
    
    # Generate charts
    revenue_chart = viz.create_revenue_chart(financial_data)
    market_share_chart = viz.create_market_share_chart(market_data)
    sentiment_chart = viz.create_sentiment_chart(sentiment_data)
    geographic_map = viz.create_geographic_map(location_data)
    
    print("Visualizations generated successfully!")
    print(f"Revenue chart: {revenue_chart[:100]}..." if isinstance(revenue_chart, str) else "Revenue chart generated")
    print(f"Market share chart: {market_share_chart[:100]}..." if isinstance(market_share_chart, str) else "Market share chart generated")
    print(f"Sentiment chart: {sentiment_chart[:100]}..." if isinstance(sentiment_chart, str) else "Sentiment chart generated")
    print(f"Geographic map: {geographic_map[:100]}..." if isinstance(geographic_map, str) else "Geographic map generated")
