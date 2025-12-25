/**
 * StageIndicator Component
 *
 * Visual indicator for multi-step process stages.
 * Shows current stage, completed stages, and upcoming stages.
 */

import React from 'react';
import { ProgressStage } from '../../hooks/useProgressTracking';
import './StageIndicator.css';

interface Stage {
  stage: ProgressStage;
  label: string;
  progress: number; // 0 to 1
}

interface StageIndicatorProps {
  stages: Stage[];
  currentStage: ProgressStage;
  compact?: boolean;
  orientation?: 'horizontal' | 'vertical';
  className?: string;
}

export const StageIndicator: React.FC<StageIndicatorProps> = ({
  stages,
  currentStage,
  compact = false,
  orientation = 'horizontal',
  className = ''
}) => {
  const getStageStatus = (stage: Stage): 'completed' | 'current' | 'pending' => {
    if (stage.progress >= 1.0) return 'completed';
    if (stage.stage === currentStage) return 'current';
    return 'pending';
  };

  const getStageIcon = (status: string): string => {
    switch (status) {
      case 'completed':
        return '✓';
      case 'current':
        return '●';
      default:
        return '○';
    }
  };

  return (
    <div
      className={`stage-indicator ${orientation} ${compact ? 'compact' : ''} ${className}`}
      role="list"
      aria-label="Process stages"
    >
      {stages.map((stage, index) => {
        const status = getStageStatus(stage);
        const isLast = index === stages.length - 1;

        return (
          <div
            key={stage.stage}
            className={`stage-item ${status}`}
            role="listitem"
            aria-current={status === 'current' ? 'step' : undefined}
          >
            <div className="stage-marker">
              <div className={`stage-icon ${status}`}>
                {status === 'current' && stage.progress > 0 && stage.progress < 1 ? (
                  <div className="stage-spinner">
                    <div className="spinner" />
                  </div>
                ) : (
                  <span>{getStageIcon(status)}</span>
                )}
              </div>
              {!isLast && <div className={`stage-connector ${status}`} />}
            </div>
            {!compact && (
              <div className="stage-label">
                <div className={`stage-name ${status}`}>{stage.label}</div>
                {status === 'current' && stage.progress > 0 && stage.progress < 1 && (
                  <div className="stage-progress-text">
                    {Math.round(stage.progress * 100)}%
                  </div>
                )}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
};

export default StageIndicator;
