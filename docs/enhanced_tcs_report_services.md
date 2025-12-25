# Enhanced TCS Report Generator Services Documentation

**Date:** May 16, 2025  
**Author:** OnSide Development Team  
**Version:** 1.1.0  

## Overview

This document provides detailed documentation for the enhanced TCS (Tata Consultancy Services) report generator services implemented in Sprint 4 as part of the OnSide platform. These services integrate with OnSide's core capabilities to provide advanced competitive intelligence reports with chain-of-thought reasoning, confidence metrics, and strategic visualizations.

All services adhere to Semantic Seed Venture Studio Coding Standards V2.0 with proper error handling, logging, and documentation.

## Architecture Integration

The enhanced TCS report services integrate with the OnSide core platform through:

1. **LLMWithChainOfThought Base Class**: Uses OnSide's AI reasoning infrastructure for structured analysis
2. **FallbackManager**: Provides resilient LLM provider management with automatic failover
3. **Report Model**: Integrates with OnSide's database for persistent storage and tracking

## Services and Endpoints

### 1. Enhanced AI Service

The `EnhancedAIService` provides advanced AI-driven analysis with confidence scoring, reasoning chains, and fallback support.

#### Key Endpoints:

| Endpoint | Description | Parameters | Returns |
|----------|-------------|------------|---------|
| `generate_competitor_analysis_with_cot` | Generates competitor analysis with chain-of-thought reasoning | `company_data`: Dict containing company information | Enhanced AI analysis with reasoning chains and confidence scores |
| `generate_market_analysis_with_cot` | Analyzes market position and trends | `market_data`: Dict containing market information | Market analysis with predictions and confidence metrics |
| `generate_strategic_recommendations` | Creates strategic recommendations based on integrated data | `integrated_data`: Dict containing all analysis data | Strategic recommendations with confidence scores and reasoning |

#### Usage Example:

```python
from scripts.report_generators.services.enhanced_ai_service import EnhancedAIService

# Initialize the service
ai_service = EnhancedAIService(api_keys={
    "openai": "your_openai_key",
    "anthropic": "your_anthropic_key"
})

# Generate competitor analysis with chain-of-thought reasoning
company_data = {
    "company": "Tata Consultancy Services",
    "industry": "IT Services",
    "website": "tcs.com"
}
analysis = await ai_service.generate_competitor_analysis_with_cot(company_data)

# Access reasoning and confidence scores
reasoning_chain = analysis["reasoning_chain"]
confidence = analysis["confidence_score"]
```

### 2. Data Integration Service

The `DataIntegrationService` integrates data from multiple API sources to provide comprehensive analysis.

#### Key Endpoints:

| Endpoint | Description | Parameters | Returns |
|----------|-------------|------------|---------|
| `integrate_data` | Integrates data from multiple API sources | `raw_data`: Dict with all API responses | Integrated data structure with enhanced analysis |
| `generate_enhanced_swot` | Generates enhanced SWOT analysis | `competitor_data`, `market_data`: Dicts with analysis data | Enhanced SWOT analysis with confidence metrics |
| `generate_strategic_recommendations` | Generates strategic recommendations | `integrated_data`: Dict with all analysis | Strategic recommendations with reasoning |

#### Usage Example:

```python
from scripts.report_generators.services.data_integration_service import DataIntegrationService

# Initialize the service
integration_service = DataIntegrationService()

# Integrate data from multiple sources
integrated_data = integration_service.integrate_data(raw_data)

# Generate enhanced SWOT analysis
swot_analysis = integration_service.generate_enhanced_swot(
    integrated_data["competitor_analysis"],
    integrated_data["market_analysis"]
)
```

### 3. Enhanced Visualization Service

The `EnhancedVisualizationService` creates advanced data visualizations with confidence indicators.

#### Key Endpoints:

| Endpoint | Description | Parameters | Returns |
|----------|-------------|------------|---------|
| `create_all_visualizations` | Creates all visualizations for the report | `data`: Dict with integrated data | Dict of visualization paths |
| `create_competitor_matrix` | Creates competitor positioning matrix | `data`: Dict with competitor data | Path to saved visualization |
| `create_enhanced_swot` | Creates enhanced SWOT matrix with confidence indicators | `data`: Dict with SWOT analysis | Path to saved visualization |
| `create_strategic_recommendations` | Visualizes strategic recommendations | `data`, `integrated_data`: Analysis data | Path to saved visualization |
| `create_market_position_radar` | Creates market position radar chart | `data`: Dict with market position data | Path to saved visualization |

#### Usage Example:

```python
from scripts.report_generators.services.enhanced_visualization_service import EnhancedVisualizationService

# Initialize the service
visualization_service = EnhancedVisualizationService(
    export_dir="exports",
    timestamp="20250516_123456"
)

# Create all visualizations
visualizations = visualization_service.create_all_visualizations(
    integrated_data,
    integrated_data  # Pass integrated_data twice as required by the method
)

# Access individual visualization paths
competitor_matrix_path = visualizations["competitor_matrix"]
swot_matrix_path = visualizations["enhanced_swot"]
```

### 4. Enhanced PDF Service

The `OnSidePDFService` (formerly KPMGPDFService) generates professional PDF reports with reasoning chains and confidence metrics. The service has been completely  updated styling and color schemes.

