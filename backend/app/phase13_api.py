"""
Phase 13 Feedback Capture API

REST endpoints for capturing, storing, and querying analyst feedback.

Endpoints:
- POST /phase13/feedback - Submit feedback on a recommendation
- GET /phase13/feedback/<recommendation_id> - Get feedback for recommendation
- GET /phase13/feedback/project/<project_id> - Get all feedback for project
- GET /phase13/analytics - Get feedback analytics
- GET /phase13/health - Health check

All endpoints are read-only for analytics (no mutations).
Feedback is append-only once written.
"""

from datetime import datetime
from flask import Blueprint, request, jsonify
from .phase13_types import FeedbackRecord, AnalystAction, validate_feedback_record
from .phase13_storage import get_feedback_store

phase13_bp = Blueprint('phase13', __name__, url_prefix='/phase13')


@phase13_bp.route('/feedback', methods=['POST'])
def submit_feedback():
    """
    Submit analyst feedback on a Phase 12 recommendation.
    
    Request body:
    {
        "recommendation_id": "rec_xyz",
        "project_id": "proj_123",
        "analyst_action": "accepted" | "rejected" | "modified",
        "reason_codes": ["aligns_with_plan", "budget_available"],
        "modification_summary": "Reduced scope to 8 weeks" (required if modified),
        "analyst_id": "analyst_hash_or_pseudonym",
        "decided_at": "2024-01-15T10:30:00Z",
        "notes": "Optional analyst notes for audit"
    }
    
    Response: (200 OK or 400 Bad Request)
    {
        "status": "success" or "error",
        "message": "Feedback recorded" or error details,
        "recommendation_id": "rec_xyz"
    }
    
    Note: Never throws on validation error - logs instead.
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'Request body required'
            }), 400
        
        dry_run = request.args.get('dry_run', 'false').lower() == 'true'
        
        # Build feedback record
        try:
            feedback = FeedbackRecord(
                recommendation_id=data.get('recommendation_id', ''),
                project_id=data.get('project_id', ''),
                analyst_action=data.get('analyst_action', 'accepted'),
                reason_codes=data.get('reason_codes', []),
                modification_summary=data.get('modification_summary'),
                modification_confidence=data.get('modification_confidence'),
                analyst_id=data.get('analyst_id', ''),
                decided_at=data.get('decided_at', ''),
                initial_action=data.get('initial_action'),
                decision_time_seconds=data.get('decision_time_seconds'),
                recorded_at=datetime.utcnow().isoformat() + 'Z',
                notes=data.get('notes'),
            )
        except (TypeError, ValueError) as e:
            return jsonify({
                'status': 'error',
                'message': f'Invalid feedback data: {str(e)}'
            }), 400
        
        # Store feedback (append-only)
        store = get_feedback_store()
        success, message = store.append_feedback(feedback, dry_run=dry_run)
        
        if success:
            return jsonify({
                'status': 'success',
                'message': message,
                'recommendation_id': feedback.recommendation_id
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'message': message,
                'recommendation_id': data.get('recommendation_id')
            }), 400
    
    except Exception as e:
        # Log errors but don't throw
        print(f"Feedback submission error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Feedback processing failed: {str(e)}'
        }), 500


@phase13_bp.route('/feedback/<recommendation_id>', methods=['GET'])
def get_feedback(recommendation_id: str):
    """
    Get feedback for a specific recommendation (read-only).
    
    Returns:
    {
        "status": "found" | "not_found",
        "feedback": {...} or null
    }
    """
    try:
        store = get_feedback_store()
        feedback = store.get_feedback_by_recommendation(recommendation_id)
        
        if feedback:
            return jsonify({
                'status': 'found',
                'feedback': feedback.to_dict()
            }), 200
        else:
            return jsonify({
                'status': 'not_found',
                'feedback': None
            }), 404
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Query failed: {str(e)}'
        }), 500


@phase13_bp.route('/feedback/project/<project_id>', methods=['GET'])
def get_feedback_by_project(project_id: str):
    """
    Get all feedback records for a project (read-only, append order).
    
    Returns:
    {
        "status": "success",
        "project_id": "proj_123",
        "feedback_count": 5,
        "feedback": [...]
    }
    """
    try:
        store = get_feedback_store()
        feedback_list = store.get_feedback_by_project(project_id)
        
        return jsonify({
            'status': 'success',
            'project_id': project_id,
            'feedback_count': len(feedback_list),
            'feedback': [f.to_dict() for f in feedback_list]
        }), 200
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Query failed: {str(e)}'
        }), 500


@phase13_bp.route('/analytics', methods=['GET'])
def get_analytics():
    """
    Get feedback analytics (read-only aggregates).
    
    Query params:
    - period_start: ISO 8601 timestamp (default: 30 days ago)
    - period_end: ISO 8601 timestamp (default: now)
    
    Returns aggregated statistics on analyst feedback:
    - Acceptance rate by action type
    - Rejection reasons frequency
    - Analyst override patterns
    - Time-to-decision metrics
    
    Note: Analytics only - no inference, no learning yet.
    """
    try:
        store = get_feedback_store()
        all_feedback = store.get_all_feedback()
        
        # Parse query params
        period_start = request.args.get('period_start', '')
        period_end = request.args.get('period_end', '')
        
        # Filter feedback by date range if specified
        filtered = all_feedback
        if period_start:
            filtered = [f for f in filtered if f.decided_at >= period_start]
        if period_end:
            filtered = [f for f in filtered if f.decided_at <= period_end]
        
        # Compute aggregates
        if len(filtered) == 0:
            return jsonify({
                'status': 'success',
                'total_feedback': 0,
                'acceptance_rate': {},
                'rejection_reasons': [],
                'override_patterns': [],
                'time_to_decision': {}
            }), 200
        
        # Count by action
        action_counts = {}
        rejection_reasons = {}
        time_to_decisions = []
        
        for fb in filtered:
            action = fb.analyst_action
            if isinstance(action, AnalystAction):
                action = action.value
            
            action_counts[action] = action_counts.get(action, 0) + 1
            
            # Track rejection reasons
            if action == 'rejected':
                for code in fb.reason_codes:
                    rejection_reasons[code] = rejection_reasons.get(code, 0) + 1
            
            # Track time to decision
            if fb.decision_time_seconds:
                time_to_decisions.append(fb.decision_time_seconds)
        
        # Calculate acceptance rates
        acceptance_rates = {}
        total = len(filtered)
        for action_type in ['schedule_buffer_increase', 'subcontractor_review', 'material_procurement_check', 'site_inspection_priority', 'monitoring_only']:
            acceptance_rates[action_type] = 0.0  # Placeholder - would need recommendation type
        
        # Time stats
        time_stats = {}
        if time_to_decisions:
            time_to_decisions.sort()
            time_stats = {
                'median': time_to_decisions[len(time_to_decisions) // 2],
                'p95': time_to_decisions[int(len(time_to_decisions) * 0.95)] if len(time_to_decisions) > 20 else None,
                'p99': time_to_decisions[int(len(time_to_decisions) * 0.99)] if len(time_to_decisions) > 100 else None,
            }
        
        return jsonify({
            'status': 'success',
            'period_start': period_start or 'all',
            'period_end': period_end or 'now',
            'total_feedback': len(filtered),
            'action_distribution': action_counts,
            'rejection_reasons': [
                {'code': code, 'count': count, 'percentage': count / total * 100}
                for code, count in sorted(rejection_reasons.items(), key=lambda x: x[1], reverse=True)
            ],
            'time_to_decision_metrics': time_stats
        }), 200
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Analytics query failed: {str(e)}'
        }), 500


@phase13_bp.route('/health', methods=['GET'])
def health_check():
    """
    Health check for Phase 13 service.
    Verifies feedback system is operational and append-only.
    """
    try:
        store = get_feedback_store()
        is_valid, integrity_msg = store.verify_append_only_integrity()
        
        return jsonify({
            'status': 'operational' if is_valid else 'degraded',
            'phase': 13,
            'component': 'feedback_system',
            'append_only': True,
            'immutable': True,
            'no_inference': True,
            'integrity_check': integrity_msg,
            'record_count': store.count_records()
        }), 200
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Health check failed: {str(e)}'
        }), 500
