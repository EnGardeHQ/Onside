/**
 * En Garde API
 * Brand analysis and setup wizard endpoints
 */

import { apiClient } from './client';
import {
  BrandAnalysisRequest,
  BrandAnalysisInitResponse,
  AnalysisStatus,
  BrandAnalysisResults,
  ConfirmAnalysisRequest,
  ConfirmAnalysisResponse,
} from '../types';

export const engardeApi = {
  /**
   * Initiate brand analysis with questionnaire data
   */
  async initiateBrandAnalysis(data: BrandAnalysisRequest): Promise<BrandAnalysisInitResponse> {
    return apiClient.post<BrandAnalysisInitResponse>('/engarde/brand-analysis/initiate', data);
  },

  /**
   * Get analysis status
   */
  async getAnalysisStatus(analysisId: string): Promise<AnalysisStatus> {
    return apiClient.get<AnalysisStatus>(`/engarde/brand-analysis/${analysisId}/status`);
  },

  /**
   * Get analysis results
   */
  async getAnalysisResults(analysisId: string): Promise<BrandAnalysisResults> {
    return apiClient.get<BrandAnalysisResults>(`/engarde/brand-analysis/${analysisId}/results`);
  },

  /**
   * Confirm analysis and import selected keywords/competitors
   */
  async confirmAnalysis(
    analysisId: string,
    data: ConfirmAnalysisRequest
  ): Promise<ConfirmAnalysisResponse> {
    return apiClient.post<ConfirmAnalysisResponse>(
      `/engarde/brand-analysis/${analysisId}/confirm`,
      data
    );
  },
};
