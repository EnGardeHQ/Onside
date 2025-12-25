/**
 * Progress Tracker Component
 * Tracks and displays brand analysis progress with polling
 */

import React, { useEffect } from 'react';
import { AlertCircle, CheckCircle2, Loader2, Globe, Brain, Database } from 'lucide-react';
import { Card, Button } from '../../../components/common';
import { AnalysisStatus } from '../../../types';

interface ProgressTrackerProps {
  status: AnalysisStatus | undefined;
  onComplete: () => void;
  onCancel: () => void;
  onFallback?: () => void;
  isLoading?: boolean;
  error?: Error | null;
}

export const ProgressTracker: React.FC<ProgressTrackerProps> = ({
  status,
  onComplete,
  onCancel,
  onFallback,
  isLoading = true,
  error,
}) => {
  // Auto-advance when completed
  useEffect(() => {
    if (status?.status === 'completed') {
      // Small delay before transitioning
      const timer = setTimeout(onComplete, 1000);
      return () => clearTimeout(timer);
    }
  }, [status?.status, onComplete]);

  const getStatusInfo = () => {
    if (error || status?.status === 'failed') {
      return {
        icon: AlertCircle,
        color: 'text-danger-500',
        bgColor: 'bg-danger-100 dark:bg-danger-900/30',
        title: 'Analysis Failed',
        message: status?.error_message || error?.message || 'An error occurred during analysis',
      };
    }

    switch (status?.status) {
      case 'pending':
        return {
          icon: Loader2,
          color: 'text-primary-500',
          bgColor: 'bg-primary-100 dark:bg-primary-900/30',
          title: 'Preparing Analysis',
          message: 'Setting up your brand analysis...',
        };
      case 'crawling':
        return {
          icon: Globe,
          color: 'text-blue-500',
          bgColor: 'bg-blue-100 dark:bg-blue-900/30',
          title: 'Crawling Website',
          message: 'Analyzing your website and discovering content...',
        };
      case 'analyzing':
        return {
          icon: Brain,
          color: 'text-purple-500',
          bgColor: 'bg-purple-100 dark:bg-purple-900/30',
          title: 'Analyzing Data',
          message: 'Processing discovered content and identifying patterns...',
        };
      case 'processing':
        return {
          icon: Database,
          color: 'text-indigo-500',
          bgColor: 'bg-indigo-100 dark:bg-indigo-900/30',
          title: 'Processing Results',
          message: 'Generating recommendations and insights...',
        };
      case 'completed':
        return {
          icon: CheckCircle2,
          color: 'text-success-500',
          bgColor: 'bg-success-100 dark:bg-success-900/30',
          title: 'Analysis Complete',
          message: 'Successfully analyzed your brand!',
        };
      default:
        return {
          icon: Loader2,
          color: 'text-gray-500',
          bgColor: 'bg-gray-100 dark:bg-gray-900/30',
          title: 'Loading',
          message: 'Please wait...',
        };
    }
  };

  const statusInfo = getStatusInfo();
  const Icon = statusInfo.icon;
  const progress = status?.progress_percentage || 0;
  const estimatedTime = status?.estimated_time_remaining;

  const formatTime = (seconds: number) => {
    if (seconds < 60) return `${Math.round(seconds)}s`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.round(seconds % 60);
    return `${minutes}m ${remainingSeconds}s`;
  };

  return (
    <div className="max-w-2xl mx-auto">
      <Card className="p-8">
        <div className="text-center">
          {/* Status Icon */}
          <div className={`inline-flex items-center justify-center w-20 h-20 rounded-full ${statusInfo.bgColor} mb-6`}>
            <Icon
              className={`${statusInfo.color} ${status?.status !== 'completed' && status?.status !== 'failed' ? 'animate-spin' : ''}`}
              size={40}
            />
          </div>

          {/* Status Title */}
          <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-2">
            {statusInfo.title}
          </h2>

          {/* Status Message */}
          <p className="text-gray-600 dark:text-gray-400 mb-6">
            {statusInfo.message}
          </p>

          {/* Progress Bar */}
          {status?.status !== 'failed' && status?.status !== 'completed' && (
            <div className="mb-6">
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3 overflow-hidden">
                <div
                  className="bg-primary-500 h-3 rounded-full transition-all duration-500 ease-out"
                  style={{ width: `${progress}%` }}
                />
              </div>
              <div className="flex justify-between items-center mt-2 text-sm text-gray-600 dark:text-gray-400">
                <span>{progress}% complete</span>
                {estimatedTime && (
                  <span>~{formatTime(estimatedTime)} remaining</span>
                )}
              </div>
            </div>
          )}

          {/* Current Step */}
          {status?.current_step && status?.status !== 'failed' && status?.status !== 'completed' && (
            <div className="mb-6 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
              <p className="text-sm font-medium text-gray-700 dark:text-gray-300">
                Current Step
              </p>
              <p className="text-gray-600 dark:text-gray-400 mt-1">
                {status.current_step}
              </p>
            </div>
          )}

          {/* Steps Progress */}
          {status?.status !== 'failed' && (
            <div className="mb-8">
              <div className="flex items-center justify-center gap-2">
                {['pending', 'crawling', 'analyzing', 'processing', 'completed'].map((step, index) => {
                  const stepStatuses = ['pending', 'crawling', 'analyzing', 'processing', 'completed'];
                  const currentIndex = stepStatuses.indexOf(status?.status || 'pending');
                  const isComplete = index <= currentIndex;
                  const isCurrent = index === currentIndex;

                  return (
                    <React.Fragment key={step}>
                      <div
                        className={`w-3 h-3 rounded-full transition-all ${
                          isComplete
                            ? 'bg-primary-500'
                            : 'bg-gray-300 dark:bg-gray-600'
                        } ${isCurrent ? 'ring-4 ring-primary-200 dark:ring-primary-800' : ''}`}
                      />
                      {index < 4 && (
                        <div
                          className={`w-8 h-0.5 ${
                            isComplete
                              ? 'bg-primary-500'
                              : 'bg-gray-300 dark:bg-gray-600'
                          }`}
                        />
                      )}
                    </React.Fragment>
                  );
                })}
              </div>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex gap-3 justify-center">
            {status?.status === 'failed' ? (
              <>
                {onFallback && (
                  <Button variant="secondary" onClick={onFallback}>
                    Use Manual Entry
                  </Button>
                )}
                <Button variant="primary" onClick={onCancel}>
                  Start Over
                </Button>
              </>
            ) : status?.status === 'completed' ? (
              <Button variant="primary" onClick={onComplete}>
                View Results
              </Button>
            ) : (
              <Button
                variant="secondary"
                onClick={onCancel}
                disabled={isLoading}
              >
                Cancel
              </Button>
            )}
          </div>
        </div>
      </Card>
    </div>
  );
};
