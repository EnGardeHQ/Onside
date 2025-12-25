/**
 * Results Review Component
 * Review and select discovered keywords and competitors
 */

import React, { useState, useMemo } from 'react';
import {
  CheckCircle2,
  Circle,
  Search,
  TrendingUp,
  ArrowUpDown,
  Users,
  Building2,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent, Button } from '../../../components/common';
import { BrandAnalysisResults, DiscoveredKeyword, DiscoveredCompetitor } from '../../../types';

interface ResultsReviewProps {
  results: BrandAnalysisResults;
  onConfirm: (selectedKeywords: string[], selectedCompetitors: string[]) => void;
  onBack: () => void;
  isLoading?: boolean;
}

type SortField = 'keyword' | 'relevance' | 'volume' | 'source';
type SortOrder = 'asc' | 'desc';
type CompetitorSortField = 'domain' | 'relevance' | 'category';

export const ResultsReview: React.FC<ResultsReviewProps> = ({
  results,
  onConfirm,
  onBack,
  isLoading = false,
}) => {
  // Keywords state
  const [selectedKeywords, setSelectedKeywords] = useState<Set<string>>(
    new Set(results.discovered_keywords.map((k) => k.keyword))
  );
  const [keywordSearch, setKeywordSearch] = useState('');
  const [keywordSort, setKeywordSort] = useState<{ field: SortField; order: SortOrder }>({
    field: 'relevance',
    order: 'desc',
  });

  // Competitors state
  const [selectedCompetitors, setSelectedCompetitors] = useState<Set<string>>(
    new Set(results.discovered_competitors.map((c) => c.domain))
  );
  const [competitorSearch, setCompetitorSearch] = useState('');
  const [competitorSort, setCompetitorSort] = useState<{
    field: CompetitorSortField;
    order: SortOrder;
  }>({
    field: 'relevance',
    order: 'desc',
  });

  const [showKeywords, setShowKeywords] = useState(true);
  const [showCompetitors, setShowCompetitors] = useState(true);

  // Filter and sort keywords
  const filteredKeywords = useMemo(() => {
    let filtered = results.discovered_keywords.filter((k) =>
      k.keyword.toLowerCase().includes(keywordSearch.toLowerCase())
    );

    filtered.sort((a, b) => {
      let comparison = 0;
      switch (keywordSort.field) {
        case 'keyword':
          comparison = a.keyword.localeCompare(b.keyword);
          break;
        case 'relevance':
          comparison = a.relevance_score - b.relevance_score;
          break;
        case 'volume':
          comparison = (a.search_volume || 0) - (b.search_volume || 0);
          break;
        case 'source':
          comparison = a.source.localeCompare(b.source);
          break;
      }
      return keywordSort.order === 'asc' ? comparison : -comparison;
    });

    return filtered;
  }, [results.discovered_keywords, keywordSearch, keywordSort]);

  // Filter and sort competitors
  const filteredCompetitors = useMemo(() => {
    let filtered = results.discovered_competitors.filter(
      (c) =>
        c.domain.toLowerCase().includes(competitorSearch.toLowerCase()) ||
        c.company_name?.toLowerCase().includes(competitorSearch.toLowerCase())
    );

    filtered.sort((a, b) => {
      let comparison = 0;
      switch (competitorSort.field) {
        case 'domain':
          comparison = a.domain.localeCompare(b.domain);
          break;
        case 'relevance':
          comparison = a.relevance_score - b.relevance_score;
          break;
        case 'category':
          comparison = a.category.localeCompare(b.category);
          break;
      }
      return competitorSort.order === 'asc' ? comparison : -comparison;
    });

    return filtered;
  }, [results.discovered_competitors, competitorSearch, competitorSort]);

  const toggleKeyword = (keyword: string) => {
    const newSet = new Set(selectedKeywords);
    if (newSet.has(keyword)) {
      newSet.delete(keyword);
    } else {
      newSet.add(keyword);
    }
    setSelectedKeywords(newSet);
  };

  const toggleCompetitor = (domain: string) => {
    const newSet = new Set(selectedCompetitors);
    if (newSet.has(domain)) {
      newSet.delete(domain);
    } else {
      newSet.add(domain);
    }
    setSelectedCompetitors(newSet);
  };

  const selectAllKeywords = () => {
    setSelectedKeywords(new Set(filteredKeywords.map((k) => k.keyword)));
  };

  const deselectAllKeywords = () => {
    setSelectedKeywords(new Set());
  };

  const selectAllCompetitors = () => {
    setSelectedCompetitors(new Set(filteredCompetitors.map((c) => c.domain)));
  };

  const deselectAllCompetitors = () => {
    setSelectedCompetitors(new Set());
  };

  const handleSort = (field: SortField) => {
    setKeywordSort((prev) => ({
      field,
      order: prev.field === field && prev.order === 'desc' ? 'asc' : 'desc',
    }));
  };

  const handleCompetitorSort = (field: CompetitorSortField) => {
    setCompetitorSort((prev) => ({
      field,
      order: prev.field === field && prev.order === 'desc' ? 'asc' : 'desc',
    }));
  };

  const handleConfirm = () => {
    onConfirm(Array.from(selectedKeywords), Array.from(selectedCompetitors));
  };

  const getSourceBadge = (source: string) => {
    const badges = {
      website: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
      competitor: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400',
      industry: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
      inferred: 'bg-gray-100 text-gray-700 dark:bg-gray-900/30 dark:text-gray-400',
    };
    return badges[source as keyof typeof badges] || badges.inferred;
  };

  const getCategoryBadge = (category: string) => {
    const badges = {
      direct: 'bg-danger-100 text-danger-700 dark:bg-danger-900/30 dark:text-danger-400',
      indirect: 'bg-warning-100 text-warning-700 dark:bg-warning-900/30 dark:text-warning-400',
      potential: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
    };
    return badges[category as keyof typeof badges] || badges.potential;
  };

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <Card className="p-6">
        <div className="flex items-start justify-between">
          <div>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
              Review Analysis Results
            </h2>
            <p className="text-gray-600 dark:text-gray-400 mt-2">
              We found {results.discovered_keywords.length} keywords and{' '}
              {results.discovered_competitors.length} competitors for {results.brand_name}
            </p>
          </div>
          <div className="text-right">
            <p className="text-sm text-gray-600 dark:text-gray-400">Selected</p>
            <p className="text-2xl font-bold text-primary-500">
              {selectedKeywords.size + selectedCompetitors.size}
            </p>
          </div>
        </div>
      </Card>

      {/* Keywords Section */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <button
              onClick={() => setShowKeywords(!showKeywords)}
              className="flex items-center gap-2 text-left hover:opacity-80 transition-opacity"
            >
              <TrendingUp className="text-primary-500" size={24} />
              <CardTitle>
                Discovered Keywords ({selectedKeywords.size}/{results.discovered_keywords.length} selected)
              </CardTitle>
              {showKeywords ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
            </button>
            {showKeywords && (
              <div className="flex gap-2">
                <Button size="sm" variant="ghost" onClick={selectAllKeywords}>
                  Select All
                </Button>
                <Button size="sm" variant="ghost" onClick={deselectAllKeywords}>
                  Deselect All
                </Button>
              </div>
            )}
          </div>
        </CardHeader>

        {showKeywords && (
          <CardContent>
            {/* Search */}
            <div className="mb-4">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
                <input
                  type="text"
                  placeholder="Search keywords..."
                  value={keywordSearch}
                  onChange={(e) => setKeywordSearch(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-400"
                />
              </div>
            </div>

            {/* Keywords Table */}
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50 dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700">
                  <tr>
                    <th className="w-10 px-4 py-3"></th>
                    <th className="px-4 py-3 text-left">
                      <button
                        onClick={() => handleSort('keyword')}
                        className="flex items-center gap-1 font-semibold text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-gray-100"
                      >
                        Keyword
                        <ArrowUpDown size={14} />
                      </button>
                    </th>
                    <th className="px-4 py-3 text-left">
                      <button
                        onClick={() => handleSort('source')}
                        className="flex items-center gap-1 font-semibold text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-gray-100"
                      >
                        Source
                        <ArrowUpDown size={14} />
                      </button>
                    </th>
                    <th className="px-4 py-3 text-left">
                      <button
                        onClick={() => handleSort('relevance')}
                        className="flex items-center gap-1 font-semibold text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-gray-100"
                      >
                        Relevance
                        <ArrowUpDown size={14} />
                      </button>
                    </th>
                    <th className="px-4 py-3 text-left">
                      <button
                        onClick={() => handleSort('volume')}
                        className="flex items-center gap-1 font-semibold text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-gray-100"
                      >
                        Volume
                        <ArrowUpDown size={14} />
                      </button>
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                  {filteredKeywords.map((keyword) => (
                    <tr
                      key={keyword.keyword}
                      onClick={() => toggleKeyword(keyword.keyword)}
                      className="cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
                    >
                      <td className="px-4 py-3">
                        {selectedKeywords.has(keyword.keyword) ? (
                          <CheckCircle2 className="text-primary-500" size={20} />
                        ) : (
                          <Circle className="text-gray-400" size={20} />
                        )}
                      </td>
                      <td className="px-4 py-3 font-medium text-gray-900 dark:text-gray-100">
                        {keyword.keyword}
                      </td>
                      <td className="px-4 py-3">
                        <span
                          className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${getSourceBadge(
                            keyword.source
                          )}`}
                        >
                          {keyword.source}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          <div className="w-20 bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                            <div
                              className="bg-primary-500 h-2 rounded-full"
                              style={{ width: `${keyword.relevance_score * 100}%` }}
                            />
                          </div>
                          <span className="text-sm text-gray-600 dark:text-gray-400">
                            {Math.round(keyword.relevance_score * 100)}%
                          </span>
                        </div>
                      </td>
                      <td className="px-4 py-3 text-gray-600 dark:text-gray-400">
                        {keyword.search_volume?.toLocaleString() || 'N/A'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {filteredKeywords.length === 0 && (
              <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                No keywords found matching your search
              </div>
            )}
          </CardContent>
        )}
      </Card>

      {/* Competitors Section */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <button
              onClick={() => setShowCompetitors(!showCompetitors)}
              className="flex items-center gap-2 text-left hover:opacity-80 transition-opacity"
            >
              <Users className="text-primary-500" size={24} />
              <CardTitle>
                Discovered Competitors ({selectedCompetitors.size}/{results.discovered_competitors.length} selected)
              </CardTitle>
              {showCompetitors ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
            </button>
            {showCompetitors && (
              <div className="flex gap-2">
                <Button size="sm" variant="ghost" onClick={selectAllCompetitors}>
                  Select All
                </Button>
                <Button size="sm" variant="ghost" onClick={deselectAllCompetitors}>
                  Deselect All
                </Button>
              </div>
            )}
          </div>
        </CardHeader>

        {showCompetitors && (
          <CardContent>
            {/* Search */}
            <div className="mb-4">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
                <input
                  type="text"
                  placeholder="Search competitors..."
                  value={competitorSearch}
                  onChange={(e) => setCompetitorSearch(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-400"
                />
              </div>
            </div>

            {/* Competitors Table */}
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50 dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700">
                  <tr>
                    <th className="w-10 px-4 py-3"></th>
                    <th className="px-4 py-3 text-left">
                      <button
                        onClick={() => handleCompetitorSort('domain')}
                        className="flex items-center gap-1 font-semibold text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-gray-100"
                      >
                        Competitor
                        <ArrowUpDown size={14} />
                      </button>
                    </th>
                    <th className="px-4 py-3 text-left">
                      <button
                        onClick={() => handleCompetitorSort('category')}
                        className="flex items-center gap-1 font-semibold text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-gray-100"
                      >
                        Category
                        <ArrowUpDown size={14} />
                      </button>
                    </th>
                    <th className="px-4 py-3 text-left">
                      <button
                        onClick={() => handleCompetitorSort('relevance')}
                        className="flex items-center gap-1 font-semibold text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-gray-100"
                      >
                        Relevance
                        <ArrowUpDown size={14} />
                      </button>
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                  {filteredCompetitors.map((competitor) => (
                    <tr
                      key={competitor.domain}
                      onClick={() => toggleCompetitor(competitor.domain)}
                      className="cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
                    >
                      <td className="px-4 py-3">
                        {selectedCompetitors.has(competitor.domain) ? (
                          <CheckCircle2 className="text-primary-500" size={20} />
                        ) : (
                          <Circle className="text-gray-400" size={20} />
                        )}
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          <Building2 className="text-gray-400" size={18} />
                          <div>
                            <p className="font-medium text-gray-900 dark:text-gray-100">
                              {competitor.company_name || competitor.domain}
                            </p>
                            {competitor.company_name && (
                              <p className="text-sm text-gray-500 dark:text-gray-400">
                                {competitor.domain}
                              </p>
                            )}
                          </div>
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <span
                          className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${getCategoryBadge(
                            competitor.category
                          )}`}
                        >
                          {competitor.category}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          <div className="w-20 bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                            <div
                              className="bg-primary-500 h-2 rounded-full"
                              style={{ width: `${competitor.relevance_score * 100}%` }}
                            />
                          </div>
                          <span className="text-sm text-gray-600 dark:text-gray-400">
                            {Math.round(competitor.relevance_score * 100)}%
                          </span>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {filteredCompetitors.length === 0 && (
              <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                No competitors found matching your search
              </div>
            )}
          </CardContent>
        )}
      </Card>

      {/* Action Buttons */}
      <div className="flex gap-3">
        <Button variant="secondary" onClick={onBack} disabled={isLoading}>
          Back
        </Button>
        <Button
          variant="primary"
          onClick={handleConfirm}
          isLoading={isLoading}
          fullWidth
          disabled={selectedKeywords.size === 0 && selectedCompetitors.size === 0}
        >
          Confirm & Import ({selectedKeywords.size + selectedCompetitors.size} items)
        </Button>
      </div>
    </div>
  );
};
