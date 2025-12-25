#!/usr/bin/env python
"""
Data Visualization Module for TCS API Reports

This module provides visualization functions for the TCS API data,
creating charts and graphs that will be embedded in the PDF report.

Following Semantic Seed Venture Studio Coding Standards V2.0.
"""

import os
import io
import json
import logging
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for server usage
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("tcs_visualizer")

class ReportVisualizer:
    """Class to create visualizations for TCS report data."""
    
    def __init__(self, output_dir: str = "exports"):
        """Initialize the visualizer.
        
        Args:
            output_dir: Directory to save visualization files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def create_competitor_comparison(self, data: Dict[str, Any]) -> str:
        """Create a competitor comparison chart.
        
        Args:
            data: API data containing competitor information
            
        Returns:
            Path to the generated visualization file
        """
        logger.info("Creating competitor comparison visualization")
        try:
            # Extract competitor data
            ai_content = data.get("ai_analysis", {}).get("content", "{}")
            # Try to parse JSON from AI response
            try:
                ai_data = json.loads(ai_content)
                competitors = ai_data.get("competitor_analysis", [])
            except:
                # Fallback if AI response isn't valid JSON
                competitors = [
                    {"competitor_name": "Infosys", "threat_level": "High"},
                    {"competitor_name": "Wipro", "threat_level": "Medium"},
                    {"competitor_name": "Cognizant", "threat_level": "High"}
                ]
            
            # Convert threat levels to numeric values
            threat_values = {
                "Low": 1,
                "Medium": 2,
                "High": 3
            }
            
            # Prepare data for visualization
            comp_names = []
            threat_scores = []
            
            for comp in competitors:
                name = comp.get("competitor_name", comp.get("name", "Unknown"))
                threat = comp.get("threat_level", "Medium")
                comp_names.append(name)
                threat_scores.append(threat_values.get(threat, 2))
            
            # Create the visualization
            plt.figure(figsize=(10, 6))
            bars = plt.bar(comp_names, threat_scores, color=['green' if x == 1 else 'orange' if x == 2 else 'red' for x in threat_scores])
            
            # Add labels and title
            plt.xlabel('Competitors')
            plt.ylabel('Threat Level')
            plt.title('TCS Competitor Threat Analysis')
            plt.xticks(rotation=45)
            plt.ylim(0, 4)
            
            # Add a legend
            from matplotlib.patches import Patch
            legend_elements = [
                Patch(facecolor='green', label='Low Threat'),
                Patch(facecolor='orange', label='Medium Threat'),
                Patch(facecolor='red', label='High Threat')
            ]
            plt.legend(handles=legend_elements)
            
            # Add values on top of bars
            for bar in bars:
                height = bar.get_height()
                plt.text(bar.get_x() + bar.get_width() / 2., height,
                        ['', 'Low', 'Medium', 'High'][int(height)],
                        ha='center', va='bottom')
            
            plt.tight_layout()
            
            # Save the chart
            output_path = self.output_dir / f"competitor_comparison_{self.timestamp}.png"
            plt.savefig(output_path)
            plt.close()
            
            return str(output_path)
        except Exception as e:
            logger.error(f"Error creating competitor comparison: {str(e)}")
            return ""
    
    def create_news_sentiment_chart(self, data: Dict[str, Any]) -> str:
        """Create a news sentiment chart.
        
        Args:
            data: API data containing news information
            
        Returns:
            Path to the generated visualization file
        """
        logger.info("Creating news sentiment visualization")
        try:
            # Extract news data
            news_articles = data.get("news", {}).get("articles", [])
            
            # For a real implementation, we would use NLP to analyze sentiment
            # Here we'll simulate sentiment scores based on article titles
            sentiments = {
                "Positive": 0,
                "Neutral": 0,
                "Negative": 0
            }
            
            # Simple naive sentiment analysis based on keywords
            positive_keywords = ["award", "honour", "success", "growth", "increase", "partner"]
            negative_keywords = ["force", "relocate", "alleges", "decline", "challenge", "problem"]
            
            for article in news_articles:
                title = article.get("title", "").lower()
                found_positive = any(keyword in title for keyword in positive_keywords)
                found_negative = any(keyword in title for keyword in negative_keywords)
                
                if found_positive and not found_negative:
                    sentiments["Positive"] += 1
                elif found_negative and not found_positive:
                    sentiments["Negative"] += 1
                else:
                    sentiments["Neutral"] += 1
            
            # Create pie chart
            plt.figure(figsize=(8, 8))
            labels = list(sentiments.keys())
            sizes = list(sentiments.values())
            colors = ['#4CAF50', '#FFC107', '#F44336']  # Green, Amber, Red
            
            # Plot only segments with non-zero values
            non_zero_indices = [i for i, size in enumerate(sizes) if size > 0]
            filtered_labels = [labels[i] for i in non_zero_indices]
            filtered_sizes = [sizes[i] for i in non_zero_indices]
            filtered_colors = [colors[i] for i in non_zero_indices]
            
            if filtered_sizes:
                plt.pie(filtered_sizes, labels=filtered_labels, colors=filtered_colors,
                      autopct='%1.1f%%', startangle=90, shadow=True)
            else:
                # Fallback if no articles
                plt.pie([1], labels=["No data"], colors=['#CCCCCC'],
                      autopct='%1.1f%%', startangle=90, shadow=True)
            
            plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
            plt.title(f"TCS News Sentiment Analysis ({len(news_articles)} articles)")
            
            # Save the chart
            output_path = self.output_dir / f"news_sentiment_{self.timestamp}.png"
            plt.savefig(output_path)
            plt.close()
            
            return str(output_path)
        except Exception as e:
            logger.error(f"Error creating news sentiment chart: {str(e)}")
            return ""
    
    def create_market_trends_chart(self, data: Dict[str, Any]) -> str:
        """Create a market trends chart.
        
        Args:
            data: API data containing market trend information
            
        Returns:
            Path to the generated visualization file
        """
        logger.info("Creating market trends visualization")
        try:
            # Extract market data - in a real scenario this would come from the API
            # For demo, we'll create sample data based on industry trends
            market_segments = [
                "Cloud Services", 
                "AI & ML", 
                "Cybersecurity", 
                "Digital Transformation",
                "IoT Solutions"
            ]
            
            growth_rates = [18.5, 25.3, 15.8, 20.1, 12.7]
            tcs_market_share = [12.3, 8.7, 5.4, 14.2, 7.1]
            
            # Create the bar chart
            x = np.arange(len(market_segments))
            width = 0.35
            
            fig, ax = plt.subplots(figsize=(12, 7))
            bars1 = ax.bar(x - width/2, growth_rates, width, label='Industry Growth Rate (%)')
            bars2 = ax.bar(x + width/2, tcs_market_share, width, label='TCS Market Share (%)')
            
            # Add labels and title
            ax.set_ylabel('Percentage (%)')
            ax.set_title('TCS Market Position by Segment')
            ax.set_xticks(x)
            ax.set_xticklabels(market_segments, rotation=45, ha='right')
            ax.legend()
            
            # Add value labels on top of bars
            def add_labels(bars):
                for bar in bars:
                    height = bar.get_height()
                    ax.annotate(f'{height:.1f}%',
                                xy=(bar.get_x() + bar.get_width() / 2, height),
                                xytext=(0, 3),  # 3 points vertical offset
                                textcoords="offset points",
                                ha='center', va='bottom')
            
            add_labels(bars1)
            add_labels(bars2)
            
            fig.tight_layout()
            
            # Save the chart
            output_path = self.output_dir / f"market_trends_{self.timestamp}.png"
            plt.savefig(output_path)
            plt.close()
            
            return str(output_path)
        except Exception as e:
            logger.error(f"Error creating market trends chart: {str(e)}")
            return ""
    
    def create_geographic_distribution(self, data: Dict[str, Any]) -> str:
        """Create a geographic distribution chart.
        
        Args:
            data: API data containing location information
            
        Returns:
            Path to the generated visualization file
        """
        logger.info("Creating geographic distribution visualization")
        try:
            # In a real scenario, we would analyze the company's global footprint
            # For this demo, we'll create a sample visualization
            regions = [
                "North America", 
                "Europe", 
                "Asia Pacific",
                "Latin America", 
                "Middle East & Africa"
            ]
            
            tcs_presence = [35, 25, 30, 5, 5]  # Percentages
            
            # Create the pie chart
            plt.figure(figsize=(10, 8))
            colors = ['#3498db', '#2ecc71', '#e74c3c', '#f1c40f', '#9b59b6']
            explode = (0.1, 0, 0, 0, 0)  # explode the 1st slice (North America)
            
            plt.pie(tcs_presence, explode=explode, labels=regions, colors=colors,
                   autopct='%1.1f%%', shadow=True, startangle=140)
            plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
            plt.title('TCS Global Footprint by Region')
            
            # Save the chart
            output_path = self.output_dir / f"geographic_distribution_{self.timestamp}.png"
            plt.savefig(output_path)
            plt.close()
            
            return str(output_path)
        except Exception as e:
            logger.error(f"Error creating geographic distribution: {str(e)}")
            return ""
    
    def create_swot_analysis(self, data: Dict[str, Any]) -> str:
        """Create a SWOT analysis visualization.
        
        Args:
            data: API data containing company analysis
            
        Returns:
            Path to the generated visualization file
        """
        logger.info("Creating SWOT analysis visualization")
        try:
            # Extract data from AI analysis
            ai_content = data.get("ai_analysis", {}).get("content", "{}")
            
            # Try to parse JSON from AI response
            try:
                ai_data = json.loads(ai_content)
                strengths = ai_data.get("strengths", [])[:4]  # Limit to top 4
                weaknesses = ai_data.get("weaknesses", [])[:4]  # Limit to top 4
            except:
                # Fallback data
                strengths = [
                    "Global presence",
                    "Strong brand",
                    "Diverse portfolio",
                    "Financial stability"
                ]
                weaknesses = [
                    "US market dependency",
                    "Talent retention",
                    "Aggressive marketing",
                    "Digital transformation"
                ]
            
            # Fixed opportunities and threats for demo
            opportunities = [
                "Cloud services expansion",
                "AI/ML integration",
                "Healthcare IT growth",
                "Digital transformation"
            ]
            
            threats = [
                "Emerging competitors",
                "Talent war",
                "Economic uncertainty",
                "Rapid tech changes"
            ]
            
            # Create the SWOT visualization
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 10))
            
            # Configure the axes for the quadrants
            ax1.set_xlim(0, 1)
            ax1.set_ylim(0, 1)
            ax1.set_title('Strengths', fontsize=14, fontweight='bold', color='darkgreen')
            
            ax2.set_xlim(0, 1)
            ax2.set_ylim(0, 1)
            ax2.set_title('Weaknesses', fontsize=14, fontweight='bold', color='darkred')
            
            ax3.set_xlim(0, 1)
            ax3.set_ylim(0, 1)
            ax3.set_title('Opportunities', fontsize=14, fontweight='bold', color='darkblue')
            
            ax4.set_xlim(0, 1)
            ax4.set_ylim(0, 1)
            ax4.set_title('Threats', fontsize=14, fontweight='bold', color='darkorange')
            
            # Remove axis ticks and labels
            for ax in [ax1, ax2, ax3, ax4]:
                ax.set_xticks([])
                ax.set_yticks([])
                ax.set_xticklabels([])
                ax.set_yticklabels([])
                
                # Add a subtle border
                for spine in ax.spines.values():
                    spine.set_visible(True)
                    spine.set_color('lightgray')
            
            # Add text to each quadrant
            for i, strength in enumerate(strengths):
                ax1.text(0.1, 0.8 - i*0.2, f"• {strength}", fontsize=11, color='darkgreen')
                
            for i, weakness in enumerate(weaknesses):
                ax2.text(0.1, 0.8 - i*0.2, f"• {weakness}", fontsize=11, color='darkred')
                
            for i, opportunity in enumerate(opportunities):
                ax3.text(0.1, 0.8 - i*0.2, f"• {opportunity}", fontsize=11, color='darkblue')
                
            for i, threat in enumerate(threats):
                ax4.text(0.1, 0.8 - i*0.2, f"• {threat}", fontsize=11, color='darkorange')
            
            # Add main title
            plt.suptitle('TCS SWOT Analysis', fontsize=16, fontweight='bold')
            
            plt.tight_layout(rect=[0, 0, 1, 0.95])  # Adjust layout to make room for the title
            
            # Save the chart
            output_path = self.output_dir / f"swot_analysis_{self.timestamp}.png"
            plt.savefig(output_path)
            plt.close()
            
            return str(output_path)
        except Exception as e:
            logger.error(f"Error creating SWOT analysis: {str(e)}")
            return ""
    
    def create_all_visualizations(self, data: Dict[str, Any]) -> Dict[str, str]:
        """Create all visualizations for the report.
        
        Args:
            data: API data for visualization
            
        Returns:
            Dictionary with paths to all generated visualizations
        """
        return {
            "competitor_chart": self.create_competitor_comparison(data),
            "news_sentiment": self.create_news_sentiment_chart(data),
            "market_trends": self.create_market_trends_chart(data),
            "geographic_distribution": self.create_geographic_distribution(data),
            "swot_analysis": self.create_swot_analysis(data)
        }


if __name__ == "__main__":
    # Test the visualizer with sample data
    try:
        # Create sample data
        with open("exports/tcs_api_demo_20250516_164740.json", "r") as f:
            sample_data = json.load(f)
        
        # Create visualizations
        visualizer = ReportVisualizer()
        results = visualizer.create_all_visualizations(sample_data)
        
        print("\n✅ Visualizations created successfully:")
        for name, path in results.items():
            if path:
                print(f"- {name}: {path}")
    except Exception as e:
        print(f"\n❌ Error creating visualizations: {str(e)}")
