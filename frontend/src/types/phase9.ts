export interface PrimaryRiskFactor {
  factor: string
  contribution: number
}

export interface Phase9Output {
  schema_version: string
  project_id: string
  project_name?: string | null
  risk_score: number
  risk_level: string
  predicted_delay_days?: number | null
  delay_probability: number
  confidence_score?: number
  primary_risk_factors: PrimaryRiskFactor[]
  recommended_actions: string[]
  explanation: string
  model_version: string
  generated_at: string
}
