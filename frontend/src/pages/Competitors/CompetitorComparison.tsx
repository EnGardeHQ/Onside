/**
 * Competitor Comparison Component
 * Side-by-side comparison of competitors
 */

import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { X } from 'lucide-react';
import { competitorApi } from '../../api';
import { Button, Card } from '../../components/common';
import { LoadingSpinner } from '../../components/common/Loading';

interface CompetitorComparisonProps {
  competitorIds: number[];
  onClose: () => void;
}

export const CompetitorComparison: React.FC<CompetitorComparisonProps> = ({
  competitorIds,
  onClose,
}) => {
  const competitorQueries = useQuery({
    queryKey: ['competitors', 'comparison', competitorIds],
    queryFn: async () => {
      const results = await Promise.all(
        competitorIds.map((id) => competitorApi.get(id))
      );
      return results;
    },
  });

  if (competitorQueries.isLoading) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <Card className="p-8">
          <LoadingSpinner size="lg" />
        </Card>
      </div>
    );
  }

  const competitors = competitorQueries.data || [];

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-6xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
            Competitor Comparison
          </h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
          >
            <X size={20} />
          </button>
        </div>

        {/* Comparison Table */}
        <div className="p-6 overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr>
                <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900 dark:text-gray-100">
                  Attribute
                </th>
                {competitors.map((competitor) => (
                  <th
                    key={competitor.id}
                    className="px-4 py-3 text-left text-sm font-semibold text-gray-900 dark:text-gray-100"
                  >
                    {competitor.name}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
              <tr>
                <td className="px-4 py-3 text-sm font-medium text-gray-700 dark:text-gray-300">
                  Website
                </td>
                {competitors.map((competitor) => (
                  <td key={competitor.id} className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">
                    {competitor.website ? (
                      <a
                        href={competitor.website}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-primary-600 dark:text-primary-400 hover:underline"
                      >
                        {competitor.website}
                      </a>
                    ) : (
                      '-'
                    )}
                  </td>
                ))}
              </tr>
              <tr>
                <td className="px-4 py-3 text-sm font-medium text-gray-700 dark:text-gray-300">
                  Industry
                </td>
                {competitors.map((competitor) => (
                  <td key={competitor.id} className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">
                    {competitor.industry || '-'}
                  </td>
                ))}
              </tr>
              <tr>
                <td className="px-4 py-3 text-sm font-medium text-gray-700 dark:text-gray-300">
                  Company Size
                </td>
                {competitors.map((competitor) => (
                  <td key={competitor.id} className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">
                    {competitor.size || '-'}
                  </td>
                ))}
              </tr>
              <tr>
                <td className="px-4 py-3 text-sm font-medium text-gray-700 dark:text-gray-300">
                  Location
                </td>
                {competitors.map((competitor) => (
                  <td key={competitor.id} className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">
                    {competitor.location || '-'}
                  </td>
                ))}
              </tr>
              <tr>
                <td className="px-4 py-3 text-sm font-medium text-gray-700 dark:text-gray-300">
                  Domains
                </td>
                {competitors.map((competitor) => (
                  <td key={competitor.id} className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">
                    {competitor.domains?.length || 0}
                  </td>
                ))}
              </tr>
              <tr>
                <td className="px-4 py-3 text-sm font-medium text-gray-700 dark:text-gray-300">
                  Tracking Status
                </td>
                {competitors.map((competitor) => (
                  <td key={competitor.id} className="px-4 py-3 text-sm">
                    <span
                      className={`inline-flex px-2 py-1 rounded-full text-xs font-medium ${
                        competitor.tracking_enabled
                          ? 'bg-success-100 dark:bg-success-900/30 text-success-700 dark:text-success-300'
                          : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
                      }`}
                    >
                      {competitor.tracking_enabled ? 'Enabled' : 'Disabled'}
                    </span>
                  </td>
                ))}
              </tr>
            </tbody>
          </table>
        </div>

        {/* Footer */}
        <div className="p-6 border-t border-gray-200 dark:border-gray-700">
          <Button variant="secondary" onClick={onClose} fullWidth>
            Close
          </Button>
        </div>
      </div>
    </div>
  );
};
