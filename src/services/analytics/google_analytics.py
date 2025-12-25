from typing import Dict, Optional
import logging
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    RunReportRequest,
    DateRange,
    Metric,
    Dimension
)

logger = logging.getLogger(__name__)

class GoogleAnalyticsService:
    def __init__(self, client=None):
        self.client = client or BetaAnalyticsDataClient()
        self.property_id = "properties/YOUR_GA4_PROPERTY_ID"

    async def get_content_metrics(self, content_asset) -> Dict:
        """Get content performance metrics from Google Analytics"""
        try:
            request = RunReportRequest(
                property=self.property_id,
                dimensions=[
                    Dimension(name="pagePath"),
                    Dimension(name="deviceCategory"),
                    Dimension(name="country")
                ],
                metrics=[
                    Metric(name="screenPageViews"),
                    Metric(name="engagedSessions"),
                    Metric(name="conversions"),
                    Metric(name="totalRevenue")
                ],
                date_ranges=[DateRange(
                    start_date="30daysAgo",
                    end_date="today"
                )]
            )

            response = self.client.run_report(request)

            return self._process_ga_response(response)

        except Exception as e:
            logger.error(f"Error getting GA metrics: {str(e)}")
            return {}

    def _process_ga_response(self, response) -> Dict:
        """Process GA response into structured metrics"""
        try:
            metrics = {
                "pageviews": 0,
                "engaged_sessions": 0,
                "conversions": 0,
                "revenue": 0.0,
                "by_device": {},
                "by_country": {}
            }

            for row in response.rows:
                metrics["pageviews"] += int(row.metric_values[0].value)
                metrics["engaged_sessions"] += int(row.metric_values[1].value)
                metrics["conversions"] += int(row.metric_values[2].value)
                metrics["revenue"] += float(row.metric_values[3].value)

                # Add device breakdown
                device = row.dimension_values[1].value
                if device not in metrics["by_device"]:
                    metrics["by_device"][device] = {
                        "pageviews": 0,
                        "engaged_sessions": 0
                    }
                metrics["by_device"][device]["pageviews"] += int(row.metric_values[0].value)
                metrics["by_device"][device]["engaged_sessions"] += int(row.metric_values[1].value)

                # Add country breakdown
                country = row.dimension_values[2].value
                if country not in metrics["by_country"]:
                    metrics["by_country"][country] = {
                        "pageviews": 0,
                        "conversions": 0
                    }
                metrics["by_country"][country]["pageviews"] += int(row.metric_values[0].value)
                metrics["by_country"][country]["conversions"] += int(row.metric_values[2].value)

            return metrics

        except Exception as e:
            logger.error(f"Error processing GA response: {str(e)}")
            return {}
