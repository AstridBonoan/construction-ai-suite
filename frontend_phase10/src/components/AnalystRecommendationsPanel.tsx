/**
 * Phase 12 Analyst Recommendations Panel
 * 
 * Displays decision support recommendations alongside Phase 11 analyst review.
 * Recommendations are advisory-only and fully traceable to Phase 9 intelligence.
 * Analysts can acknowledge, defer, or add notes without affecting the recommendations.
 */

import React, { useState, useEffect } from 'react';
import './AnalystRecommendationsPanel.css';
import type {
  DecisionOutput,
  Recommendation,
  AnalystRecommendationAcknowledgment,
} from '../types/phase12';

interface AnalystRecommendationsPanelProps {
  projectId: string;
  phase9Data?: any;
}

/**
 * Hook to manage analyst acknowledgments of recommendations
 * Stored separately from recommendations - analyst actions don't modify them
 */
function useRecommendationAcknowledgments(projectId: string) {
  const [acknowledgments, setAcknowledgments] = useState<
    Map<string, AnalystRecommendationAcknowledgment>
  >(new Map());

  useEffect(() => {
    const key = `recommendations_acknowledged_${projectId}`;
    const stored = localStorage.getItem(key);
    if (stored) {
      try {
        const parsed = JSON.parse(stored);
        setAcknowledgments(new Map(Object.entries(parsed)));
      } catch (e) {
        console.warn('Failed to parse stored acknowledgments', e);
      }
    }
  }, [projectId]);

  const updateAcknowledgment = (
    recommendationId: string,
    update: Partial<AnalystRecommendationAcknowledgment>
  ) => {
    setAcknowledgments((prev) => {
      const updated = new Map(prev);
      const existing = updated.get(recommendationId) || {
        recommendation_id: recommendationId,
        status: 'reviewing',
        analyst_notes: '',
        acknowledged_at: new Date().toISOString(),
      };
      updated.set(recommendationId, { ...existing, ...update });

      // Persist to localStorage
      const key = `recommendations_acknowledged_${projectId}`;
      const obj = Object.fromEntries(updated);
      localStorage.setItem(key, JSON.stringify(obj));

      return updated;
    });
  };

  return { acknowledgments, updateAcknowledgment };
}

/**
 * Individual recommendation card component
 */
function RecommendationCard({
  recommendation,
  acknowledgment,
  onAcknowledge,
}: {
  recommendation: Recommendation;
  acknowledgment?: AnalystRecommendationAcknowledgment;
  onAcknowledge: (status: 'acknowledged' | 'deferred') => void;
}) {
  const [showDetails, setShowDetails] = useState(false);

  const confidenceColor = {
    high: '#10b981',
    medium: '#f59e0b',
    low: '#ef4444',
  };

  return (
    <div className="recommendation-card">
      <div className="recommendation-header">
        <div className="recommendation-action">
          <span
            className="confidence-badge"
            style={{ backgroundColor: confidenceColor[recommendation.confidence_level] }}
          >
            {recommendation.confidence_level.toUpperCase()}
          </span>
          <span className="action-label">{recommendation.recommended_action}</span>
        </div>

        <div className="recommendation-status">
          <span className="advisory-badge">ADVISORY ONLY</span>
          {acknowledgment && (
            <span className={`status-badge status-${acknowledgment.status}`}>
              {acknowledgment.status.toUpperCase()}
            </span>
          )}
        </div>
      </div>

      <p className="justification">{recommendation.justification}</p>

      {showDetails && (
        <div className="recommendation-details">
          <div className="detail-section">
            <strong>Supporting Risks:</strong>
            <ul>
              {recommendation.supporting_risks.map((risk, i) => (
                <li key={i}>{risk}</li>
              ))}
            </ul>
          </div>

          <div className="detail-section">
            <strong>Tradeoffs:</strong>
            <ul>
              {recommendation.tradeoffs.map((tradeoff, i) => (
                <li key={i}>{tradeoff}</li>
              ))}
            </ul>
          </div>

          <div className="detail-section">
            <strong>No Action Risk:</strong>
            <p>{recommendation.no_action_risk}</p>
          </div>

          <div className="detail-section">
            <strong>Traceability:</strong>
            <pre style={{ fontSize: '0.85em', background: '#f3f4f6', padding: '8px', borderRadius: '4px' }}>
              {JSON.stringify(recommendation.traceability, null, 2)}
            </pre>
          </div>
        </div>
      )}

      <div className="recommendation-controls">
        <button
          onClick={() => setShowDetails(!showDetails)}
          className="btn-details"
        >
          {showDetails ? 'Hide' : 'Show'} Details
        </button>

        <div className="acknowledgment-buttons">
          <button
            onClick={() => onAcknowledge('acknowledged')}
            className={`btn-status ${acknowledgment?.status === 'acknowledged' ? 'active' : ''}`}
          >
            ✓ Acknowledge
          </button>
          <button
            onClick={() => onAcknowledge('deferred')}
            className={`btn-status ${acknowledgment?.status === 'deferred' ? 'active' : ''}`}
          >
            ⟳ Defer
          </button>
        </div>
      </div>

      {acknowledgment?.analyst_notes && (
        <div className="analyst-notes">
          <strong>Analyst Notes:</strong>
          <p>{acknowledgment.analyst_notes}</p>
        </div>
      )}
    </div>
  );
}

