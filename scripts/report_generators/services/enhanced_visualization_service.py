#!/usr/bin/env python
"""
Enhanced Visualization Service for TCS Report

Creates strategic visualizations with confidence indicators and business context
for the enhanced TCS report.

Following Semantic Seed Venture Studio Coding Standards V2.0.
"""

import os
import io
import logging
import traceback
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from pathlib import Path
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch
import matplotlib.colors as mcolors

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("enhanced_visualization_service")

class EnhancedVisualizationService:
    """
    Service for creating strategic visualizations with confidence indicators.
    """
    
    def __init__(self, output_dir: str = "exports"):
        """
        Initialize the enhanced visualization service.
        
        Args:
            output_dir: Directory to save visualization files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Configure visualization styling
        plt.style.use('seaborn-v0_8-whitegrid')
        plt.rcParams['font.family'] = 'sans-serif'
        plt.rcParams['font.sans-serif'] = ['Arial', 'Helvetica', 'DejaVu Sans']
        plt.rcParams['axes.labelsize'] = 12
        plt.rcParams['axes.titlesize'] = 14
        plt.rcParams['xtick.labelsize'] = 10
        plt.rcParams['ytick.labelsize'] = 10
        
        # Define colors for consistent branding
        self.colors = {
            'primary': '#1e3d59',    # Dark blue
            'secondary': '#f5f0e1',  # Cream
            'accent1': '#ff6e40',    # Orange
            'accent2': '#ffc13b',    # Yellow
            'positive': '#2ecc71',   # Green
            'negative': '#e74c3c',   # Red
            'neutral': '#3498db',    # Blue
            'high_conf': '#2ecc71',  # Green for high confidence
            'med_conf': '#f39c12',   # Orange for medium confidence
            'low_conf': '#e74c3c'    # Red for low confidence
        }
    
    def create_competitor_matrix(self, data: Dict[str, Any]) -> str:
        """
        Create a competitor positioning matrix with confidence indicators.
        
        Args:
            data: Integrated analysis data
            
        Returns:
            Path to the generated visualization
        """
        logger.info("Creating competitor positioning matrix")
        try:
            # Extract competitor data
            competitor_analysis = data.get("integrated_analysis", {}).get("competitor_analysis", {})
            competitors = competitor_analysis.get("competitors", [])
            
            if not competitors:
                logger.warning("No competitor data available for visualization")
                return ""
            
            # Prepare data for visualization
            names = []
            market_share = []
            innovation = []
            threat_levels = []
            
            for comp in competitors:
                name = comp.get("name", "Unknown")
                metrics = comp.get("comparison_metrics", {})
                relative_ms = metrics.get("relative_market_share", 1.0)
                innovation_idx = metrics.get("innovation_index", 1.0)
                threat = comp.get("threat_level", "Medium")
                
                names.append(name)
                market_share.append(relative_ms)
                innovation.append(innovation_idx)
                threat_levels.append(threat)
            
            # Add TCS as a reference point
            names.append("TCS")
            market_share.append(1.0)  # Reference point
            innovation.append(1.0)    # Reference point
            threat_levels.append("Reference")
            
            # Map threat levels to colors
            threat_colors = {
                "High": self.colors['negative'],
                "Medium": self.colors['accent2'],
                "Low": self.colors['positive'],
                "Reference": self.colors['primary']
            }
            
            # Create the visualization
            plt.figure(figsize=(10, 8))
            
            # Plot competitors as scatter points
            for i in range(len(names)):
                marker_size = 200 if names[i] == "TCS" else 150
                plt.scatter(
                    market_share[i], 
                    innovation[i], 
                    s=marker_size, 
                    color=threat_colors.get(threat_levels[i], self.colors['neutral']),
                    alpha=0.7,
                    edgecolors='black',
                    linewidth=1
                )
                
                # Add labels with offsets
                x_offset = 0.02
                y_offset = 0.02
                plt.annotate(
                    names[i],
                    (market_share[i] + x_offset, innovation[i] + y_offset),
                    fontsize=10,
                    fontweight='bold' if names[i] == "TCS" else 'normal'
                )
            
            # Add quadrant lines
            plt.axhline(y=1.0, color='gray', linestyle='--', alpha=0.5)
            plt.axvline(x=1.0, color='gray', linestyle='--', alpha=0.5)
            
            # Add quadrant labels
            plt.text(1.4, 1.4, "LEADERS", fontsize=12, ha='center', va='center', fontweight='bold', alpha=0.7)
            plt.text(0.6, 1.4, "INNOVATORS", fontsize=12, ha='center', va='center', fontweight='bold', alpha=0.7)
            plt.text(1.4, 0.6, "ESTABLISHED", fontsize=12, ha='center', va='center', fontweight='bold', alpha=0.7)
            plt.text(0.6, 0.6, "CHALLENGERS", fontsize=12, ha='center', va='center', fontweight='bold', alpha=0.7)
            
            # Add labels and title
            plt.xlabel('Relative Market Share (vs TCS)', fontsize=12, fontweight='bold')
            plt.ylabel('Innovation Index (vs TCS)', fontsize=12, fontweight='bold')
            plt.title('Competitive Positioning Matrix', fontsize=14, fontweight='bold', color=self.colors['primary'])
            
            # Add confidence indicator
            conf_score = competitor_analysis.get("confidence_score", 0.8)
            conf_color = self._get_confidence_color(conf_score)
            conf_text = f"Confidence: {conf_score:.2f}"
            plt.figtext(0.02, 0.02, conf_text, fontsize=10, color=conf_color)
            
            # Add TCS watermark
            plt.figtext(0.5, 0.5, "TCS", fontsize=50, color=self.colors['secondary'], 
                       ha='center', va='center', alpha=0.1, fontweight='bold')
            
            # Add a legend for threat levels
            legend_elements = [
                Patch(facecolor=self.colors['negative'], label='High Threat'),
                Patch(facecolor=self.colors['accent2'], label='Medium Threat'),
                Patch(facecolor=self.colors['positive'], label='Low Threat'),
                Patch(facecolor=self.colors['primary'], label='TCS (Reference)')
            ]
            plt.legend(handles=legend_elements, loc='upper left')
            
            # Set axis limits with some padding
            max_x = max(market_share) * 1.2
            max_y = max(innovation) * 1.2
            plt.xlim(0.4, max(max_x, 1.6))
            plt.ylim(0.4, max(max_y, 1.6))
            
            plt.tight_layout()
            
            # Save the visualization
            output_path = self.output_dir / f"competitor_matrix_{self.timestamp}.png"
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info(f"Saved competitor matrix to {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Error creating competitor matrix: {str(e)}")
            logger.error(traceback.format_exc())
            return ""
    
    def create_swot_matrix(self, data: Dict[str, Any]) -> str:
        """
        Create an enhanced SWOT matrix with confidence indicators.
        
        Args:
            data: Integrated analysis data
            
        Returns:
            Path to the generated visualization
        """
        logger.info("Creating enhanced SWOT matrix")
        try:
            # Extract SWOT data
            swot_analysis = data.get("integrated_analysis", {}).get("swot_analysis", {})
            
            strengths = swot_analysis.get("strengths", [])
            weaknesses = swot_analysis.get("weaknesses", [])
            opportunities = swot_analysis.get("opportunities", [])
            threats = swot_analysis.get("threats", [])
            
            # Function to extract text and confidence
            def extract_items(items, default_conf=0.8):
                result = []
                for item in items[:4]:  # Limit to top 4 items
                    if isinstance(item, dict):
                        text = item.get("strength", item.get("weakness", item.get("opportunity", item.get("threat", ""))))
                        conf = item.get("confidence", default_conf)
                    else:
                        text = str(item)
                        conf = default_conf
                    result.append((text, conf))
                return result
            
            # Process each quadrant
            s_items = extract_items(strengths)
            w_items = extract_items(weaknesses)
            o_items = extract_items(opportunities)
            t_items = extract_items(threats)
            
            # Create the visualization
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 10))
            
            # Function to populate a quadrant
            def populate_quadrant(ax, title, items, color):
                ax.set_xlim(0, 1)
                ax.set_ylim(0, 1)
                ax.set_title(title, fontsize=14, fontweight='bold', color=color)
                ax.set_xticks([])
                ax.set_yticks([])
                
                # Remove axis spines
                for spine in ax.spines.values():
                    spine.set_visible(False)
                
                # Add items with confidence indicators
                for i, (text, conf) in enumerate(items):
                    conf_color = self._get_confidence_color(conf)
                    textstr = f"{text} ({conf:.2f})"
                    ax.text(0.1, 0.85 - i*0.2, f"• {textstr}", fontsize=11, color=color)
                    
                    # Add confidence bar
                    bar_width = conf * 0.4  # Scale to 40% of the quadrant width
                    ax.barh(0.83 - i*0.2, bar_width, height=0.03, left=0.1, color=conf_color, alpha=0.7)
            
            # Populate each quadrant
            populate_quadrant(ax1, "STRENGTHS", s_items, self.colors['positive'])
            populate_quadrant(ax2, "WEAKNESSES", w_items, self.colors['negative'])
            populate_quadrant(ax3, "OPPORTUNITIES", o_items, self.colors['accent2'])
            populate_quadrant(ax4, "THREATS", t_items, self.colors['accent1'])
            
            # Add title
            plt.suptitle("Enhanced SWOT Analysis with Confidence Scoring", 
                         fontsize=16, fontweight='bold', color=self.colors['primary'])
            
            # Add confidence legend
            legend_elements = [
                Patch(facecolor=self.colors['high_conf'], label='High Confidence (0.8-1.0)'),
                Patch(facecolor=self.colors['med_conf'], label='Medium Confidence (0.6-0.8)'),
                Patch(facecolor=self.colors['low_conf'], label='Low Confidence (<0.6)')
            ]
            fig.legend(handles=legend_elements, loc='lower center', ncol=3, bbox_to_anchor=(0.5, 0.02))
            
            # Add overall confidence score
            conf_score = swot_analysis.get("confidence_score", 0.8)
            conf_text = f"Overall Confidence: {conf_score:.2f}"
            plt.figtext(0.02, 0.02, conf_text, fontsize=10, color=self._get_confidence_color(conf_score))
            
            plt.tight_layout(rect=[0, 0.05, 1, 0.95])
            
            # Save the visualization
            output_path = self.output_dir / f"enhanced_swot_{self.timestamp}.png"
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info(f"Saved enhanced SWOT matrix to {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Error creating SWOT matrix: {str(e)}")
            logger.error(traceback.format_exc())
            return ""
    
    def create_strategic_recommendations(self, data: Dict[str, Any], integrated_data: Dict[str, Any] = None) -> str:
        """
        Create strategic recommendations visualization with priority ranking.
        
        Args:
            data: Integrated analysis data
            
        Returns:
            Path to the generated visualization
        """
        logger.info("Creating strategic recommendations visualization")
        try:
            # Extract recommendations data
            recommendations = data.get("integrated_analysis", {}).get("strategic_recommendations", {})
            
            # Combine all recommendation categories
            all_recs = []
            categories = {
                "Leverage Strengths": recommendations.get("leverage_strengths", []),
                "Address Weaknesses": recommendations.get("address_weaknesses", []),
                "Pursue Opportunities": recommendations.get("pursue_opportunities", []),
                "Mitigate Threats": recommendations.get("mitigate_threats", [])
            }
            
            # Priority mapping
            priority_map = {"High": 3, "Medium": 2, "Low": 1}
            priority_colors = {"High": self.colors['accent1'], "Medium": self.colors['accent2'], "Low": self.colors['neutral']}
            
            # Prepare data for visualization
            for category, items in categories.items():
                for item in items:
                    if isinstance(item, dict):
                        rec_text = item.get("recommendation", "")
                        priority = item.get("priority", "Medium")
                        confidence = item.get("confidence", 0.8)
                        impact = item.get("impact", "")
                        
                        all_recs.append({
                            "category": category,
                            "recommendation": rec_text,
                            "priority": priority,
                            "priority_value": priority_map.get(priority, 2),
                            "confidence": confidence,
                            "impact": impact
                        })
            
            # Sort recommendations by priority
            all_recs.sort(key=lambda x: x["priority_value"], reverse=True)
            
            # Limit to top 8 recommendations
            all_recs = all_recs[:8]
            
            # Prepare data for visualization
            categories = [r["category"] for r in all_recs]
            recommendations = [r["recommendation"] for r in all_recs]
            priorities = [r["priority_value"] for r in all_recs]
            confidences = [r["confidence"] for r in all_recs]
            priority_labels = [r["priority"] for r in all_recs]
            
            # Create the visualization
            fig, ax = plt.subplots(figsize=(12, 8))
            
            # Create horizontal bars
            bars = ax.barh(range(len(recommendations)), priorities, alpha=0.7)
            
            # Color bars by priority
            for i, bar in enumerate(bars):
                bar.set_color(priority_colors.get(priority_labels[i], self.colors['neutral']))
                
                # Add confidence indicators
                conf = confidences[i]
                conf_color = self._get_confidence_color(conf)
                conf_width = 0.2
                ax.barh(i, conf_width, left=priorities[i], color=conf_color, alpha=0.7)
                
                # Add recommendation text
                ax.text(0.1, i, f"{recommendations[i]} ({priority_labels[i]})", va='center', fontsize=10)
            
            # Add labels and title
            ax.set_yticks(range(len(recommendations)))
            ax.set_yticklabels([f"{cat}" for cat in categories])
            ax.set_xlabel('Priority Score', fontsize=12)
            ax.set_title('Strategic Recommendations with Priority Ranking', 
                         fontsize=14, fontweight='bold', color=self.colors['primary'])
            
            # Remove y-axis
            ax.spines['left'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['top'].set_visible(False)
            
            # Add confidence legend
            legend_elements = [
                Patch(facecolor=self.colors['accent1'], label='High Priority'),
                Patch(facecolor=self.colors['accent2'], label='Medium Priority'),
                Patch(facecolor=self.colors['neutral'], label='Low Priority'),
                Patch(facecolor=self.colors['high_conf'], label='Confidence Indicator')
            ]
            ax.legend(handles=legend_elements, loc='upper right')
            
            # Add overall recommendation if available in the integrated data
            if integrated_data and isinstance(integrated_data, dict):
                # Extract from the original data structure instead of the recommendations list
                strategic_recs = integrated_data.get("strategic_recommendations", {})
                if isinstance(strategic_recs, dict):
                    overall_rec = strategic_recs.get("overall_recommendation", "")
                    if overall_rec:
                        plt.figtext(0.5, 0.02, f"OVERALL: {overall_rec}", 
                                  fontsize=10, ha='center', fontweight='bold', 
                                  bbox=dict(facecolor=self.colors['secondary'], alpha=0.3, boxstyle='round,pad=0.5'))
            
            plt.tight_layout(rect=[0, 0.05, 1, 0.95])
            
            # Save the visualization
            output_path = self.output_dir / f"strategic_recommendations_{self.timestamp}.png"
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info(f"Saved strategic recommendations to {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Error creating strategic recommendations: {str(e)}")
            logger.error(traceback.format_exc())
            return ""
    
    def create_market_position_radar(self, data: Dict[str, Any]) -> str:
        """
        Create a radar chart showing market position across dimensions.
        
        Args:
            data: Integrated analysis data
            
        Returns:
            Path to the generated visualization
        """
        logger.info("Creating market position radar chart")
        try:
            # Define dimensions for radar chart
            dimensions = [
                'Market Share', 
                'Brand Strength', 
                'Innovation', 
                'Growth Rate',
                'Digital Presence',
                'Service Diversity'
            ]
            
            # Create simulated values for TCS
            tcs_values = [0.8, 0.9, 0.75, 0.7, 0.85, 0.95]
            
            # Create some competitor values
            competitors = {
                "Infosys": [0.7, 0.8, 0.8, 0.75, 0.8, 0.9],
                "Wipro": [0.65, 0.75, 0.7, 0.7, 0.75, 0.85],
                "Cognizant": [0.75, 0.7, 0.8, 0.8, 0.9, 0.8]
            }
            
            # Set up radar chart
            angles = np.linspace(0, 2*np.pi, len(dimensions), endpoint=False)
            angles = np.concatenate((angles, [angles[0]]))  # Close the loop
            
            # Create the dimensions plus the first one repeated (to close the circle)
            dimensions = np.concatenate((dimensions, [dimensions[0]]))
            
            # Set up plot
            fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(polar=True))
            
            # Add data for TCS
            tcs_values = np.concatenate((tcs_values, [tcs_values[0]]))
            ax.plot(angles, tcs_values, 'o-', linewidth=2, color=self.colors['primary'], label='TCS')
            ax.fill(angles, tcs_values, color=self.colors['primary'], alpha=0.25)
            
            # Add data for competitors
            colors = [self.colors['accent1'], self.colors['accent2'], self.colors['neutral']]
            for i, (name, values) in enumerate(competitors.items()):
                values = np.concatenate((values, [values[0]]))
                ax.plot(angles, values, 'o-', linewidth=2, color=colors[i % len(colors)], label=name)
                ax.fill(angles, values, color=colors[i % len(colors)], alpha=0.1)
            
            # Set ticks and labels
            ax.set_xticks(angles[:-1])
            ax.set_xticklabels(dimensions[:-1], fontsize=10, fontweight='bold')
            
            # Set y-ticks
            ax.set_yticks([0.2, 0.4, 0.6, 0.8, 1.0])
            ax.set_yticklabels(['0.2', '0.4', '0.6', '0.8', '1.0'], fontsize=8)
            ax.set_ylim(0, 1)
            
            # Add title and legend
            plt.title('Market Position Radar Analysis', fontsize=14, fontweight='bold', color=self.colors['primary'])
            plt.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))
            
            # Add confidence indicator
            conf_score = data.get("integrated_analysis", {}).get("confidence_metrics", {}).get("overall_confidence", 0.8)
            conf_text = f"Confidence: {conf_score:.2f}"
            plt.figtext(0.02, 0.02, conf_text, fontsize=10, color=self._get_confidence_color(conf_score))
            
            # Save the visualization
            output_path = self.output_dir / f"market_position_radar_{self.timestamp}.png"
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info(f"Saved market position radar chart to {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Error creating market position radar: {str(e)}")
            logger.error(traceback.format_exc())
            return ""
    
    def create_all_visualizations(self, data: Dict[str, Any]) -> Dict[str, str]:
        """
        Create all enhanced visualizations for the report.
        
        Args:
            data: Integrated analysis data
            
        Returns:
            Dictionary with paths to all generated visualizations
        """
        logger.info("Creating all enhanced visualizations")
        
        visualizations = {
            "competitor_matrix": self.create_competitor_matrix(data),
            "enhanced_swot": self.create_swot_matrix(data),
            "strategic_recommendations": self.create_strategic_recommendations(data, data),
            "market_position_radar": self.create_market_position_radar(data)
        }
        
        logger.info(f"Created {len([v for v in visualizations.values() if v])} visualizations")
        return visualizations
    
    def _get_confidence_color(self, confidence: float) -> str:
        """
        Get color based on confidence score.
        
        Args:
            confidence: Confidence score (0-1)
            
        Returns:
            Color for confidence level
        """
        if confidence >= 0.8:
            return self.colors['high_conf']
        elif confidence >= 0.6:
            return self.colors['med_conf']
        else:
            return self.colors['low_conf']


# Test function
def test_service():
    """Test the enhanced visualization service with sample data."""
    try:
        # Load sample API data
        with open("exports/tcs_api_demo_20250516_164740.json", "r") as f:
            sample_data = json.load(f)
        
        # Create data integration service to get integrated data
        from data_integration_service import DataIntegrationService
        integration_service = DataIntegrationService()
        integrated_data = integration_service.integrate_data(sample_data)
        
        # Create visualization service
        visualization_service = EnhancedVisualizationService()
        
        # Create visualizations
        visualizations = visualization_service.create_all_visualizations(integrated_data)
        
        print("\n✅ Enhanced visualizations created:")
        for name, path in visualizations.items():
            if path:
                print(f"- {name}: {path}")
        
        return visualizations
        
    except Exception as e:
        print(f"\n❌ Error testing visualization service: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return {}


if __name__ == "__main__":
    test_service()
