/**
 * Report Types
 * Type definitions for report-related data
 */

export type ReportType = 'content' | 'sentiment' | 'seo' | 'competitor' | 'audience';
export type ReportStatus = 'pending' | 'processing' | 'completed' | 'failed';
export type ReportFormat = 'pdf' | 'json' | 'csv';

export interface Report {
  id: string;
  title: string;
  description?: string;
  type: ReportType;
  status: ReportStatus;
  progress?: number;
  created_at: string;
  updated_at?: string;
  completed_at?: string;
  created_by: number;
  file_url?: string;
  error_message?: string;
  metadata?: Record<string, any>;
}

export interface ReportCreate {
  title: string;
  description?: string;
  type: ReportType;
  parameters?: Record<string, any>;
}

export interface ReportFilters {
  search?: string;
  type?: ReportType;
  status?: ReportStatus;
  date_from?: string;
  date_to?: string;
  sort_by?: 'created_at' | 'updated_at' | 'title';
  sort_order?: 'asc' | 'desc';
}

export interface ReportListResponse {
  reports: Report[];
  total: number;
  page: number;
  page_size: number;
}

export interface ReportSchedule {
  id: number;
  report_type: ReportType;
  frequency: 'daily' | 'weekly' | 'monthly';
  day_of_week?: number;
  day_of_month?: number;
  time: string;
  enabled: boolean;
  next_run?: string;
}

export interface ChartData {
  labels: string[];
  datasets: {
    label: string;
    data: number[];
    backgroundColor?: string | string[];
    borderColor?: string | string[];
    borderWidth?: number;
  }[];
}

export interface ReportSection {
  id: string;
  title: string;
  type: 'chart' | 'table' | 'text' | 'metrics';
  data: any;
  chart_type?: 'line' | 'bar' | 'pie' | 'area';
}

export interface ReportDetails extends Report {
  sections: ReportSection[];
}
