/**
 * Report API
 * Report generation and management endpoints
 */

import { apiClient } from './client';
import {
  Report,
  ReportCreate,
  ReportListResponse,
  ReportFilters,
  ReportDetails,
  ReportSchedule,
  PaginationParams,
} from '../types';

export const reportApi = {
  /**
   * Get list of reports with filters and pagination
   */
  async list(params?: ReportFilters & PaginationParams): Promise<ReportListResponse> {
    const response = await apiClient.get<Report[]>('/reports', params);
    return {
      reports: response as any,
      total: (response as any).length || 0,
      page: params?.page || 1,
      page_size: params?.page_size || 20,
    };
  },

  /**
   * Get a single report by ID
   */
  async get(id: string): Promise<ReportDetails> {
    return apiClient.get<ReportDetails>(`/reports/${id}`);
  },

  /**
   * Create and generate a new report
   */
  async create(data: ReportCreate): Promise<Report> {
    return apiClient.post<Report>('/reports', data);
  },

  /**
   * Get report generation status
   */
  async getStatus(id: string): Promise<{ status: string; progress: number; message?: string }> {
    return apiClient.get<{ status: string; progress: number; message?: string }>(
      `/reports/${id}/status`
    );
  },

  /**
   * Cancel report generation
   */
  async cancel(id: string): Promise<void> {
    return apiClient.post<void>(`/reports/${id}/cancel`);
  },

  /**
   * Delete a report
   */
  async delete(id: string): Promise<void> {
    return apiClient.delete<void>(`/reports/${id}`);
  },

  /**
   * Download report file
   */
  async download(id: string, format: 'pdf' | 'json' | 'csv' = 'pdf'): Promise<Blob> {
    return apiClient.get<Blob>(`/reports/${id}/download`, {
      format,
      responseType: 'blob',
    } as any);
  },

  /**
   * Export report to PDF
   */
  async exportPdf(id: string): Promise<Blob> {
    return this.download(id, 'pdf');
  },

  /**
   * Get report schedules
   */
  async getSchedules(): Promise<ReportSchedule[]> {
    return apiClient.get<ReportSchedule[]>('/reports/schedules');
  },

  /**
   * Create a report schedule
   */
  async createSchedule(schedule: Omit<ReportSchedule, 'id' | 'next_run'>): Promise<ReportSchedule> {
    return apiClient.post<ReportSchedule>('/reports/schedules', schedule);
  },

  /**
   * Update a report schedule
   */
  async updateSchedule(id: number, schedule: Partial<ReportSchedule>): Promise<ReportSchedule> {
    return apiClient.put<ReportSchedule>(`/reports/schedules/${id}`, schedule);
  },

  /**
   * Delete a report schedule
   */
  async deleteSchedule(id: number): Promise<void> {
    return apiClient.delete<void>(`/reports/schedules/${id}`);
  },
};
