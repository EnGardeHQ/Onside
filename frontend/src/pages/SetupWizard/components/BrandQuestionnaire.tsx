/**
 * Brand Questionnaire Component
 * Form for automated brand analysis path
 */

import React from 'react';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Globe, Building2, Target, Package, Users, TrendingUp } from 'lucide-react';
import { Button, Input, Card } from '../../../components/common';
import { BrandQuestionnaireData } from '../../../types';

const questionnaireSchema = z.object({
  brand_name: z.string().min(1, 'Brand name is required'),
  primary_website: z.string().url('Must be a valid URL').min(1, 'Website is required'),
  industry: z.string().min(1, 'Industry is required'),
  target_markets: z.string().min(1, 'At least one target market is required'),
  products_services: z.string().min(1, 'At least one product/service is required'),
  known_competitors: z.string().optional(),
  target_keywords: z.string().optional(),
});

type FormData = z.infer<typeof questionnaireSchema>;

interface BrandQuestionnaireProps {
  onSubmit: (data: BrandQuestionnaireData) => void;
  onBack: () => void;
  initialData?: BrandQuestionnaireData;
  isLoading?: boolean;
}

export const BrandQuestionnaire: React.FC<BrandQuestionnaireProps> = ({
  onSubmit,
  onBack,
  initialData,
  isLoading = false,
}) => {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormData>({
    resolver: zodResolver(questionnaireSchema),
    defaultValues: initialData
      ? {
          brand_name: initialData.brand_name,
          primary_website: initialData.primary_website,
          industry: initialData.industry,
          target_markets: initialData.target_markets.join(', '),
          products_services: initialData.products_services.join(', '),
          known_competitors: initialData.known_competitors?.join(', ') || '',
          target_keywords: initialData.target_keywords?.join(', ') || '',
        }
      : undefined,
  });

  const handleFormSubmit = (data: FormData) => {
    const formattedData: BrandQuestionnaireData = {
      brand_name: data.brand_name,
      primary_website: data.primary_website,
      industry: data.industry,
      target_markets: data.target_markets.split(',').map((s) => s.trim()).filter(Boolean),
      products_services: data.products_services.split(',').map((s) => s.trim()).filter(Boolean),
      known_competitors: data.known_competitors
        ? data.known_competitors.split(',').map((s) => s.trim()).filter(Boolean)
        : undefined,
      target_keywords: data.target_keywords
        ? data.target_keywords.split(',').map((s) => s.trim()).filter(Boolean)
        : undefined,
    };
    onSubmit(formattedData);
  };

  return (
    <div className="max-w-3xl mx-auto">
      <Card className="p-8">
        <div className="mb-6">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
            Tell us about your brand
          </h2>
          <p className="text-gray-600 dark:text-gray-400 mt-2">
            Help us understand your brand so we can provide better competitor and keyword recommendations
          </p>
        </div>

        <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-6">
          {/* Brand Name */}
          <Input
            {...register('brand_name')}
            label="Brand Name"
            placeholder="Enter your brand or company name"
            error={errors.brand_name?.message}
            leftIcon={<Building2 size={18} />}
            required
          />

          {/* Primary Website */}
          <Input
            {...register('primary_website')}
            label="Primary Website"
            type="url"
            placeholder="https://example.com"
            error={errors.primary_website?.message}
            leftIcon={<Globe size={18} />}
            helperText="Your main website URL"
            required
          />

          {/* Industry */}
          <Input
            {...register('industry')}
            label="Industry"
            placeholder="e.g., E-commerce, SaaS, Healthcare, etc."
            error={errors.industry?.message}
            leftIcon={<Target size={18} />}
            required
          />

          {/* Target Markets */}
          <div>
            <Input
              {...register('target_markets')}
              label="Target Markets"
              placeholder="e.g., North America, Europe, Global"
              error={errors.target_markets?.message}
              leftIcon={<Users size={18} />}
              helperText="Separate multiple markets with commas"
              required
            />
          </div>

          {/* Products/Services */}
          <div>
            <Input
              {...register('products_services')}
              label="Products/Services"
              placeholder="e.g., CRM Software, Marketing Automation, Analytics"
              error={errors.products_services?.message}
              leftIcon={<Package size={18} />}
              helperText="Separate multiple items with commas"
              required
            />
          </div>

          {/* Known Competitors (Optional) */}
          <div>
            <Input
              {...register('known_competitors')}
              label="Known Competitors (Optional)"
              placeholder="e.g., competitor1.com, competitor2.com"
              error={errors.known_competitors?.message}
              leftIcon={<Users size={18} />}
              helperText="Competitor domains separated by commas (we'll discover more for you)"
            />
          </div>

          {/* Target Keywords (Optional) */}
          <div>
            <Input
              {...register('target_keywords')}
              label="Target Keywords (Optional)"
              placeholder="e.g., project management, task tracking, team collaboration"
              error={errors.target_keywords?.message}
              leftIcon={<TrendingUp size={18} />}
              helperText="Keywords separated by commas (we'll discover more for you)"
            />
          </div>

          {/* Action Buttons */}
          <div className="flex gap-3 pt-4">
            <Button
              type="button"
              variant="secondary"
              onClick={onBack}
              disabled={isLoading}
            >
              Back
            </Button>
            <Button
              type="submit"
              variant="primary"
              isLoading={isLoading}
              fullWidth
            >
              Analyze My Brand
            </Button>
          </div>
        </form>
      </Card>
    </div>
  );
};
