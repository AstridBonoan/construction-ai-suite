/**
 * Phase 12 Decision Support & Recommendation Engine Types
 * 
 * These types define the structure of decision support recommendations
 * derived from Phase 9 intelligence. All recommendations are advisory-only
 * and fully traceable to Phase 9 risk factors.
 */

/**
 * Traceability linking a recommendation back to Phase 9 intelligence
 */
export interface RecommendationTraceability {
  source_phase: 'phase9';
  risk_score: number;
  delay_probability: number;
  contributing_risks: string[];
  phase9_project_id: string;
}

/**
 * Individual recommendation action
 * 
 * Actions are defined from a fixed, construction-specific library:
 * - schedule_buffer_increase: Increase project schedule reserves
 * - subcontractor_review: Review and strengthen subcontractor agreements
 * - material_procurement_check: Prioritize material procurement planning
 * - site_inspection_priority: Schedule priority site inspections
 * - monitoring_only: Continue existing monitoring without intervention
 */
export type RecommendedAction =
  | 'schedule_buffer_increase'
  | 'subcontractor_review'
  | 'material_procurement_check'
  | 'site_inspection_priority'
  | 'monitoring_only';

/**
 * Confidence level assessment
 */
export type ConfidenceLevel = 'high' | 'medium' | 'low';

/**
 * Individual recommendation with full decision support context
 * 
 * Advisory-only: is_advisory is always true. These are decision support tools
 * for analyst review, not automated actions. Analysts decide to accept, defer,
 * or override each recommendation.
 */
export interface Recommendation {
  recommendation_id: string; // deterministic uuid5(project_id, action_type, index)
  recommended_action: RecommendedAction;
  confidence_level: ConfidenceLevel;
  supporting_risks: string[]; // risk factors triggering this recommendation
  tradeoffs: string[]; // potential downsides of this action
  no_action_risk: string; // risk if this recommendation is not followed
  is_advisory: true; // Always true - no execution capability
  justification: string; // Human-readable explanation
  traceability: RecommendationTraceability;
}

/**
 * Complete decision support output
 * 
 * Deterministic: same Phase 9 input always produces same output
 * Immutable: recommendations do not change based on analyst review
 * Explainable: every recommendation has full traceability and justification
 */
export interface DecisionOutput {
  schema_version: '1.0';
  project_id: string;
  generated_at: string; // ISO 8601 timestamp
  phase9_version: string; // version of Phase 9 that produced the input
  recommendations: Recommendation[];
  summary: {
    total_recommendations: number;
    high_confidence_count: number;
    medium_confidence_count: number;
    low_confidence_count: number;
    action_distribution: Record<RecommendedAction, number>;
  };
}

/**
 * Analyst acknowledgment of a recommendation (Phase 11 interaction)
 * 
 * Separate from the recommendation itself. Analyst feedback does NOT
 * change the recommendation or Phase 9 intelligence.
 */
export interface AnalystRecommendationAcknowledgment {
  recommendation_id: string;
  status: 'acknowledged' | 'deferred' | 'reviewing';
  analyst_notes: string;
  acknowledged_at: string;
}
