/**
 * ProgressBar Component
 *
 * A beautiful, accessible progress bar component that shows
 * real-time progress with smooth animations.
 */

import React from 'react';
import { ProgressStatus, getProgressColor } from '../../hooks/useProgressTracking';
import './ProgressBar.css';

interface ProgressBarProps {
  progress: number; // 0 to 100
  status: ProgressStatus;
  label?: string;
  showPercentage?: boolean;
  animated?: boolean;
  height?: string;
  className?: string;
}

export const ProgressBar: React.FC<ProgressBarProps> = ({
  progress,
  status,
  label,
  showPercentage = true,
  animated = true,
  height = '24px',
  className = ''
}) => {
  const progressColor = getProgressColor(status);
  const clampedProgress = Math.min(Math.max(progress, 0), 100);

  return (
    <div className={`progress-bar-container ${className}`}>
      {label && (
        <div className="progress-bar-label">
          <span>{label}</span>
          {showPercentage && (
            <span className="progress-bar-percentage">
              {Math.round(clampedProgress)}%
            </span>
          )}
        </div>
      )}
      <div
        className="progress-bar-track"
        style={{ height }}
        role="progressbar"
        aria-valuenow={clampedProgress}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={label || 'Progress'}
      >
        <div
          className={`progress-bar-fill ${animated ? 'animated' : ''} ${status}`}
          style={{
            width: `${clampedProgress}%`,
            backgroundColor: progressColor,
            height: '100%'
          }}
        >
          {status === ProgressStatus.IN_PROGRESS && animated && (
            <div className="progress-bar-shimmer" />
          )}
        </div>
      </div>
    </div>
  );
};

export default ProgressBar;
