/**
 * En Garde Hooks
 * Custom hooks for En Garde brand analysis operations
 */

import { useState, useEffect, useCallback } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { engardeApi } from '../api/engarde.api';
import {
  BrandAnalysisRequest,
  BrandAnalysisInitResponse,
  AnalysisStatus,
  BrandAnalysisResults,
  ConfirmAnalysisRequest,
  ConfirmAnalysisResponse,
} from '../types';

/**
 * Hook to initiate brand analysis
 */
export const useBrandAnalysis = () => {
  return useMutation<BrandAnalysisInitResponse, Error, BrandAnalysisRequest>({
    mutationFn: (data: BrandAnalysisRequest) => engardeApi.initiateBrandAnalysis(data),
  });
};

/**
 * Hook to poll analysis status
 */
export const useAnalysisStatus = (
  analysisId: string | undefined,
  options?: {
    enabled?: boolean;
    refetchInterval?: number;
  }
) => {
  const { enabled = true, refetchInterval = 3000 } = options || {};

  return useQuery<AnalysisStatus, Error>({
    queryKey: ['analysis-status', analysisId],
    queryFn: () => engardeApi.getAnalysisStatus(analysisId!),
    enabled: !!analysisId && enabled,
    refetchInterval: (query) => {
      const data = query.state.data;
      // Stop polling if completed or failed
      if (data?.status === 'completed' || data?.status === 'failed') {
        return false;
      }
      return refetchInterval;
    },
    retry: 3,
  });
};

/**
 * Hook to fetch analysis results
 */
export const useAnalysisResults = (analysisId: string | undefined, enabled: boolean = true) => {
  return useQuery<BrandAnalysisResults, Error>({
    queryKey: ['analysis-results', analysisId],
    queryFn: () => engardeApi.getAnalysisResults(analysisId!),
    enabled: !!analysisId && enabled,
    retry: 2,
  });
};

/**
 * Hook to confirm analysis and import data
 */
export const useConfirmAnalysis = (analysisId: string | undefined) => {
  return useMutation<ConfirmAnalysisResponse, Error, ConfirmAnalysisRequest>({
    mutationFn: (data: ConfirmAnalysisRequest) =>
      engardeApi.confirmAnalysis(analysisId!, data),
  });
};

/**
 * Combined hook for the entire analysis workflow
 */
export const useAnalysisWorkflow = () => {
  const [analysisId, setAnalysisId] = useState<string>();
  const [isPolling, setIsPolling] = useState(false);
  const [isCompleted, setIsCompleted] = useState(false);

  const initiateMutation = useBrandAnalysis();
  const statusQuery = useAnalysisStatus(analysisId, { enabled: isPolling });
  const resultsQuery = useAnalysisResults(analysisId, isCompleted);
  const confirmMutation = useConfirmAnalysis(analysisId);

  // Start analysis
  const startAnalysis = useCallback(async (data: BrandAnalysisRequest) => {
    setIsCompleted(false);
    const response = await initiateMutation.mutateAsync(data);
    setAnalysisId(response.analysis_id);
    setIsPolling(true);
    return response;
  }, [initiateMutation]);

  // Monitor status changes
  useEffect(() => {
    if (statusQuery.data?.status === 'completed') {
      setIsPolling(false);
      setIsCompleted(true);
    } else if (statusQuery.data?.status === 'failed') {
      setIsPolling(false);
    }
  }, [statusQuery.data?.status]);

  // Confirm and import
  const confirmAndImport = useCallback(async (data: ConfirmAnalysisRequest) => {
    return confirmMutation.mutateAsync(data);
  }, [confirmMutation]);

  // Reset workflow
  const reset = useCallback(() => {
    setAnalysisId(undefined);
    setIsPolling(false);
    setIsCompleted(false);
  }, []);

  return {
    analysisId,
    status: statusQuery.data,
    results: resultsQuery.data,
    startAnalysis,
    confirmAndImport,
    reset,
    isInitiating: initiateMutation.isPending,
    isPolling,
    isCompleted,
    error: initiateMutation.error || statusQuery.error || resultsQuery.error || confirmMutation.error,
  };
};
