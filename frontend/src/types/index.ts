/**
 * Common Types
 * Shared type definitions across the application
 */

export * from './auth';
export * from './competitor';
export * from './report';
export * from './seo';
export * from './engarde';

export interface PaginationParams {
  page?: number;
  page_size?: number;
  skip?: number;
  limit?: number;
}

export interface SortParams {
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

export interface ApiError {
  message: string;
  status?: number;
  detail?: string;
  errors?: Record<string, string[]>;
}

export interface ApiResponse<T> {
  data: T;
  message?: string;
  status: number;
}

export interface ListResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export type ThemeMode = 'light' | 'dark' | 'system';

export interface AppConfig {
  apiUrl: string;
  wsUrl: string;
  environment: 'development' | 'staging' | 'production';
}
