/**
 * ReportProgressTracker Component
 *
 * Complete progress tracking interface for report generation.
 * Combines WebSocket connection, progress bar, stage indicators,
 * and time estimation in a beautiful, accessible UI.
 */

import React, { useEffect } from 'react';
import {
  useProgressTracking,
  ProgressStatus,
  ProgressStage,
  formatTimeRemaining
} from '../../hooks/useProgressTracking';
import ProgressBar from './ProgressBar';
import StageIndicator from './StageIndicator';
import './ReportProgressTracker.css';

interface ReportProgressTrackerProps {
  reportId: number;
  userId: number;
  onComplete?: () => void;
  onError?: (error: string) => void;
  onCancel?: () => void;
  showStages?: boolean;
  showTimeEstimate?: boolean;
  allowCancel?: boolean;
  className?: string;
}

export const ReportProgressTracker: React.FC<ReportProgressTrackerProps> = ({
  reportId,
  userId,
  onComplete,
  onError,
  onCancel,
  showStages = true,
  showTimeEstimate = true,
  allowCancel = true,
  className = ''
}) => {
  const {
    progressData,
    isConnected,
    cancelReport,
    stageLabels
  } = useProgressTracking({
    reportId,
    userId,
    onComplete: () => {
      onComplete?.();
    },
    onError: (error) => {
      onError?.(error);
    }
  });

  // Prepare stages data
  const stages = progressData
    ? Object.values(ProgressStage).map((stage) => ({
        stage,
        label: stageLabels[stage],
        progress: progressData.stageProgress[stage] || 0
      }))
    : [];

  const handleCancel = () => {
    cancelReport();
    onCancel?.();
  };

  const renderConnectionStatus = () => {
    if (!isConnected && progressData?.status === ProgressStatus.IN_PROGRESS) {
      return (
        <div className="connection-status disconnected" role="status">
          <span className="status-indicator">●</span>
          <span>Reconnecting...</span>
        </div>
      );
    }
    return null;
  };

  const renderStatusMessage = () => {
    if (!progressData) {
      return (
        <div className="status-message info">
          <div className="spinner-small" />
          <span>Initializing report generation...</span>
        </div>
      );
    }

    switch (progressData.status) {
      case ProgressStatus.COMPLETED:
        return (
          <div className="status-message success" role="status">
            <svg className="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M5 13l4 4L19 7"
              />
            </svg>
            <span>Report generated successfully!</span>
          </div>
        );

      case ProgressStatus.FAILED:
        return (
          <div className="status-message error" role="alert">
            <svg className="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
            <span>
              {progressData.errorMessage || 'An error occurred during report generation'}
            </span>
          </div>
        );

      case ProgressStatus.CANCELLED:
        return (
          <div className="status-message warning" role="status">
            <svg className="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
              />
            </svg>
            <span>Report generation cancelled</span>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className={`report-progress-tracker ${className}`}>
      <div className="progress-header">
        <h3 className="progress-title">Report Generation Progress</h3>
        {renderConnectionStatus()}
      </div>

      {renderStatusMessage()}

      {progressData && (
        <>
          {/* Overall Progress Bar */}
          <ProgressBar
            progress={progressData.overallProgress}
            status={progressData.status}
            label="Overall Progress"
            showPercentage={true}
            animated={true}
          />

          {/* Time Estimate */}
          {showTimeEstimate &&
            progressData.status === ProgressStatus.IN_PROGRESS &&
            progressData.estimatedTimeRemaining && (
              <div className="time-estimate">
                <svg className="icon-small" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
                <span>
                  Estimated time remaining:{' '}
                  <strong>{formatTimeRemaining(progressData.estimatedTimeRemaining)}</strong>
                </span>
              </div>
            )}

          {/* Stage Indicators */}
          {showStages && stages.length > 0 && (
            <div className="stages-section">
              <h4 className="stages-title">Processing Stages</h4>
              <StageIndicator
                stages={stages}
                currentStage={progressData.currentStage}
                orientation="horizontal"
              />
            </div>
          )}

          {/* Current Stage Details */}
          {progressData.status === ProgressStatus.IN_PROGRESS && (
            <div className="current-stage-details">
              <div className="stage-info">
                <span className="stage-label">Current Stage:</span>
                <span className="stage-name">
                  {stageLabels[progressData.currentStage]}
                </span>
              </div>
              <ProgressBar
                progress={(progressData.stageProgress[progressData.currentStage] || 0) * 100}
                status={ProgressStatus.IN_PROGRESS}
                showPercentage={true}
                animated={true}
                height="8px"
              />
            </div>
          )}

          {/* Actions */}
          {allowCancel && progressData.status === ProgressStatus.IN_PROGRESS && (
            <div className="progress-actions">
              <button
                onClick={handleCancel}
                className="btn-cancel"
                type="button"
                aria-label="Cancel report generation"
              >
                Cancel
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default ReportProgressTracker;
