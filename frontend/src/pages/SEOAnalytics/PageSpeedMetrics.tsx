/**
 * PageSpeed Metrics Component
 * Displays Core Web Vitals metrics
 */

import React from 'react';
import { PageSpeedMetrics as PageSpeedMetricsType } from '../../types';

interface PageSpeedMetricsProps {
  metrics: PageSpeedMetricsType[];
}

export const PageSpeedMetrics: React.FC<PageSpeedMetricsProps> = ({ metrics }) => {
  if (metrics.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500 dark:text-gray-400">
        No PageSpeed metrics available
      </div>
    );
  }

  const getRating = (value: number, metric: 'lcp' | 'fid' | 'cls' | 'fcp') => {
    const thresholds: Record<string, { good: number; poor: number }> = {
      lcp: { good: 2500, poor: 4000 },
      fid: { good: 100, poor: 300 },
      cls: { good: 0.1, poor: 0.25 },
      fcp: { good: 1800, poor: 3000 },
    };

    const threshold = thresholds[metric];
    if (value <= threshold.good) return 'good';
    if (value <= threshold.poor) return 'needs-improvement';
    return 'poor';
  };

  const getRatingColor = (rating: string) => {
    switch (rating) {
      case 'good':
        return 'bg-success-100 dark:bg-success-900/30 text-success-700 dark:text-success-300';
      case 'needs-improvement':
        return 'bg-warning-100 dark:bg-warning-900/30 text-warning-700 dark:text-warning-300';
      case 'poor':
        return 'bg-danger-100 dark:bg-danger-900/30 text-danger-700 dark:text-danger-300';
      default:
        return 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300';
    }
  };

  return (
    <div className="space-y-4">
      {metrics.map((metric, index) => (
        <div key={index} className="border-b border-gray-200 dark:border-gray-700 last:border-0 pb-4 last:pb-0">
          <div className="flex items-center justify-between mb-3">
            <span className="font-medium text-gray-900 dark:text-gray-100">{metric.url}</span>
            <span className="text-sm text-gray-600 dark:text-gray-400">
              Score: {metric.performance_score}/100
            </span>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-3">
              <p className="text-xs text-gray-600 dark:text-gray-400 mb-1">LCP</p>
              <p className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                {(metric.lcp / 1000).toFixed(2)}s
              </p>
              <span
                className={`inline-flex mt-1 px-2 py-0.5 rounded text-xs font-medium ${getRatingColor(
                  getRating(metric.lcp, 'lcp')
                )}`}
              >
                {getRating(metric.lcp, 'lcp')}
              </span>
            </div>

            <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-3">
              <p className="text-xs text-gray-600 dark:text-gray-400 mb-1">FID</p>
              <p className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                {metric.fid.toFixed(0)}ms
              </p>
              <span
                className={`inline-flex mt-1 px-2 py-0.5 rounded text-xs font-medium ${getRatingColor(
                  getRating(metric.fid, 'fid')
                )}`}
              >
                {getRating(metric.fid, 'fid')}
              </span>
            </div>

            <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-3">
              <p className="text-xs text-gray-600 dark:text-gray-400 mb-1">CLS</p>
              <p className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                {metric.cls.toFixed(3)}
              </p>
              <span
                className={`inline-flex mt-1 px-2 py-0.5 rounded text-xs font-medium ${getRatingColor(
                  getRating(metric.cls, 'cls')
                )}`}
              >
                {getRating(metric.cls, 'cls')}
              </span>
            </div>

            <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-3">
              <p className="text-xs text-gray-600 dark:text-gray-400 mb-1">FCP</p>
              <p className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                {(metric.fcp / 1000).toFixed(2)}s
              </p>
              <span
                className={`inline-flex mt-1 px-2 py-0.5 rounded text-xs font-medium ${getRatingColor(
                  getRating(metric.fcp, 'fcp')
                )}`}
              >
                {getRating(metric.fcp, 'fcp')}
              </span>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};
