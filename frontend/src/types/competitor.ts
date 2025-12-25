/**
 * Competitor Types
 * Type definitions for competitor-related data
 */

export interface Competitor {
  id: number;
  name: string;
  website?: string;
  description?: string;
  industry?: string;
  size?: string;
  location?: string;
  domains: Domain[];
  tracking_enabled: boolean;
  created_at: string;
  updated_at?: string;
}

export interface Domain {
  id: number;
  domain: string;
  competitor_id: number;
  is_primary: boolean;
  created_at: string;
}

export interface CompetitorCreate {
  name: string;
  website?: string;
  description?: string;
  industry?: string;
  size?: string;
  location?: string;
  tracking_enabled?: boolean;
}

export interface CompetitorUpdate {
  name?: string;
  website?: string;
  description?: string;
  industry?: string;
  size?: string;
  location?: string;
  tracking_enabled?: boolean;
}

export interface CompetitorMetrics {
  competitor_id: number;
  website_traffic?: number;
  social_followers?: number;
  content_count?: number;
  engagement_rate?: number;
  last_updated: string;
}

export interface CompetitorComparison {
  competitors: Competitor[];
  metrics: {
    [competitorId: number]: CompetitorMetrics;
  };
}

export interface CompetitorFilters {
  search?: string;
  industry?: string;
  tracking_enabled?: boolean;
  sort_by?: 'name' | 'created_at' | 'updated_at';
  sort_order?: 'asc' | 'desc';
}

export interface CompetitorListResponse {
  competitors: Competitor[];
  total: number;
  page: number;
  page_size: number;
}