#### Key Endpoints:

| Endpoint | Description | Parameters | Returns |
|----------|-------------|------------|---------|
| `create_pdf_report` | Creates comprehensive PDF report | `integrated_data`, `visualizations`: Report data and visualization paths | Path to saved PDF file |
| `add_executive_summary` | Adds executive summary to the report | `data`: Dict with summary information | None |
| `add_competitor_analysis` | Adds competitor analysis section | `data`: Dict with competitor analysis | None |
| `add_market_analysis` | Adds market analysis section | `data`: Dict with market analysis | None |
| `add_strategic_recommendations` | Adds strategic recommendations | `data`: Dict with recommendations | None |
| `add_visualizations` | Adds visualizations to the report | `visualizations`: Dict with visualization paths | None |

#### Usage Example:

```python
from scripts.report_generators.services.enhanced_pdf_service import EnhancedPDFService

# Initialize the service
pdf_service = EnhancedPDFService(
    export_dir="exports",
    timestamp="20250516_123456",
    filename="tcs_enhanced_report"
)

# Create the PDF report
pdf_path = pdf_service.create_pdf_report(integrated_data, visualizations)
```

### 5. Main Report Generator

The `enhanced_tcs_report.py` script coordinates all services to generate the complete report.

#### Key Functions:

| Function | Description | Parameters | Returns |
|----------|-------------|------------|---------|
| `generate_enhanced_tcs_report` | Main function to generate the report | None | Tuple of (raw_data_path, pdf_path, visualizations) |
| `collect_api_data` | Collects data from all API sources | None | Dict with all API responses |
| `_call_gnews_api` | Calls GNews API for news data | `query`: Search query | News data response |
| `_call_whoapi` | Calls WHOAPI for domain information | `domain`: Domain name | Domain information response |
| `_call_serpapi` | Calls SERPAPI for search insights | `query`: Search query | Search insights response |
| `_call_ipinfo` | Calls IPInfo API for geographic data | `ip`: IP address to lookup | Geographic data response |

#### Usage Example:

```python
# Run the enhanced TCS report generator
python scripts/report_generators/enhanced_tcs_report.py

# Output includes:
# - Raw data JSON: exports/tcs_enhanced_data_[timestamp].json
# - PDF report: exports/tcs_enhanced_report_[timestamp].pdf
# - Visualizations in the exports directory
```

## API Integration

The enhanced TCS report generator integrates with the following external APIs:

1. **GNews API**: Current news analysis
2. **WHOAPI**: Domain information
3. **SERPAPI**: Search engine data
4. **IPInfo**: Geographic data

Additionally, it integrates with OnSide's internal APIs:

1. **LLM Provider API**: For AI analysis with chain-of-thought reasoning
2. **Database API**: For report storage and tracking

## Environment Configuration

The following environment variables are required:

```
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
GNEWS_API_KEY=your_gnews_key
WHOAPI_API_KEY=your_whoapi_key
SERPAPI_API_KEY=your_serpapi_key
IPINFO_API_KEY=your_ipinfo_key
```

## Development Notes

1. **Python Version**: Python 3.10+ recommended for production use
2. **Dependencies**: See `requirements.txt` for all dependencies
3. **Virtual Environment**: Use `onside_prod310` virtual environment for development and testing
4. **OnSide Core Services**: Requires SQLAlchemy with greenlet for async functionality

## Future Enhancements

1. **Additional LLM Providers**: Implementation ready for Cohere and HuggingFace integration
2. **Enhanced Confidence Metrics**: Framework in place for more sophisticated confidence scoring
3. **Additional Visualization Types**: Structure supports adding new visualization formats
4. **Interactive Reports**: PDF structure can be extended to interactive HTML reports

## Recent Updates

### May 16, 2025 Update (v1.1.0):

1. **Rebranding**: Complete transition to OnSide branding throughout the PDF service
   - Updated class name to `OnSidePDFService`
   - Changed all color constants to use OnSide's brand colors
   - Updated all style definitions with OnSide-specific naming
   
2. **Report Layout Improvements**:
   - Fixed blank page issues by optimizing page breaks
   - Improved section headings and content flow
   - Enhanced readability through better spacing and formatting

3. **Integration Status**:
   - Current test implementation uses core OnSide services but with mock data
   - External APIs (GNews, WHOAPI, SERPAPI, IPInfo) are defined but not actively used in tests
   - Future work needed to combine the improved core services with active external API integration

## Current Development Status

The enhanced TCS report generator is in a transitional state:

1. **Completed**: PDF service rebranding, formatting fixes, and core services integration
2. **In Progress**: Re-integration of external API data sources with the improved core services
3. **Planned**: Full end-to-end testing with all data sources and core services working together

## Troubleshooting

1. **SQLAlchemy Import Issues**: Ensure greenlet is installed for async functionality
2. **Python Version Compatibility**: For Python 3.10, use timezone.utc instead of UTC from datetime
3. **FallbackManager Initialization**: Ensure proper LLMProvider enum values are passed
4. **Report Model Integration**: Check database connection and schema alignment
5. **Blank Pages in PDF**: If blank pages appear in the generated PDF, check for unnecessary PageBreak() calls in the code

## Support and Contribution

For questions or contributions, please contact the OnSide development team or refer to the project's CONTRIBUTING.md guidelines.
