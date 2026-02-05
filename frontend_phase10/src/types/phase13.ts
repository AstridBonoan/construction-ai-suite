/**
 * Phase 13 Feedback Schema (Frozen v1.0)
 *
 * Strict, immutable schema for capturing analyst decisions on Phase 12 recommendations.
 * This schema is versioned and MUST NOT CHANGE without major version bump.
 *
 * Philosophy: Evidence collection for future improvement (no learning, no inference yet)
 */

/**
 * Analyst action on a recommendation
 * - accepted: Analyst agrees with recommendation and plans to implement
 * - rejected: Analyst disagrees and will not implement
 * - modified: Analyst accepts recommendation but modifies the implementation
 */
export type AnalystAction = 'accepted' | 'rejected' | 'modified';

/**
 * Structured reason codes for feedback decisions
 * Controlled vocabulary to avoid free-text chaos and enable aggregation
 */
export type ReasonCode =
  // Acceptance reasons
  | 'aligns_with_plan'
  | 'risk_justifies_action'
  | 'timing_optimal'
  | 'budget_available'
  | 'team_capacity'
  | 'stakeholder_agreement'
  // Rejection reasons
  | 'already_planned'
  | 'budget_insufficient'
  | 'timing_inappropriate'
  | 'team_unavailable'
  | 'stakeholder_disagreement'
  | 'risk_acceptable'
  | 'conflicting_priority'
  | 'insufficient_confidence'
  | 'alternative_approach'
  // Modification reasons
  | 'scope_reduction'
  | 'implementation_change'
  | 'timeline_adjustment'
  | 'budget_constraint'
  | 'resource_allocation'
  | 'stakeholder_feedback'
  | 'additional_validation_needed';

/**
 * Feedback from analyst on a Phase 12 recommendation
 *
 * Immutable once written. Links recommendation back to project context,
 * analyst decision, and structured reasoning.
 *
 * This is the foundation for future feedback aggregation and (much later)
 * potential retraining - but Phase 13 is ONLY capture and audit, no learning.
 */
export interface FeedbackRecord {
  // Schema versioning (immutable)
  schema_version: '1.0';
  
  // Correlation to Phase 12 & Phase 9
  recommendation_id: string;  // From Phase 12
  project_id: string;         // From Phase 12 → Phase 9
  
  // Analyst decision (required)
  analyst_action: AnalystAction;
  
  // Structured reasoning (required for non-accepted)
  reason_codes: ReasonCode[];  // Multi-select allowed
  
  // Optional structured modification details
  modification_summary?: string;  // "Reduced scope to 8 weeks instead of 12"
  modification_confidence?: 'high' | 'medium' | 'low';
  
  // Analyst identity (hashed or pseudonymous)
  analyst_id: string;  // Could be hash, pseudonym, or anonymized
  
  // Temporal context (ISO 8601)
  decided_at: string;  // When analyst made this decision
  
  // Optional: Why changed mind from initial review
  initial_action?: AnalystAction;  // What analyst first thought
  decision_time_seconds?: number;  // How long to decide
  
  // Audit trail
  recorded_at: string;  // When feedback was stored (server timestamp)
  
  // Optional context (never changes recommendations, only for audit)
  notes?: string;  // Free-text analyst notes (audit only, not used for learning)
  
  // Governance
  is_final: boolean;  // Once true, record is immutable
}

/**
 * Feedback storage contract
 * Used internally by backend to validate and store feedback
 */
export interface FeedbackStorageContract {
  // Immutability guarantee
  readonly schema_version: '1.0';
  
  // Validation contract
  readonly required_fields: (keyof FeedbackRecord)[];
  readonly enum_constraints: {
    analyst_action: AnalystAction[];
    reason_codes: ReasonCode[];
    modification_confidence?: ('high' | 'medium' | 'low')[];
  };
  
  // Storage constraint
  readonly append_only: true;
  readonly immutable_after_write: true;
  readonly correlations: {
    to_phase12: 'recommendation_id';
    to_phase9: 'project_id';
  };
}

/**
 * Analytics aggregates (computed from feedback, read-only)
 * These are computed from feedback records but NEVER modify recommendations
 */
export interface FeedbackAnalytics {
  // Time range for this analysis
  period_start: string;
  period_end: string;
  
  // Overall metrics
  total_feedback_records: number;
  
  // Acceptance rate by recommendation action type
  acceptance_rate: {
    schedule_buffer_increase: number;      // 0.0-1.0
    subcontractor_review: number;
    material_procurement_check: number;
    site_inspection_priority: number;
    monitoring_only: number;
  };
  
  // Why analysts reject recommendations
  rejection_reasons: {
    reason_code: ReasonCode;
    count: number;
    percentage: number;
  }[];
  
  // Analyst override patterns
  override_patterns: {
    action_type: string;
    modification_frequency: number;
    common_modifications: string[];
  }[];
  
  // Decision speed
  time_to_decision_metrics: {
    median_seconds: number;
    p95_seconds: number;
    p99_seconds: number;
  };
  
  // Analyst consistency
  analyst_agreement: {
    analyst_id: string;
    decision_consistency: number;  // 0.0-1.0
  }[];
}

/**
 * Feedback query contract (read-only analytics)
 * Used to safely query feedback without modification
 */
export interface FeedbackQueryContract {
  readonly read_only: true;
  readonly no_mutations: true;
  readonly no_inference: true;
  
  // Safe queries
  get_feedback_by_recommendation(recommendation_id: string): FeedbackRecord | null;
  get_feedback_by_project(project_id: string): FeedbackRecord[];
  get_analytics(period_start: string, period_end: string): FeedbackAnalytics;
}
