/**
 * SEO API
 * SEO analytics and keyword tracking endpoints
 */

import { apiClient } from './client';
import {
  Keyword,
  KeywordHistory,
  SerpFeature,
  PageSpeedMetrics,
  CompetitorRanking,
  KeywordTrackingConfig,
  SEOAnalytics,
  SEOFilters,
  PaginationParams,
} from '../types';

export const seoApi = {
  /**
   * Get SEO analytics overview
   */
  async getAnalytics(filters?: SEOFilters): Promise<SEOAnalytics> {
    return apiClient.get<SEOAnalytics>('/seo/analytics', filters);
  },

  /**
   * Get keyword rankings
   */
  async getKeywords(params?: SEOFilters & PaginationParams): Promise<Keyword[]> {
    return apiClient.get<Keyword[]>('/seo/keywords', params);
  },

  /**
   * Get keyword ranking history
   */
  async getKeywordHistory(keywordId: number, dateFrom?: string, dateTo?: string): Promise<KeywordHistory> {
    return apiClient.get<KeywordHistory>(`/seo/keywords/${keywordId}/history`, {
      date_from: dateFrom,
      date_to: dateTo,
    });
  },

  /**
   * Add a keyword for tracking
   */
  async addKeyword(config: KeywordTrackingConfig): Promise<Keyword> {
    return apiClient.post<Keyword>('/seo/keywords', config);
  },

  /**
   * Update keyword tracking configuration
   */
  async updateKeyword(keywordId: number, config: Partial<KeywordTrackingConfig>): Promise<Keyword> {
    return apiClient.put<Keyword>(`/seo/keywords/${keywordId}`, config);
  },

  /**
   * Delete a keyword from tracking
   */
  async deleteKeyword(keywordId: number): Promise<void> {
    return apiClient.delete<void>(`/seo/keywords/${keywordId}`);
  },

  /**
   * Get SERP features distribution
   */
  async getSerpFeatures(): Promise<SerpFeature[]> {
    return apiClient.get<SerpFeature[]>('/seo/serp-features');
  },

  /**
   * Get PageSpeed metrics for URLs
   */
  async getPageSpeed(urls?: string[]): Promise<PageSpeedMetrics[]> {
    return apiClient.get<PageSpeedMetrics[]>('/seo/pagespeed', { urls });
  },

  /**
   * Get competitor ranking comparison
   */
  async getCompetitorRankings(competitorIds?: number[]): Promise<CompetitorRanking[]> {
    return apiClient.get<CompetitorRanking[]>('/seo/competitor-rankings', {
      competitor_ids: competitorIds?.join(','),
    });
  },

  /**
   * Trigger keyword ranking update
   */
  async updateRankings(keywordIds?: number[]): Promise<{ updated: number; queued: number }> {
    return apiClient.post<{ updated: number; queued: number }>('/seo/update-rankings', {
      keyword_ids: keywordIds,
    });
  },

  /**
   * Export keyword data
   */
  async exportKeywords(format: 'csv' | 'json', filters?: SEOFilters): Promise<Blob> {
    return apiClient.get<Blob>('/seo/keywords/export', {
      ...filters,
      format,
    });
  },

  /**
   * Import keywords from file
   */
  async importKeywords(file: File): Promise<{ imported: number; errors: string[] }> {
    const formData = new FormData();
    formData.append('file', file);
    return apiClient.post<{ imported: number; errors: string[] }>('/seo/keywords/import', formData);
  },

  /**
   * Get SEO subjects (topics)
   */
  async getSubjects(): Promise<any[]> {
    return apiClient.get<any[]>('/seo/subjects');
  },

  /**
   * Create SEO subject
   */
  async createSubject(data: { name: string; market_scope: string; language: string }): Promise<any> {
    return apiClient.post<any>('/seo/subjects', data);
  },

  /**
   * Analyze SEO subject
   */
  async analyzeSubject(subjectId: number): Promise<{ message: string; subject_id: number }> {
    return apiClient.post<{ message: string; subject_id: number }>(`/seo/subjects/${subjectId}/analyze`);
  },
};
