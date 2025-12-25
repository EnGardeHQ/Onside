/**
 * Example Usage: ReportProgressTracker Component
 *
 * This file demonstrates how to use the ReportProgressTracker component
 * in your React application.
 */

import React, { useState } from 'react';
import { ReportProgressTracker } from './ReportProgressTracker';

export const ProgressTrackerExample: React.FC = () => {
  const [showTracker, setShowTracker] = useState(false);
  const [reportId, setReportId] = useState<number | null>(null);

  const handleStartReport = async () => {
    try {
      // Call your API to start report generation
      const response = await fetch('/api/v1/progress/reports/123/start', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('authToken')}`
        },
        body: JSON.stringify({
          user_id: 1 // Replace with actual user ID
        })
      });

      if (response.ok) {
        const data = await response.json();
        setReportId(data.report_id);
        setShowTracker(true);
      }
    } catch (error) {
      console.error('Failed to start report generation:', error);
    }
  };

  const handleComplete = () => {
    console.log('Report generation completed!');
    // Navigate to report view, show success message, etc.
  };

  const handleError = (error: string) => {
    console.error('Report generation failed:', error);
    // Show error notification, etc.
  };

  const handleCancel = () => {
    console.log('Report generation cancelled');
    setShowTracker(false);
  };

  return (
    <div className="container">
      <h1>Report Generation Example</h1>

      {!showTracker ? (
        <button onClick={handleStartReport} className="btn-primary">
          Generate Report
        </button>
      ) : (
        reportId && (
          <ReportProgressTracker
            reportId={reportId}
            userId={1} // Replace with actual user ID
            onComplete={handleComplete}
            onError={handleError}
            onCancel={handleCancel}
            showStages={true}
            showTimeEstimate={true}
            allowCancel={true}
          />
        )
      )}
    </div>
  );
};

/**
 * Alternative Example: Inline Progress for Multiple Reports
 */
export const MultipleReportsExample: React.FC = () => {
  const [activeReports, setActiveReports] = useState<number[]>([]);

  const startNewReport = async () => {
    // Start report generation and add to active reports
    const newReportId = Date.now(); // Replace with actual API call
    setActiveReports([...activeReports, newReportId]);
  };

  const removeReport = (reportId: number) => {
    setActiveReports(activeReports.filter((id) => id !== reportId));
  };

  return (
    <div className="container">
      <h1>Multiple Reports Dashboard</h1>

      <button onClick={startNewReport} className="btn-primary">
        Start New Report
      </button>

      <div className="reports-grid">
        {activeReports.map((reportId) => (
          <div key={reportId} className="report-card">
            <ReportProgressTracker
              reportId={reportId}
              userId={1}
              onComplete={() => removeReport(reportId)}
              onError={(error) => {
                console.error(`Report ${reportId} failed:`, error);
                removeReport(reportId);
              }}
              onCancel={() => removeReport(reportId)}
              showStages={false} // Compact view for multiple reports
              showTimeEstimate={true}
              allowCancel={true}
            />
          </div>
        ))}
      </div>
    </div>
  );
};

/**
 * Example: Using the Hook Directly for Custom UI
 */
export const CustomProgressExample: React.FC = () => {
  const {
    progressData,
    isConnected,
    cancelReport
  } = require('../../hooks/useProgressTracking').useProgressTracking({
    reportId: 123,
    userId: 1,
    onComplete: (data) => {
      console.log('Completed:', data);
    }
  });

  return (
    <div>
      <h2>Custom Progress UI</h2>
      {progressData && (
        <div>
          <p>Status: {progressData.status}</p>
          <p>Progress: {progressData.overallProgress}%</p>
          <p>Connected: {isConnected ? 'Yes' : 'No'}</p>

          {progressData.status === 'in_progress' && (
            <button onClick={cancelReport}>Cancel</button>
          )}
        </div>
      )}
    </div>
  );
};

export default ProgressTrackerExample;
