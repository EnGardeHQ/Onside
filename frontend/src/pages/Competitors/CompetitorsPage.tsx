/**
 * Competitors Page
 * Main competitor management interface
 */

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Plus, Search, Download, Upload, Trash2 } from 'lucide-react';
import { competitorApi } from '../../api';
import { Competitor, CompetitorFilters } from '../../types';
import { Button, Card, Input } from '../../components/common';
import { CompetitorList } from './CompetitorList';
import { CompetitorModal } from './CompetitorModal';
import { CompetitorComparison } from './CompetitorComparison';
import { LoadingSpinner } from '../../components/common/Loading';

export const CompetitorsPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [filters, setFilters] = useState<CompetitorFilters>({});
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCompetitors, setSelectedCompetitors] = useState<number[]>([]);
  const [showModal, setShowModal] = useState(false);
  const [showComparison, setShowComparison] = useState(false);
  const [editingCompetitor, setEditingCompetitor] = useState<Competitor | undefined>();

  // Fetch competitors
  const { data: competitorsData, isLoading } = useQuery({
    queryKey: ['competitors', filters],
    queryFn: () => competitorApi.list(filters),
  });

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: (id: number) => competitorApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['competitors'] });
    },
  });

  // Bulk delete mutation
  const bulkDeleteMutation = useMutation({
    mutationFn: (ids: number[]) => competitorApi.bulkDelete(ids),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['competitors'] });
      setSelectedCompetitors([]);
    },
  });

  // Export mutation
  const exportMutation = useMutation({
    mutationFn: (format: 'csv' | 'json') => competitorApi.export(format, filters),
    onSuccess: (blob, format) => {
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `competitors-${new Date().toISOString()}.${format}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    },
  });

  const handleSearch = (value: string) => {
    setSearchTerm(value);
    setFilters((prev) => ({ ...prev, search: value || undefined }));
  };

  const handleCreate = () => {
    setEditingCompetitor(undefined);
    setShowModal(true);
  };

  const handleEdit = (competitor: Competitor) => {
    setEditingCompetitor(competitor);
    setShowModal(true);
  };

  const handleDelete = async (id: number) => {
    if (window.confirm('Are you sure you want to delete this competitor?')) {
      await deleteMutation.mutateAsync(id);
    }
  };

  const handleBulkDelete = async () => {
    if (
      selectedCompetitors.length > 0 &&
      window.confirm(`Delete ${selectedCompetitors.length} competitor(s)?`)
    ) {
      await bulkDeleteMutation.mutateAsync(selectedCompetitors);
    }
  };

  const handleCompare = () => {
    if (selectedCompetitors.length >= 2) {
      setShowComparison(true);
    }
  };

  const handleImport = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      try {
        const result = await competitorApi.import(file);
        alert(`Imported ${result.imported} competitor(s)`);
        if (result.errors.length > 0) {
          console.error('Import errors:', result.errors);
        }
        queryClient.invalidateQueries({ queryKey: ['competitors'] });
      } catch (error: any) {
        alert(`Import failed: ${error.message}`);
      }
    }
  };

  const competitors = competitorsData?.competitors || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
            Competitor Management
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Track and analyze your competitors
          </p>
        </div>
        <Button variant="primary" icon={<Plus size={18} />} onClick={handleCreate}>
          Add Competitor
        </Button>
      </div>

      {/* Filters and Actions */}
      <Card>
        <div className="flex flex-col lg:flex-row gap-4">
          <div className="flex-1">
            <Input
              placeholder="Search competitors..."
              value={searchTerm}
              onChange={(e) => handleSearch(e.target.value)}
              leftIcon={<Search size={18} />}
            />
          </div>
          <div className="flex flex-wrap gap-2">
            <Button
              variant="secondary"
              size="sm"
              icon={<Download size={16} />}
              onClick={() => exportMutation.mutate('csv')}
              isLoading={exportMutation.isPending}
            >
              Export CSV
            </Button>
            <Button
              variant="secondary"
              size="sm"
              icon={<Download size={16} />}
              onClick={() => exportMutation.mutate('json')}
              isLoading={exportMutation.isPending}
            >
              Export JSON
            </Button>
            <label className="inline-flex cursor-pointer">
              <input
                type="file"
                accept=".csv,.json"
                className="hidden"
                onChange={handleImport}
              />
              <span className="inline-flex items-center justify-center px-3 py-1.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 dark:bg-gray-800 dark:text-gray-200 dark:border-gray-600 dark:hover:bg-gray-700">
                <Upload size={16} className="mr-1.5" />
                Import
              </span>
            </label>
            {selectedCompetitors.length >= 2 && (
              <Button variant="primary" size="sm" onClick={handleCompare}>
                Compare ({selectedCompetitors.length})
              </Button>
            )}
            {selectedCompetitors.length > 0 && (
              <Button
                variant="danger"
                size="sm"
                icon={<Trash2 size={16} />}
                onClick={handleBulkDelete}
                isLoading={bulkDeleteMutation.isPending}
              >
                Delete ({selectedCompetitors.length})
              </Button>
            )}
          </div>
        </div>
      </Card>

      {/* Competitor List */}
      <Card padding="none">
        {isLoading ? (
          <div className="flex items-center justify-center p-12">
            <LoadingSpinner size="lg" />
          </div>
        ) : (
          <CompetitorList
            competitors={competitors}
            selectedIds={selectedCompetitors}
            onSelectionChange={setSelectedCompetitors}
            onEdit={handleEdit}
            onDelete={handleDelete}
          />
        )}
      </Card>

      {/* Create/Edit Modal */}
      {showModal && (
        <CompetitorModal
          competitor={editingCompetitor}
          onClose={() => setShowModal(false)}
          onSuccess={() => {
            setShowModal(false);
            queryClient.invalidateQueries({ queryKey: ['competitors'] });
          }}
        />
      )}

      {/* Comparison Modal */}
      {showComparison && (
        <CompetitorComparison
          competitorIds={selectedCompetitors}
          onClose={() => setShowComparison(false)}
        />
      )}
    </div>
  );
};
