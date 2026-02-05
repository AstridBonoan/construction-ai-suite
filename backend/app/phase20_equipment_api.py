"""
Phase 20: Equipment Maintenance API Endpoints (Flask blueprint)
Expose /analyze, /equipment/<id>, /project/<id> and /health endpoints.
"""
import logging
from flask import Blueprint, request, jsonify

logger = logging.getLogger(__name__)

equipment_bp = Blueprint('equipment', __name__, url_prefix='/api/equipment')


@equipment_bp.route('/analyze', methods=['POST'])
def analyze_equipment():
    try:
        from phase20_equipment_types import Equipment, MaintenanceRecord, FailureEvent, EquipmentType, EquipmentStatus
        from phase20_equipment_analyzer import EquipmentMaintenanceAnalyzer
        from phase20_equipment_integration import feed_equipment_to_core_risk_engine

        data = request.get_json()
        analyzer = EquipmentMaintenanceAnalyzer()

        # Add equipment
        for eq_data in data.get('equipment', []):
            try:
                eq_type = EquipmentType[eq_data.get('equipment_type', 'OTHER').upper()]
            except KeyError:
                eq_type = EquipmentType.OTHER
            
            try:
                status = EquipmentStatus[eq_data.get('status', 'OPERATIONAL').upper()]
            except KeyError:
                status = EquipmentStatus.OPERATIONAL
            
            eq = Equipment(
                equipment_id=eq_data['equipment_id'],
                name=eq_data.get('name', 'Unknown'),
                equipment_type=eq_type,
                acquisition_date=eq_data.get('acquisition_date', '2020-01-01'),
                current_status=status,
                monday_asset_id=eq_data.get('monday_asset_id')
            )
            analyzer.add_equipment(eq)

        # Add maintenance records
        for m_data in data.get('maintenance_records', []):
            rec = MaintenanceRecord(
                project_id=m_data.get('project_id', ''),
                equipment_id=m_data.get('equipment_id', ''),
                maintenance_date=m_data.get('maintenance_date', ''),
                maintenance_type=m_data.get('maintenance_type', 'preventive'),
                duration_hours=m_data.get('duration_hours', 0.0),
                cost=m_data.get('cost', 0.0),
                completed=m_data.get('completed', True),
                notes=m_data.get('notes', '')
            )
            analyzer.add_maintenance_record(rec)

        # Add failure events
        for f_data in data.get('failure_events', []):
            evt = FailureEvent(
                project_id=f_data.get('project_id', ''),
                task_id=f_data.get('task_id', ''),
                equipment_id=f_data.get('equipment_id', ''),
                failure_date=f_data.get('failure_date', ''),
                failure_type=f_data.get('failure_type', 'unknown'),
                repair_duration_hours=f_data.get('repair_duration_hours', 0.0),
                repair_cost=f_data.get('repair_cost', 0.0),
                downtime_impact_days=f_data.get('downtime_impact_days', 0.0),
                notes=f_data.get('notes', '')
            )
            analyzer.add_failure_event(evt)

        project_id = data.get('project_id', 'UNKNOWN')
        project_name = data.get('project_name', 'Unknown')
        equipment_ids = [eq['equipment_id'] for eq in data.get('equipment', [])]

        intelligence = analyzer.create_project_intelligence(
            project_id=project_id,
            project_name=project_name,
            equipment_ids=equipment_ids
        )

        feed_equipment_to_core_risk_engine(intelligence)

        return jsonify({
            'project_id': intelligence.project_id,
            'project_name': intelligence.project_name,
            'equipment_risk_score': intelligence.equipment_risk_score,
            'integration_ready': intelligence.integration_ready
        }), 200

    except Exception as e:
        logger.exception(f"Equipment analysis error: {e}")
        return jsonify({'error': str(e)}), 500


@equipment_bp.route('/equipment/<eq_id>', methods=['GET'])
def get_equipment(eq_id: str):
    return jsonify({'error': 'not_implemented', 'message': 'Persistent lookups not implemented'}), 404


@equipment_bp.route('/project/<pid>', methods=['GET'])
def get_project(pid: str):
    return jsonify({'error': 'not_implemented', 'message': 'Persistent lookups not implemented'}), 404


@equipment_bp.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy', 'service': 'equipment-maintenance'}), 200
