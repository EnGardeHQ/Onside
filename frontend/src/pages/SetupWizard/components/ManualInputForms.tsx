/**
 * Manual Input Forms Component
 * Manual entry of keywords and competitors
 */

import React, { useState } from 'react';
import { Plus, Trash2, TrendingUp, Users } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent, Button, Input } from '../../../components/common';
import { ManualKeywordEntry, ManualCompetitorEntry } from '../../../types';

interface ManualInputFormsProps {
  onSubmit: (keywords: string[], competitors: Array<{ domain: string; company_name?: string }>) => void;
  onBack: () => void;
  isLoading?: boolean;
}

export const ManualInputForms: React.FC<ManualInputFormsProps> = ({
  onSubmit,
  onBack,
  isLoading = false,
}) => {
  const [keywords, setKeywords] = useState<ManualKeywordEntry[]>([
    { id: crypto.randomUUID(), keyword: '' },
  ]);
  const [competitors, setCompetitors] = useState<ManualCompetitorEntry[]>([
    { id: crypto.randomUUID(), domain: '', company_name: '' },
  ]);

  const [errors, setErrors] = useState<{
    keywords: Record<string, string>;
    competitors: Record<string, string>;
  }>({
    keywords: {},
    competitors: {},
  });

  // Keyword handlers
  const addKeyword = () => {
    setKeywords([...keywords, { id: crypto.randomUUID(), keyword: '' }]);
  };

  const removeKeyword = (id: string) => {
    if (keywords.length > 1) {
      setKeywords(keywords.filter((k) => k.id !== id));
      const newErrors = { ...errors.keywords };
      delete newErrors[id];
      setErrors({ ...errors, keywords: newErrors });
    }
  };

  const updateKeyword = (id: string, value: string) => {
    setKeywords(keywords.map((k) => (k.id === id ? { ...k, keyword: value } : k)));
    // Clear error when user types
    if (errors.keywords[id]) {
      const newErrors = { ...errors.keywords };
      delete newErrors[id];
      setErrors({ ...errors, keywords: newErrors });
    }
  };

  // Competitor handlers
  const addCompetitor = () => {
    setCompetitors([...competitors, { id: crypto.randomUUID(), domain: '', company_name: '' }]);
  };

  const removeCompetitor = (id: string) => {
    if (competitors.length > 1) {
      setCompetitors(competitors.filter((c) => c.id !== id));
      const newErrors = { ...errors.competitors };
      delete newErrors[id];
      setErrors({ ...errors, competitors: newErrors });
    }
  };

  const updateCompetitor = (
    id: string,
    field: 'domain' | 'company_name',
    value: string
  ) => {
    setCompetitors(
      competitors.map((c) => (c.id === id ? { ...c, [field]: value } : c))
    );
    // Clear error when user types in domain field
    if (field === 'domain' && errors.competitors[id]) {
      const newErrors = { ...errors.competitors };
      delete newErrors[id];
      setErrors({ ...errors, competitors: newErrors });
    }
  };

  // Validation
  const validate = (): boolean => {
    const newErrors: {
      keywords: Record<string, string>;
      competitors: Record<string, string>;
    } = {
      keywords: {},
      competitors: {},
    };

    let isValid = true;

    // Validate keywords
    const filledKeywords = keywords.filter((k) => k.keyword.trim() !== '');
    if (filledKeywords.length === 0) {
      newErrors.keywords[keywords[0].id] = 'At least one keyword is required';
      isValid = false;
    }

    // Check for duplicate keywords
    const keywordSet = new Set<string>();
    keywords.forEach((k) => {
      if (k.keyword.trim()) {
        const normalized = k.keyword.toLowerCase().trim();
        if (keywordSet.has(normalized)) {
          newErrors.keywords[k.id] = 'Duplicate keyword';
          isValid = false;
        }
        keywordSet.add(normalized);
      }
    });

    // Validate competitors
    const filledCompetitors = competitors.filter((c) => c.domain.trim() !== '');
    if (filledCompetitors.length === 0) {
      newErrors.competitors[competitors[0].id] = 'At least one competitor domain is required';
      isValid = false;
    }

    // Validate competitor domains
    const urlPattern = /^([a-z0-9]+(-[a-z0-9]+)*\.)+[a-z]{2,}$/i;
    competitors.forEach((c) => {
      if (c.domain.trim() && !urlPattern.test(c.domain.trim())) {
        newErrors.competitors[c.id] = 'Invalid domain format (e.g., example.com)';
        isValid = false;
      }
    });

    // Check for duplicate competitors
    const competitorSet = new Set<string>();
    competitors.forEach((c) => {
      if (c.domain.trim()) {
        const normalized = c.domain.toLowerCase().trim();
        if (competitorSet.has(normalized)) {
          newErrors.competitors[c.id] = 'Duplicate competitor';
          isValid = false;
        }
        competitorSet.add(normalized);
      }
    });

    setErrors(newErrors);
    return isValid;
  };

  const handleSubmit = () => {
    if (!validate()) {
      return;
    }

    const validKeywords = keywords
      .map((k) => k.keyword.trim())
      .filter(Boolean);

    const validCompetitors = competitors
      .filter((c) => c.domain.trim())
      .map((c) => ({
        domain: c.domain.trim(),
        company_name: c.company_name?.trim() || undefined,
      }));

    onSubmit(validKeywords, validCompetitors);
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <Card className="p-6">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
          Manual Entry
        </h2>
        <p className="text-gray-600 dark:text-gray-400 mt-2">
          Add your target keywords and competitors manually
        </p>
      </Card>

      {/* Keywords Section */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <TrendingUp className="text-primary-500" size={24} />
              <CardTitle>Target Keywords</CardTitle>
            </div>
            <Button
              size="sm"
              variant="secondary"
              onClick={addKeyword}
              icon={<Plus size={16} />}
            >
              Add Keyword
            </Button>
          </div>
        </CardHeader>

        <CardContent>
          <div className="space-y-3">
            {keywords.map((keyword, index) => (
              <div key={keyword.id} className="flex gap-2 items-start">
                <div className="flex-shrink-0 w-8 pt-2 text-sm text-gray-500 dark:text-gray-400 text-center">
                  {index + 1}
                </div>
                <div className="flex-1">
                  <Input
                    value={keyword.keyword}
                    onChange={(e) => updateKeyword(keyword.id, e.target.value)}
                    placeholder="Enter keyword (e.g., project management software)"
                    error={errors.keywords[keyword.id]}
                  />
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => removeKeyword(keyword.id)}
                  disabled={keywords.length === 1}
                  className="flex-shrink-0 mt-0.5"
                  icon={<Trash2 size={16} />}
                />
              </div>
            ))}
          </div>

          <p className="text-sm text-gray-500 dark:text-gray-400 mt-4">
            Add keywords that are relevant to your business and products/services
          </p>
        </CardContent>
      </Card>

      {/* Competitors Section */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Users className="text-primary-500" size={24} />
              <CardTitle>Competitors</CardTitle>
            </div>
            <Button
              size="sm"
              variant="secondary"
              onClick={addCompetitor}
              icon={<Plus size={16} />}
            >
              Add Competitor
            </Button>
          </div>
        </CardHeader>

        <CardContent>
          <div className="space-y-3">
            {competitors.map((competitor, index) => (
              <div key={competitor.id} className="flex gap-2 items-start">
                <div className="flex-shrink-0 w-8 pt-2 text-sm text-gray-500 dark:text-gray-400 text-center">
                  {index + 1}
                </div>
                <div className="flex-1 grid grid-cols-1 md:grid-cols-2 gap-2">
                  <Input
                    value={competitor.domain}
                    onChange={(e) => updateCompetitor(competitor.id, 'domain', e.target.value)}
                    placeholder="competitor.com"
                    error={errors.competitors[competitor.id]}
                  />
                  <Input
                    value={competitor.company_name || ''}
                    onChange={(e) =>
                      updateCompetitor(competitor.id, 'company_name', e.target.value)
                    }
                    placeholder="Company Name (optional)"
                  />
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => removeCompetitor(competitor.id)}
                  disabled={competitors.length === 1}
                  className="flex-shrink-0 mt-0.5"
                  icon={<Trash2 size={16} />}
                />
              </div>
            ))}
          </div>

          <p className="text-sm text-gray-500 dark:text-gray-400 mt-4">
            Add competitor domains (e.g., competitor.com) and optionally their company names
          </p>
        </CardContent>
      </Card>

      {/* Action Buttons */}
      <div className="flex gap-3">
        <Button variant="secondary" onClick={onBack} disabled={isLoading}>
          Back
        </Button>
        <Button
          variant="primary"
          onClick={handleSubmit}
          isLoading={isLoading}
          fullWidth
        >
          Import Keywords & Competitors
        </Button>
      </div>
    </div>
  );
};
