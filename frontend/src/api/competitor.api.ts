/**
 * Competitor API
 * Competitor management endpoints
 */

import { apiClient } from './client';
import {
  Competitor,
  CompetitorCreate,
  CompetitorUpdate,
  CompetitorMetrics,
  CompetitorListResponse,
  CompetitorFilters,
  PaginationParams,
  Domain,
} from '../types';

export const competitorApi = {
  /**
   * Get list of competitors with filters and pagination
   */
  async list(params?: CompetitorFilters & PaginationParams): Promise<CompetitorListResponse> {
    const response = await apiClient.get<Competitor[]>('/competitor', params);
    // Transform the array response to match our list response type
    return {
      competitors: response as any,
      total: (response as any).length || 0,
      page: params?.page || 1,
      page_size: params?.page_size || 100,
    };
  },

  /**
   * Get a single competitor by ID
   */
  async get(id: number): Promise<Competitor> {
    return apiClient.get<Competitor>(`/competitor/${id}`);
  },

  /**
   * Create a new competitor
   */
  async create(data: CompetitorCreate): Promise<Competitor> {
    return apiClient.post<Competitor>('/competitor', data);
  },

  /**
   * Update an existing competitor
   */
  async update(id: number, data: CompetitorUpdate): Promise<Competitor> {
    return apiClient.put<Competitor>(`/competitor/${id}`, data);
  },

  /**
   * Delete a competitor
   */
  async delete(id: number): Promise<void> {
    return apiClient.delete<void>(`/competitor/${id}`);
  },

  /**
   * Bulk delete competitors
   */
  async bulkDelete(ids: number[]): Promise<void> {
    return apiClient.post<void>('/competitor/bulk-delete', { ids });
  },

  /**
   * Get competitor metrics
   */
  async getMetrics(id: number): Promise<CompetitorMetrics> {
    return apiClient.get<CompetitorMetrics>(`/competitor/${id}/metrics`);
  },

  /**
   * Add a domain to a competitor
   */
  async addDomain(competitorId: number, domain: string, isPrimary = false): Promise<Domain> {
    return apiClient.post<Domain>(`/competitor/${competitorId}/domains`, {
      domain,
      is_primary: isPrimary,
    });
  },

  /**
   * Remove a domain from a competitor
   */
  async removeDomain(competitorId: number, domainId: number): Promise<void> {
    return apiClient.delete<void>(`/competitor/${competitorId}/domains/${domainId}`);
  },

  /**
   * Export competitors list
   */
  async export(format: 'csv' | 'json', filters?: CompetitorFilters): Promise<Blob> {
    return apiClient.get<Blob>(`/competitor/export`, {
      ...filters,
      format,
    });
  },

  /**
   * Import competitors from file
   */
  async import(file: File): Promise<{ imported: number; errors: string[] }> {
    const formData = new FormData();
    formData.append('file', file);
    return apiClient.post<{ imported: number; errors: string[] }>('/competitor/import', formData);
  },
};
