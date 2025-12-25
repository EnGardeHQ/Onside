/**
 * SEO Types
 * Type definitions for SEO analytics data
 */

export interface Keyword {
  id: number;
  keyword: string;
  search_volume: number;
  competition: number;
  cpc?: number;
  trend?: number[];
  current_position?: number;
  previous_position?: number;
  best_position?: number;
  url?: string;
  last_updated: string;
}

export interface KeywordRanking {
  keyword_id: number;
  keyword: string;
  position: number;
  url: string;
  search_volume: number;
  date: string;
  serp_features?: string[];
}

export interface KeywordHistory {
  keyword_id: number;
  keyword: string;
  history: {
    date: string;
    position: number;
    search_volume: number;
  }[];
}

export interface SerpFeature {
  feature: string;
  count: number;
  percentage: number;
}

export interface PageSpeedMetrics {
  url: string;
  performance_score: number;
  fcp: number; // First Contentful Paint
  lcp: number; // Largest Contentful Paint
  fid: number; // First Input Delay
  cls: number; // Cumulative Layout Shift
  ttfb: number; // Time to First Byte
  tti: number; // Time to Interactive
  last_updated: string;
}

export interface CoreWebVitals {
  lcp: {
    value: number;
    rating: 'good' | 'needs-improvement' | 'poor';
  };
  fid: {
    value: number;
    rating: 'good' | 'needs-improvement' | 'poor';
  };
  cls: {
    value: number;
    rating: 'good' | 'needs-improvement' | 'poor';
  };
}

export interface CompetitorRanking {
  competitor_id: number;
  competitor_name: string;
  rankings: {
    keyword: string;
    position: number;
    url: string;
  }[];
  average_position: number;
  visibility_score: number;
}

export interface KeywordTrackingConfig {
  keyword: string;
  target_url?: string;
  location?: string;
  language?: string;
  device?: 'desktop' | 'mobile';
  frequency: 'daily' | 'weekly';
  enabled: boolean;
}

export interface SEOAnalytics {
  keywords: Keyword[];
  total_keywords: number;
  average_position: number;
  visibility_score: number;
  serp_features: SerpFeature[];
  competitor_comparison: CompetitorRanking[];
  page_speed: PageSpeedMetrics[];
  last_updated: string;
}

export interface SEOFilters {
  search?: string;
  min_volume?: number;
  max_volume?: number;
  min_position?: number;
  max_position?: number;
  date_from?: string;
  date_to?: string;
  sort_by?: 'keyword' | 'position' | 'search_volume' | 'competition';
  sort_order?: 'asc' | 'desc';
}
