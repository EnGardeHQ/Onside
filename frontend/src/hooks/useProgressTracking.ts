/**
 * Custom React Hook for WebSocket Progress Tracking
 *
 * This hook provides real-time progress tracking for long-running operations
 * like report generation, integrating with the backend WebSocket API.
 *
 * Features:
 * - Automatic connection management
 * - Reconnection on disconnect
 * - Progress state management
 * - Error handling
 * - Clean disconnection on unmount
 */

import { useState, useEffect, useCallback, useRef } from 'react';

export enum ProgressStatus {
  IDLE = 'idle',
  CONNECTING = 'connecting',
  IN_PROGRESS = 'in_progress',
  COMPLETED = 'completed',
  FAILED = 'failed',
  CANCELLED = 'cancelled'
}

export enum ProgressStage {
  DATA_COLLECTION = 'data_collection',
  COMPETITOR_ANALYSIS = 'competitor_analysis',
  MARKET_ANALYSIS = 'market_analysis',
  AUDIENCE_ANALYSIS = 'audience_analysis',
  REPORT_GENERATION = 'report_generation',
  VISUALIZATION = 'visualization',
  FINALIZATION = 'finalization'
}

export interface StageProgress {
  stage: ProgressStage;
  progress: number; // 0 to 1
  label: string;
  description: string;
}

export interface ProgressData {
  status: ProgressStatus;
  currentStage: ProgressStage;
  overallProgress: number; // 0 to 100
  stageProgress: Record<ProgressStage, number>;
  estimatedTimeRemaining?: number; // in seconds
  errorMessage?: string;
  errorDetails?: Record<string, any>;
  startedAt?: string;
  completedAt?: string;
}

interface UseProgressTrackingOptions {
  reportId: number;
  userId: number;
  onComplete?: (data: ProgressData) => void;
  onError?: (error: string) => void;
  autoReconnect?: boolean;
  reconnectDelay?: number; // milliseconds
  wsBaseUrl?: string;
}

interface UseProgressTrackingReturn {
  progressData: ProgressData | null;
  isConnected: boolean;
  connect: () => void;
  disconnect: () => void;
  cancelReport: () => void;
  stageLabels: Record<ProgressStage, string>;
}

const STAGE_LABELS: Record<ProgressStage, string> = {
  [ProgressStage.DATA_COLLECTION]: 'Collecting Data',
  [ProgressStage.COMPETITOR_ANALYSIS]: 'Analyzing Competitors',
  [ProgressStage.MARKET_ANALYSIS]: 'Analyzing Market',
  [ProgressStage.AUDIENCE_ANALYSIS]: 'Analyzing Audience',
  [ProgressStage.REPORT_GENERATION]: 'Generating Report',
  [ProgressStage.VISUALIZATION]: 'Creating Visualizations',
  [ProgressStage.FINALIZATION]: 'Finalizing Report'
};

export const useProgressTracking = ({
  reportId,
  userId,
  onComplete,
  onError,
  autoReconnect = true,
  reconnectDelay = 3000,
  wsBaseUrl = process.env.REACT_APP_WS_URL || 'ws://localhost:8000'
}: UseProgressTrackingOptions): UseProgressTrackingReturn => {
  const [progressData, setProgressData] = useState<ProgressData | null>(null);
  const [isConnected, setIsConnected] = useState(false);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const shouldReconnectRef = useRef(autoReconnect);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      console.log('WebSocket already connected');
      return;
    }

    try {
      const wsUrl = `${wsBaseUrl}/api/v1/progress/ws/${reportId}?user_id=${userId}`;
      console.log('Connecting to WebSocket:', wsUrl);

      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        shouldReconnectRef.current = autoReconnect;
      };

      ws.onmessage = (event) => {
        try {
          const data: ProgressData = JSON.parse(event.data);
          console.log('Progress update:', data);

          setProgressData(data);

          // Handle completion
          if (data.status === ProgressStatus.COMPLETED) {
            onComplete?.(data);
            shouldReconnectRef.current = false;
          }

          // Handle errors
          if (data.status === ProgressStatus.FAILED) {
            onError?.(data.errorMessage || 'Unknown error occurred');
            shouldReconnectRef.current = false;
          }

          // Handle cancellation
          if (data.status === ProgressStatus.CANCELLED) {
            shouldReconnectRef.current = false;
          }
        } catch (error) {
          console.error('Error parsing progress data:', error);
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        onError?.('WebSocket connection error');
      };

      ws.onclose = (event) => {
        console.log('WebSocket closed:', event.code, event.reason);
        setIsConnected(false);

        // Attempt reconnection if needed
        if (shouldReconnectRef.current && !event.wasClean) {
          console.log(`Reconnecting in ${reconnectDelay}ms...`);
          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, reconnectDelay);
        }
      };
    } catch (error) {
      console.error('Error creating WebSocket connection:', error);
      onError?.('Failed to create WebSocket connection');
    }
  }, [reportId, userId, wsBaseUrl, autoReconnect, reconnectDelay, onComplete, onError]);

  const disconnect = useCallback(() => {
    shouldReconnectRef.current = false;

    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    setIsConnected(false);
  }, []);

  const cancelReport = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ command: 'cancel' }));
    }
  }, []);

  // Auto-connect on mount
  useEffect(() => {
    connect();

    // Cleanup on unmount
    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  return {
    progressData,
    isConnected,
    connect,
    disconnect,
    cancelReport,
    stageLabels: STAGE_LABELS
  };
};

/**
 * Utility function to format estimated time remaining
 */
export const formatTimeRemaining = (seconds?: number): string => {
  if (!seconds) return 'Calculating...';

  if (seconds < 60) {
    return `${Math.ceil(seconds)}s`;
  } else if (seconds < 3600) {
    const minutes = Math.ceil(seconds / 60);
    return `${minutes}m`;
  } else {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.ceil((seconds % 3600) / 60);
    return `${hours}h ${minutes}m`;
  }
};

/**
 * Utility function to get progress color based on status
 */
export const getProgressColor = (status: ProgressStatus): string => {
  switch (status) {
    case ProgressStatus.IN_PROGRESS:
      return '#1f77b4'; // Blue
    case ProgressStatus.COMPLETED:
      return '#28a745'; // Green
    case ProgressStatus.FAILED:
      return '#dc3545'; // Red
    case ProgressStatus.CANCELLED:
      return '#6c757d'; // Gray
    default:
      return '#ffc107'; // Yellow
  }
};
