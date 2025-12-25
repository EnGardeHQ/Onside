/**
 * Competitor List Component
 * Table view of competitors with actions
 */

import React from 'react';
import { Edit2, Trash2, ExternalLink, CheckSquare, Square } from 'lucide-react';
import { Competitor } from '../../types';
import { Button } from '../../components/common';
import { format } from 'date-fns';

interface CompetitorListProps {
  competitors: Competitor[];
  selectedIds: number[];
  onSelectionChange: (ids: number[]) => void;
  onEdit: (competitor: Competitor) => void;
  onDelete: (id: number) => void;
}

export const CompetitorList: React.FC<CompetitorListProps> = ({
  competitors,
  selectedIds,
  onSelectionChange,
  onEdit,
  onDelete,
}) => {
  const allSelected = competitors.length > 0 && selectedIds.length === competitors.length;

  const toggleSelectAll = () => {
    if (allSelected) {
      onSelectionChange([]);
    } else {
      onSelectionChange(competitors.map((c) => c.id));
    }
  };

  const toggleSelect = (id: number) => {
    if (selectedIds.includes(id)) {
      onSelectionChange(selectedIds.filter((i) => i !== id));
    } else {
      onSelectionChange([...selectedIds, id]);
    }
  };

  if (competitors.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500 dark:text-gray-400">
          No competitors found. Add your first competitor to get started.
        </p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead className="bg-gray-50 dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700">
          <tr>
            <th className="px-4 py-3 text-left w-12">
              <button
                onClick={toggleSelectAll}
                className="text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200"
                aria-label={allSelected ? 'Deselect all' : 'Select all'}
              >
                {allSelected ? <CheckSquare size={18} /> : <Square size={18} />}
              </button>
            </th>
            <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900 dark:text-gray-100">
              Name
            </th>
            <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900 dark:text-gray-100">
              Website
            </th>
            <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900 dark:text-gray-100">
              Industry
            </th>
            <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900 dark:text-gray-100">
              Domains
            </th>
            <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900 dark:text-gray-100">
              Tracking
            </th>
            <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900 dark:text-gray-100">
              Added
            </th>
            <th className="px-4 py-3 text-right text-sm font-semibold text-gray-900 dark:text-gray-100">
              Actions
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
          {competitors.map((competitor) => (
            <tr
              key={competitor.id}
              className="hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors"
            >
              <td className="px-4 py-3">
                <button
                  onClick={() => toggleSelect(competitor.id)}
                  className="text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200"
                  aria-label={
                    selectedIds.includes(competitor.id) ? 'Deselect' : 'Select'
                  }
                >
                  {selectedIds.includes(competitor.id) ? (
                    <CheckSquare size={18} />
                  ) : (
                    <Square size={18} />
                  )}
                </button>
              </td>
              <td className="px-4 py-3">
                <div className="flex items-center gap-2">
                  <div>
                    <p className="font-medium text-gray-900 dark:text-gray-100">
                      {competitor.name}
                    </p>
                    {competitor.description && (
                      <p className="text-sm text-gray-500 dark:text-gray-400 truncate max-w-xs">
                        {competitor.description}
                      </p>
                    )}
                  </div>
                </div>
              </td>
              <td className="px-4 py-3">
                {competitor.website ? (
                  <a
                    href={competitor.website}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 text-primary-600 dark:text-primary-400 hover:underline text-sm"
                  >
                    <span className="truncate max-w-[200px]">{competitor.website}</span>
                    <ExternalLink size={14} />
                  </a>
                ) : (
                  <span className="text-gray-400 dark:text-gray-600 text-sm">-</span>
                )}
              </td>
              <td className="px-4 py-3">
                {competitor.industry ? (
                  <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300">
                    {competitor.industry}
                  </span>
                ) : (
                  <span className="text-gray-400 dark:text-gray-600 text-sm">-</span>
                )}
              </td>
              <td className="px-4 py-3">
                <span className="text-sm text-gray-700 dark:text-gray-300">
                  {competitor.domains?.length || 0}
                </span>
              </td>
              <td className="px-4 py-3">
                <span
                  className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                    competitor.tracking_enabled
                      ? 'bg-success-100 dark:bg-success-900/30 text-success-700 dark:text-success-300'
                      : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
                  }`}
                >
                  {competitor.tracking_enabled ? 'Enabled' : 'Disabled'}
                </span>
              </td>
              <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">
                {format(new Date(competitor.created_at), 'MMM d, yyyy')}
              </td>
              <td className="px-4 py-3">
                <div className="flex items-center justify-end gap-2">
                  <button
                    onClick={() => onEdit(competitor)}
                    className="p-1.5 text-gray-600 dark:text-gray-400 hover:text-primary-600 dark:hover:text-primary-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded transition-colors"
                    aria-label="Edit competitor"
                  >
                    <Edit2 size={16} />
                  </button>
                  <button
                    onClick={() => onDelete(competitor.id)}
                    className="p-1.5 text-gray-600 dark:text-gray-400 hover:text-danger-600 dark:hover:text-danger-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded transition-colors"
                    aria-label="Delete competitor"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
