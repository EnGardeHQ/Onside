/**
 * Competitor Modal Component
 * Form for creating and editing competitors
 */

import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useMutation } from '@tanstack/react-query';
import { X, Plus, Trash2 } from 'lucide-react';
import { competitorApi } from '../../api';
import { Competitor, Domain } from '../../types';
import { Button, Input } from '../../components/common';

const competitorSchema = z.object({
  name: z.string().min(1, 'Name is required'),
  website: z.string().url('Invalid URL').optional().or(z.literal('')),
  description: z.string().optional(),
  industry: z.string().optional(),
  size: z.string().optional(),
  location: z.string().optional(),
  tracking_enabled: z.boolean().default(true),
});

type CompetitorFormData = z.infer<typeof competitorSchema>;

interface CompetitorModalProps {
  competitor?: Competitor;
  onClose: () => void;
  onSuccess: () => void;
}

export const CompetitorModal: React.FC<CompetitorModalProps> = ({
  competitor,
  onClose,
  onSuccess,
}) => {
  const isEditing = !!competitor;
  const [domains, setDomains] = useState<Domain[]>(competitor?.domains || []);
  const [newDomain, setNewDomain] = useState('');

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<CompetitorFormData>({
    resolver: zodResolver(competitorSchema),
    defaultValues: competitor || { tracking_enabled: true },
  });

  const createMutation = useMutation({
    mutationFn: (data: CompetitorFormData) => competitorApi.create(data),
    onSuccess: () => {
      onSuccess();
    },
  });

  const updateMutation = useMutation({
    mutationFn: (data: CompetitorFormData) =>
      competitorApi.update(competitor!.id, data),
    onSuccess: () => {
      onSuccess();
    },
  });

  const addDomainMutation = useMutation({
    mutationFn: (domain: string) =>
      competitorApi.addDomain(competitor!.id, domain, domains.length === 0),
  });

  const removeDomainMutation = useMutation({
    mutationFn: (domainId: number) =>
      competitorApi.removeDomain(competitor!.id, domainId),
  });

  const onSubmit = async (data: CompetitorFormData) => {
    if (isEditing) {
      await updateMutation.mutateAsync(data);
    } else {
      await createMutation.mutateAsync(data);
    }
  };

  const handleAddDomain = async () => {
    if (!newDomain.trim() || !isEditing) return;

    try {
      const domain = await addDomainMutation.mutateAsync(newDomain.trim());
      setDomains([...domains, domain]);
      setNewDomain('');
    } catch (error) {
      console.error('Failed to add domain:', error);
    }
  };

  const handleRemoveDomain = async (domainId: number) => {
    if (!isEditing) return;

    try {
      await removeDomainMutation.mutateAsync(domainId);
      setDomains(domains.filter((d) => d.id !== domainId));
    } catch (error) {
      console.error('Failed to remove domain:', error);
    }
  };

  const isLoading = createMutation.isPending || updateMutation.isPending;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
            {isEditing ? 'Edit Competitor' : 'Add Competitor'}
          </h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
            aria-label="Close modal"
          >
            <X size={20} />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit(onSubmit)} className="p-6 space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Input
              label="Name"
              placeholder="Company name"
              required
              error={errors.name?.message}
              {...register('name')}
            />

            <Input
              label="Website"
              type="url"
              placeholder="https://example.com"
              error={errors.website?.message}
              {...register('website')}
            />
          </div>

          <Input
            label="Description"
            placeholder="Brief description of the competitor"
            error={errors.description?.message}
            {...register('description')}
          />

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Input
              label="Industry"
              placeholder="e.g., Technology"
              error={errors.industry?.message}
              {...register('industry')}
            />

            <Input
              label="Company Size"
              placeholder="e.g., 100-500"
              error={errors.size?.message}
              {...register('size')}
            />

            <Input
              label="Location"
              placeholder="e.g., San Francisco"
              error={errors.location?.message}
              {...register('location')}
            />
          </div>

          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="tracking_enabled"
              className="w-4 h-4 text-primary-600 rounded focus:ring-primary-500"
              {...register('tracking_enabled')}
            />
            <label
              htmlFor="tracking_enabled"
              className="text-sm font-medium text-gray-700 dark:text-gray-300"
            >
              Enable tracking for this competitor
            </label>
          </div>

          {/* Domains Section (only for editing) */}
          {isEditing && (
            <div className="space-y-3">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                Domains
              </h3>

              {domains.length > 0 && (
                <div className="space-y-2">
                  {domains.map((domain) => (
                    <div
                      key={domain.id}
                      className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-900 rounded-lg"
                    >
                      <div>
                        <span className="text-sm font-medium text-gray-900 dark:text-gray-100">
                          {domain.domain}
                        </span>
                        {domain.is_primary && (
                          <span className="ml-2 text-xs px-2 py-0.5 bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300 rounded">
                            Primary
                          </span>
                        )}
                      </div>
                      <button
                        type="button"
                        onClick={() => handleRemoveDomain(domain.id)}
                        className="p-1.5 text-danger-600 dark:text-danger-400 hover:bg-danger-50 dark:hover:bg-danger-900/20 rounded transition-colors"
                        disabled={removeDomainMutation.isPending}
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                  ))}
                </div>
              )}

              <div className="flex gap-2">
                <Input
                  placeholder="Add domain (e.g., example.com)"
                  value={newDomain}
                  onChange={(e) => setNewDomain(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      e.preventDefault();
                      handleAddDomain();
                    }
                  }}
                />
                <Button
                  type="button"
                  variant="secondary"
                  icon={<Plus size={18} />}
                  onClick={handleAddDomain}
                  isLoading={addDomainMutation.isPending}
                >
                  Add
                </Button>
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="flex gap-3 pt-4 border-t border-gray-200 dark:border-gray-700">
            <Button type="button" variant="secondary" onClick={onClose} fullWidth>
              Cancel
            </Button>
            <Button type="submit" variant="primary" isLoading={isLoading} fullWidth>
              {isEditing ? 'Update' : 'Create'} Competitor
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};
