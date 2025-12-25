/**
 * En Garde Types
 * Type definitions for En Garde brand analysis and setup wizard
 */

export interface BrandQuestionnaireData {
  brand_name: string;
  primary_website: string;
  industry: string;
  target_markets: string[];
  products_services: string[];
  known_competitors?: string[];
  target_keywords?: string[];
}

export interface BrandAnalysisRequest {
  questionnaire_data: BrandQuestionnaireData;
}

export interface BrandAnalysisInitResponse {
  analysis_id: string;
  status: 'pending' | 'crawling' | 'analyzing' | 'processing' | 'completed' | 'failed';
  message: string;
}

export interface AnalysisStatus {
  analysis_id: string;
  status: 'pending' | 'crawling' | 'analyzing' | 'processing' | 'completed' | 'failed';
  progress_percentage: number;
  current_step?: string;
  estimated_time_remaining?: number;
  error_message?: string;
}

export interface DiscoveredKeyword {
  keyword: string;
  source: 'website' | 'competitor' | 'industry' | 'inferred';
  relevance_score: number;
  search_volume?: number;
  is_selected?: boolean;
}

export interface DiscoveredCompetitor {
  domain: string;
  company_name?: string;
  category: 'direct' | 'indirect' | 'potential';
  relevance_score: number;
  is_selected?: boolean;
}

export interface BrandAnalysisResults {
  analysis_id: string;
  brand_name: string;
  discovered_keywords: DiscoveredKeyword[];
  discovered_competitors: DiscoveredCompetitor[];
  brand_summary?: {
    industry_classification?: string;
    primary_value_proposition?: string;
    target_audience?: string;
  };
}

export interface ConfirmAnalysisRequest {
  selected_keywords: string[];
  selected_competitors: string[];
  custom_keywords?: string[];
  custom_competitors?: Array<{
    domain: string;
    company_name?: string;
  }>;
}

export interface ConfirmAnalysisResponse {
  message: string;
  keywords_imported: number;
  competitors_imported: number;
}

export interface ManualKeywordEntry {
  id: string;
  keyword: string;
}

export interface ManualCompetitorEntry {
  id: string;
  domain: string;
  company_name?: string;
}

export type SetupWizardStep = 'path-selection' | 'questionnaire' | 'manual-input' | 'progress' | 'results';

export interface SetupWizardState {
  currentStep: SetupWizardStep;
  selectedPath: 'automated' | 'manual' | null;
  questionnaireData?: BrandQuestionnaireData;
  analysisId?: string;
  analysisResults?: BrandAnalysisResults;
  manualKeywords?: ManualKeywordEntry[];
  manualCompetitors?: ManualCompetitorEntry[];
}