/**
 * Main panel component
 */
export function AnalystRecommendationsPanel({
  projectId,
  phase9Data,
}: AnalystRecommendationsPanelProps): React.ReactElement {
  const [decisionOutput, setDecisionOutput] = useState<DecisionOutput | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { acknowledgments, updateAcknowledgment } = useRecommendationAcknowledgments(projectId);

  useEffect(() => {
    const fetchRecommendations = async () => {
      try {
        setLoading(true);
        const response = await fetch(`/phase12/recommendations/${projectId}`);

        if (response.ok) {
          const data = await response.json();
          setDecisionOutput(data);
          setError(null);
        } else if (response.status === 404) {
          // No recommendations yet - can generate from Phase 9
          if (phase9Data) {
            const genResponse = await fetch('/phase12/recommendations', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                project_id: projectId,
                phase9_output: phase9Data,
              }),
            });

            if (genResponse.ok) {
              const data = await genResponse.json();
              setDecisionOutput(data);
            } else {
              setError('Could not generate recommendations');
            }
          } else {
            setError('No Phase 9 data available to generate recommendations');
          }
        } else {
          setError(`Failed to fetch recommendations (${response.status})`);
        }
      } catch (err) {
        setError(`Error: ${err instanceof Error ? err.message : 'Unknown error'}`);
      } finally {
        setLoading(false);
      }
    };

    fetchRecommendations();
  }, [projectId, phase9Data]);

  if (loading) {
    return (
      <div className="recommendations-panel">
        <div className="panel-header">
          <h2>Decision Support Recommendations</h2>
        </div>
        <div className="loading">Loading recommendations...</div>
      </div>
    );
  }

  return (
    <div className="recommendations-panel">
      <div className="panel-header">
        <h2>Decision Support Recommendations</h2>
        <p className="panel-subtitle">Advisory-only recommendations derived from Phase 9 intelligence</p>
      </div>

      {error && (
        <div className="error-message">
          <strong>⚠️ {error}</strong>
        </div>
      )}

      {decisionOutput && (
        <>
          <div className="recommendations-summary">
            <div className="summary-stat">
              <span className="label">Total Recommendations</span>
              <span className="value">{decisionOutput.summary.total_recommendations}</span>
            </div>
            <div className="summary-stat">
              <span className="label">High Confidence</span>
              <span className="value" style={{ color: '#10b981' }}>
                {decisionOutput.summary.high_confidence_count}
              </span>
            </div>
            <div className="summary-stat">
              <span className="label">Medium Confidence</span>
              <span className="value" style={{ color: '#f59e0b' }}>
                {decisionOutput.summary.medium_confidence_count}
              </span>
            </div>
            <div className="summary-stat">
              <span className="label">Low Confidence</span>
              <span className="value" style={{ color: '#ef4444' }}>
                {decisionOutput.summary.low_confidence_count}
              </span>
            </div>
          </div>

          <div className="recommendations-list">
            {decisionOutput.recommendations.length === 0 ? (
              <div className="no-recommendations">
                No recommendations at this time. Project risks appear to be within acceptable ranges.
              </div>
            ) : (
              decisionOutput.recommendations.map((rec) => (
                <RecommendationCard
                  key={rec.recommendation_id}
                  recommendation={rec}
                  acknowledgment={acknowledgments.get(rec.recommendation_id)}
                  onAcknowledge={(status) =>
                    updateAcknowledgment(rec.recommendation_id, { status })
                  }
                />
              ))
            )}
          </div>

          <div className="recommendations-footer">
            <p>
              <strong>Important:</strong> These recommendations are advisory and created to support
              analyst decision-making. They do not execute any actions or modify project data.
              Analysts retain full control over decisions and implementations.
            </p>
          </div>
        </>
      )}
    </div>
  );
}
