/**
 * Phase 11: Analyst Review & Annotation Types
 * 
 * These types define NON-DESTRUCTIVE analyst annotations.
 * AI output remains IMMUTABLE - annotations are stored separately.
 */

export type ReviewStatus = 'unreviewed' | 'reviewed' | 'needs_followup'

export interface AnalystAnnotation {
  projectId: string
  timestamp: string
  reviewStatus: ReviewStatus
  notes: string
  flaggedRisks?: string[]
  approvedInsights?: boolean
}

export interface AnalystStore {
  [projectId: string]: AnalystAnnotation
}
