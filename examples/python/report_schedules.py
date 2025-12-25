"""
Capilytics API - Python Report Schedules Examples
"""

import requests
import os
from authentication import CapilyticsAuthClient

BASE_URL = os.getenv('CAPILYTICS_API_URL', 'http://localhost:8000/api/v1')


class ReportSchedulesClient:
    """Client for managing report schedules"""

    def __init__(self, auth_client):
        self.auth_client = auth_client
        self.base_url = auth_client.base_url

    def create_schedule(self, schedule_data):
        """Create a new report schedule"""
        response = requests.post(
            f'{self.base_url}/report-schedules',
            headers=self.auth_client.get_headers(),
            json=schedule_data
        )
        response.raise_for_status()
        return response.json()

    def list_schedules(self, company_id=None, report_type=None, is_active=None,
                      page=1, page_size=20):
        """List report schedules with optional filters"""
        params = {'page': page, 'page_size': page_size}

        if company_id:
            params['company_id'] = company_id
        if report_type:
            params['report_type'] = report_type
        if is_active is not None:
            params['is_active'] = is_active

        response = requests.get(
            f'{self.base_url}/report-schedules',
            headers=self.auth_client.get_headers(),
            params=params
        )
        response.raise_for_status()
        return response.json()

    def get_schedule(self, schedule_id):
        """Get a specific report schedule"""
        response = requests.get(
            f'{self.base_url}/report-schedules/{schedule_id}',
            headers=self.auth_client.get_headers()
        )
        response.raise_for_status()
        return response.json()

    def update_schedule(self, schedule_id, update_data):
        """Update a report schedule"""
        response = requests.put(
            f'{self.base_url}/report-schedules/{schedule_id}',
            headers=self.auth_client.get_headers(),
            json=update_data
        )
        response.raise_for_status()
        return response.json()

    def delete_schedule(self, schedule_id):
        """Delete a report schedule"""
        response = requests.delete(
            f'{self.base_url}/report-schedules/{schedule_id}',
            headers=self.auth_client.get_headers()
        )
        response.raise_for_status()
        return True

    def pause_schedule(self, schedule_id):
        """Pause a report schedule"""
        response = requests.post(
            f'{self.base_url}/report-schedules/{schedule_id}/pause',
            headers=self.auth_client.get_headers()
        )
        response.raise_for_status()
        return response.json()

    def resume_schedule(self, schedule_id):
        """Resume a report schedule"""
        response = requests.post(
            f'{self.base_url}/report-schedules/{schedule_id}/resume',
            headers=self.auth_client.get_headers()
        )
        response.raise_for_status()
        return response.json()

    def get_executions(self, schedule_id, page=1, page_size=20):
        """Get execution history for a schedule"""
        response = requests.get(
            f'{self.base_url}/report-schedules/{schedule_id}/executions',
            headers=self.auth_client.get_headers(),
            params={'page': page, 'page_size': page_size}
        )
        response.raise_for_status()
        return response.json()

    def get_stats(self, schedule_id):
        """Get execution statistics for a schedule"""
        response = requests.get(
            f'{self.base_url}/report-schedules/{schedule_id}/stats',
            headers=self.auth_client.get_headers()
        )
        response.raise_for_status()
        return response.json()


# Example usage
if __name__ == '__main__':
    # Authenticate
    auth_client = CapilyticsAuthClient()
    auth_client.login(
        email=os.getenv('CAPILYTICS_EMAIL', 'user@example.com'),
        password=os.getenv('CAPILYTICS_PASSWORD', 'password')
    )

    # Initialize schedules client
    schedules = ReportSchedulesClient(auth_client)

    # Example 1: Create a weekly report schedule
    print("Creating weekly competitor report schedule...")
    schedule = schedules.create_schedule({
        'company_id': 1,
        'name': 'Weekly Competitor Analysis',
        'description': 'Automated weekly competitor intelligence report',
        'report_type': 'competitor_analysis',
        'cron_expression': '0 9 * * MON',  # Every Monday at 9 AM
        'parameters': {
            'competitors': [1, 2, 3],
            'metrics': ['traffic', 'engagement', 'seo'],
            'include_charts': True
        },
        'email_recipients': ['team@company.com', 'manager@company.com'],
        'notify_on_completion': True
    })
    print(f"Created schedule ID: {schedule['id']}")
    print(f"Next run: {schedule['next_run_at']}")

    # Example 2: List all active schedules
    print("\nListing active schedules...")
    results = schedules.list_schedules(is_active=True, page_size=10)
    print(f"Found {results['total']} active schedules")
    for s in results['schedules']:
        print(f"  - {s['name']} (ID: {s['id']}, Type: {s['report_type']})")

    # Example 3: Get schedule details
    print(f"\nGetting schedule details for ID {schedule['id']}...")
    details = schedules.get_schedule(schedule['id'])
    print(f"Schedule: {details['name']}")
    print(f"CRON: {details['cron_expression']}")
    print(f"Recipients: {', '.join(details['email_recipients'])}")

    # Example 4: Update schedule
    print(f"\nUpdating schedule...")
    updated = schedules.update_schedule(schedule['id'], {
        'name': 'Updated Weekly Report',
        'cron_expression': '0 10 * * MON'  # Change to 10 AM
    })
    print(f"Updated schedule: {updated['name']}")
    print(f"New CRON: {updated['cron_expression']}")

    # Example 5: Pause schedule
    print(f"\nPausing schedule...")
    paused = schedules.pause_schedule(schedule['id'])
    print(f"Schedule paused: {not paused['is_active']}")

    # Example 6: Resume schedule
    print(f"\nResuming schedule...")
    resumed = schedules.resume_schedule(schedule['id'])
    print(f"Schedule active: {resumed['is_active']}")
    print(f"Next run: {resumed['next_run_at']}")

    # Example 7: Get execution history
    print(f"\nGetting execution history...")
    executions = schedules.get_executions(schedule['id'], page_size=5)
    print(f"Total executions: {executions['total']}")
    for exec in executions['executions']:
        print(f"  - {exec['started_at']}: {exec['status']} "
              f"({exec['execution_time_seconds']}s)")

    # Example 8: Get statistics
    print(f"\nGetting execution statistics...")
    stats = schedules.get_stats(schedule['id'])
    print(f"Total executions: {stats['total_executions']}")
    print(f"Success rate: {stats['success_rate']:.2f}%")
    print(f"Avg execution time: {stats['avg_execution_time_seconds']:.2f}s")

    # Example 9: Delete schedule
    print(f"\nDeleting schedule...")
    schedules.delete_schedule(schedule['id'])
    print("Schedule deleted successfully")
