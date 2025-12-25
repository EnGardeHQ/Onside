/**
 * Keyword Rankings Table
 * Displays keyword ranking data with historical trends
 */

import React from 'react';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { Keyword } from '../../types';
import { format } from 'date-fns';

interface KeywordRankingsTableProps {
  keywords: Keyword[];
}

export const KeywordRankingsTable: React.FC<KeywordRankingsTableProps> = ({ keywords }) => {
  const getPositionChange = (current?: number, previous?: number) => {
    if (!current || !previous) return null;
    return previous - current; // Positive means improvement (lower position number)
  };

  const renderPositionChange = (change: number | null) => {
    if (change === null || change === 0) {
      return <Minus className="text-gray-400" size={16} />;
    }
    if (change > 0) {
      return (
        <div className="flex items-center gap-1 text-success-600 dark:text-success-400">
          <TrendingUp size={16} />
          <span className="text-sm font-medium">{change}</span>
        </div>
      );
    }
    return (
      <div className="flex items-center gap-1 text-danger-600 dark:text-danger-400">
        <TrendingDown size={16} />
        <span className="text-sm font-medium">{Math.abs(change)}</span>
      </div>
    );
  };

  if (keywords.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500 dark:text-gray-400">
        No keywords tracked yet. Add keywords to start monitoring rankings.
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead className="bg-gray-50 dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700">
          <tr>
            <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900 dark:text-gray-100">
              Keyword
            </th>
            <th className="px-4 py-3 text-center text-sm font-semibold text-gray-900 dark:text-gray-100">
              Position
            </th>
            <th className="px-4 py-3 text-center text-sm font-semibold text-gray-900 dark:text-gray-100">
              Change
            </th>
            <th className="px-4 py-3 text-right text-sm font-semibold text-gray-900 dark:text-gray-100">
              Search Volume
            </th>
            <th className="px-4 py-3 text-right text-sm font-semibold text-gray-900 dark:text-gray-100">
              Competition
            </th>
            <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900 dark:text-gray-100">
              URL
            </th>
            <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900 dark:text-gray-100">
              Last Updated
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
          {keywords.map((keyword) => {
            const positionChange = getPositionChange(keyword.current_position, keyword.previous_position);
            return (
              <tr key={keyword.id} className="hover:bg-gray-50 dark:hover:bg-gray-800/50">
                <td className="px-4 py-3">
                  <span className="font-medium text-gray-900 dark:text-gray-100">
                    {keyword.keyword}
                  </span>
                </td>
                <td className="px-4 py-3 text-center">
                  <span className="inline-flex items-center justify-center w-12 h-8 bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300 rounded font-semibold">
                    {keyword.current_position || '-'}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center justify-center">
                    {renderPositionChange(positionChange)}
                  </div>
                </td>
                <td className="px-4 py-3 text-right text-gray-700 dark:text-gray-300">
                  {keyword.search_volume.toLocaleString()}
                </td>
                <td className="px-4 py-3 text-right">
                  <span
                    className={`inline-flex px-2 py-1 rounded text-xs font-medium ${
                      keyword.competition < 0.3
                        ? 'bg-success-100 dark:bg-success-900/30 text-success-700 dark:text-success-300'
                        : keyword.competition < 0.7
                        ? 'bg-warning-100 dark:bg-warning-900/30 text-warning-700 dark:text-warning-300'
                        : 'bg-danger-100 dark:bg-danger-900/30 text-danger-700 dark:text-danger-300'
                    }`}
                  >
                    {(keyword.competition * 100).toFixed(0)}%
                  </span>
                </td>
                <td className="px-4 py-3">
                  {keyword.url ? (
                    <a
                      href={keyword.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-primary-600 dark:text-primary-400 hover:underline text-sm truncate max-w-xs block"
                    >
                      {keyword.url}
                    </a>
                  ) : (
                    <span className="text-gray-400 dark:text-gray-600 text-sm">-</span>
                  )}
                </td>
                <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">
                  {format(new Date(keyword.last_updated), 'MMM d, yyyy')}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
};
