from typing import Dict, Optional
import logging
from aanalytics2 import Login

logger = logging.getLogger(__name__)

class AdobeAnalyticsService:
    def __init__(self, client=None):
        self.client = client or self._initialize_client()

    def _initialize_client(self):
        """Initialize Adobe Analytics client"""
        try:
            login = Login()
            return login.connector
        except Exception as e:
            logger.error(f"Error initializing Adobe Analytics client: {str(e)}")
            return None

    async def get_content_metrics(self, content_asset) -> Dict:
        """Get content performance metrics from Adobe Analytics"""
        try:
            if not self.client:
                return {}

            # Define report parameters
            params = {
                "rsid": "your_report_suite",
                "globalFilters": [{
                    "type": "dateRange",
                    "dateRange": "2024-01-01T00:00:00.000/2024-12-31T23:59:59.999"
                }],
                "metricContainer": {
                    "metrics": [{
                        "columnId": "1",
                        "id": "metrics/pageviews",
                        "filters": ["0"]
                    }, {
                        "columnId": "2",
                        "id": "metrics/visits",
                        "filters": ["0"]
                    }, {
                        "columnId": "3",
                        "id": "metrics/orders",
                        "filters": ["0"]
                    }, {
                        "columnId": "4",
                        "id": "metrics/revenue",
                        "filters": ["0"]
                    }]
                },
                "dimension": "variables/page",
                "settings": {
                    "limit": 50,
                    "page": 0,
                    "dimensionSort": "asc"
                }
            }

            response = self.client.getReport(params)
            return self._process_adobe_response(response)

        except Exception as e:
            logger.error(f"Error getting Adobe Analytics metrics: {str(e)}")
            return {}

    def _process_adobe_response(self, response) -> Dict:
        """Process Adobe Analytics response into structured metrics"""
        try:
            metrics = {
                "pageviews": 0,
                "visits": 0,
                "orders": 0,
                "revenue": 0.0,
                "by_segment": {},
                "by_device": {}
            }

            for row in response.get("rows", []):
                metrics["pageviews"] += int(row.get("values", [0])[0])
                metrics["visits"] += int(row.get("values", [0])[1])
                metrics["orders"] += int(row.get("values", [0])[2])
                metrics["revenue"] += float(row.get("values", [0])[3])

                # Process segments if available
                segments = row.get("segments", {})
                for segment_name, segment_data in segments.items():
                    if segment_name not in metrics["by_segment"]:
                        metrics["by_segment"][segment_name] = {
                            "pageviews": 0,
                            "orders": 0
                        }
                    metrics["by_segment"][segment_name]["pageviews"] += int(segment_data.get("pageviews", 0))
                    metrics["by_segment"][segment_name]["orders"] += int(segment_data.get("orders", 0))

            return metrics

        except Exception as e:
            logger.error(f"Error processing Adobe Analytics response: {str(e)}")
            return {}
