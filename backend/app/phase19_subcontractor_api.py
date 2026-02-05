"""
Phase 19: Subcontractor Performance API Endpoints (Flask blueprint)
Expose /analyze, /subcontractor/<id>, /project/<id> and /health endpoints.
"""
import logging
from flask import Blueprint, request, jsonify

logger = logging.getLogger(__name__)

subcontractor_bp = Blueprint('subcontractor', __name__, url_prefix='/api/subcontractor')


@subcontractor_bp.route('/analyze', methods=['POST'])
def analyze_subcontractors():
    try:
        from phase19_subcontractor_types import Subcontractor, SubcontractorPerformanceRecord
        from phase19_subcontractor_analyzer import SubcontractorPerformanceAnalyzer
        from phase19_subcontractor_integration import feed_subcontractor_to_core_risk_engine

        data = request.get_json()
        analyzer = SubcontractorPerformanceAnalyzer()

        for s in data.get('subcontractors', []):
            sub = Subcontractor(
                subcontractor_id=s['subcontractor_id'],
                name=s.get('name', 'Unknown'),
                monday_vendor_id=s.get('monday_vendor_id')
            )
            analyzer.add_subcontractor(sub)

        for r in data.get('performance_records', []):
            rec = SubcontractorPerformanceRecord(
                project_id=r.get('project_id', ''),
                task_id=r.get('task_id', ''),
                subcontractor_id=r.get('subcontractor_id', ''),
                scheduled_finish_date=r.get('scheduled_finish_date', ''),
                actual_finish_date=r.get('actual_finish_date'),
                days_delay=r.get('days_delay', 0.0),
                completed=r.get('completed', True),
                quality_issues=r.get('quality_issues', 0),
                notes=r.get('notes', '')
            )
            analyzer.add_record(rec)

        project_id = data.get('project_id', 'UNKNOWN')
        project_name = data.get('project_name', 'Unknown')
        subcontractor_ids = [s['subcontractor_id'] for s in data.get('subcontractors', [])]

        intelligence = analyzer.create_project_intelligence(
            project_id=project_id,
            project_name=project_name,
            subcontractor_ids=subcontractor_ids
        )

        feed_subcontractor_to_core_risk_engine(intelligence)

        return jsonify({
            'project_id': intelligence.project_id,
            'project_name': intelligence.project_name,
            'subcontractor_risk_score': intelligence.subcontractor_risk_score,
            'integration_ready': intelligence.integration_ready
        }), 200

    except Exception as e:
        logger.exception(f"Subcontractor analysis error: {e}")
        return jsonify({'error': str(e)}), 500


@subcontractor_bp.route('/subcontractor/<sid>', methods=['GET'])
def get_subcontractor(sid: str):
    return jsonify({'error': 'not_implemented', 'message': 'Persistent lookups not implemented'}), 404


@subcontractor_bp.route('/project/<pid>', methods=['GET'])
def get_project(pid: str):
    return jsonify({'error': 'not_implemented', 'message': 'Persistent lookups not implemented'}), 404


@subcontractor_bp.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy', 'service': 'subcontractor-performance'}), 200
