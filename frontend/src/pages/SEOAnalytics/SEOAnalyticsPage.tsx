/**
 * SEO Analytics Page
 * Keyword rankings, SERP features, and PageSpeed metrics
 */

import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Plus, Download, TrendingUp, TrendingDown } from 'lucide-react';
import { seoApi } from '../../api';
import { SEOFilters } from '../../types';
import { Button, Card, Input } from '../../components/common';
import { KeywordRankingsTable } from './KeywordRankingsTable';
import { SerpFeaturesChart } from './SerpFeaturesChart';
import { PageSpeedMetrics } from './PageSpeedMetrics';
import { CompetitorRankingsChart } from './CompetitorRankingsChart';
import { LoadingSpinner } from '../../components/common/Loading';

export const SEOAnalyticsPage: React.FC = () => {
  const [filters, setFilters] = useState<SEOFilters>({});
  const [searchTerm, setSearchTerm] = useState('');

  // Fetch SEO analytics
  const { data: analyticsData, isLoading } = useQuery({
    queryKey: ['seo-analytics', filters],
    queryFn: () => seoApi.getAnalytics(filters),
  });

  const handleSearch = (value: string) => {
    setSearchTerm(value);
    setFilters((prev) => ({ ...prev, search: value || undefined }));
  };

  const analytics = analyticsData || {
    keywords: [],
    total_keywords: 0,
    average_position: 0,
    visibility_score: 0,
    serp_features: [],
    competitor_comparison: [],
    page_speed: [],
    last_updated: new Date().toISOString(),
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
            SEO Analytics
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Monitor keyword rankings and SEO performance
          </p>
        </div>
        <Button variant="primary" icon={<Plus size={18} />}>
          Add Keyword
        </Button>
      </div>

      {/* Metrics Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card padding="lg">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Total Keywords</p>
              <p className="text-3xl font-bold text-gray-900 dark:text-gray-100 mt-1">
                {analytics.total_keywords}
              </p>
            </div>
            <div className="p-3 bg-primary-100 dark:bg-primary-900/30 rounded-lg">
              <TrendingUp className="text-primary-600 dark:text-primary-400" size={24} />
            </div>
          </div>
        </Card>

        <Card padding="lg">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Avg. Position</p>
              <p className="text-3xl font-bold text-gray-900 dark:text-gray-100 mt-1">
                {analytics.average_position.toFixed(1)}
              </p>
            </div>
            <div className="p-3 bg-success-100 dark:bg-success-900/30 rounded-lg">
              <TrendingDown className="text-success-600 dark:text-success-400" size={24} />
            </div>
          </div>
        </Card>

        <Card padding="lg">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Visibility Score</p>
              <p className="text-3xl font-bold text-gray-900 dark:text-gray-100 mt-1">
                {analytics.visibility_score.toFixed(0)}%
              </p>
            </div>
            <div className="p-3 bg-warning-100 dark:bg-warning-900/30 rounded-lg">
              <TrendingUp className="text-warning-600 dark:text-warning-400" size={24} />
            </div>
          </div>
        </Card>

        <Card padding="lg">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">SERP Features</p>
              <p className="text-3xl font-bold text-gray-900 dark:text-gray-100 mt-1">
                {analytics.serp_features.length}
              </p>
            </div>
            <div className="p-3 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
              <TrendingUp className="text-blue-600 dark:text-blue-400" size={24} />
            </div>
          </div>
        </Card>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <div className="p-4 border-b border-gray-200 dark:border-gray-700">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              SERP Features Distribution
            </h3>
          </div>
          <div className="p-4">
            {isLoading ? (
              <div className="flex items-center justify-center h-64">
                <LoadingSpinner size="lg" />
              </div>
            ) : (
              <SerpFeaturesChart features={analytics.serp_features} />
            )}
          </div>
        </Card>

        <Card>
          <div className="p-4 border-b border-gray-200 dark:border-gray-700">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              Competitor Rankings
            </h3>
          </div>
          <div className="p-4">
            {isLoading ? (
              <div className="flex items-center justify-center h-64">
                <LoadingSpinner size="lg" />
              </div>
            ) : (
              <CompetitorRankingsChart rankings={analytics.competitor_comparison} />
            )}
          </div>
        </Card>
      </div>

      {/* PageSpeed Metrics */}
      <Card>
        <div className="p-4 border-b border-gray-200 dark:border-gray-700">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
            Core Web Vitals
          </h3>
        </div>
        <div className="p-4">
          {isLoading ? (
            <div className="flex items-center justify-center h-32">
              <LoadingSpinner size="lg" />
            </div>
          ) : (
            <PageSpeedMetrics metrics={analytics.page_speed} />
          )}
        </div>
      </Card>

      {/* Keyword Rankings Table */}
      <Card>
        <div className="p-4 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              Keyword Rankings
            </h3>
            <Button variant="secondary" size="sm" icon={<Download size={16} />}>
              Export
            </Button>
          </div>
        </div>
        <div className="p-4">
          <Input
            placeholder="Search keywords..."
            value={searchTerm}
            onChange={(e) => handleSearch(e.target.value)}
            className="mb-4"
          />
          {isLoading ? (
            <div className="flex items-center justify-center h-64">
              <LoadingSpinner size="lg" />
            </div>
          ) : (
            <KeywordRankingsTable keywords={analytics.keywords} />
          )}
        </div>
      </Card>
    </div>
  );
};
