/**
 * Phase 12: Decision Support & Recommendation Engine
 * 
 * Types for deterministic, traceable, non-destructive decision guidance.
 * All recommendations are derived from Phase 9 intelligence only.
 */

// Construction-specific allowed actions (enum-like)
export type RecommendedAction =
  | 'schedule_buffer_increase'
  | 'subcontractor_review'
  | 'material_procurement_check'
  | 'site_inspection_priority'
  | 'monitoring_only'

export type ConfidenceLevel = 'high' | 'medium' | 'low'

export interface RecommendationTraceability {
  source_phase: 'phase9'
  risk_score: number
  delay_probability: number
  linked_risk_factors: string[]
  confidence_score?: number
}

export interface Recommendation {
  recommendation_id: string
  project_id: string
  recommended_action: RecommendedAction
  confidence_level: ConfidenceLevel
  supporting_risks: string[]
  tradeoffs: string
  no_action_risk: string
  rationale: string
  traceability: RecommendationTraceability
  timestamp: string
  is_advisory: true // Always true - cannot be executed
}

export interface DecisionOutput {
  schema_version: 'phase12-v1'
  project_id: string
  source_phase: 'phase9'
  recommendations: Recommendation[]
  summary: string
  analyst_context?: string
  generated_at: string
  deterministic_seed?: string
}
