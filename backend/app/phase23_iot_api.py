"""
Real-Time IoT REST API for Phase 23
Endpoints for sensor data streaming, intelligence queries, and alert management
"""
from flask import Blueprint, request, jsonify
from datetime import datetime
from typing import Dict, Optional
import logging

from phase23_iot_analyzer import IoTAnalyzer
from phase23_iot_integration import create_iot_integration
from phase23_alert_service import get_alert_manager
try:
    from phase23_alert_scheduler import get_scheduler_status
    SCHEDULER_AVAILABLE = True
except ImportError:
    SCHEDULER_AVAILABLE = False
from phase23_iot_types import (
    WeatherSnapshot,
    WeatherCondition,
    EquipmentSensor,
    SiteActivityMonitor,
    AirQualityMonitor,
    SensorReading,
    SensorType,
    SensorStatus,
)

logger = logging.getLogger(__name__)

# Blueprint for Phase 23 IoT endpoints
iot_bp = Blueprint('iot', __name__, url_prefix='/api/phase23/iot')

# Global analyzer and integration registry
analyzer = IoTAnalyzer()
integrations: Dict[str, 'IoTRiskIntegration'] = {}


def get_or_create_integration(project_id: str):
    """Get or create IoT integration for project"""
    if project_id not in integrations:
        integrations[project_id] = create_iot_integration(project_id)
    return integrations[project_id]


@iot_bp.route('/health', methods=['GET'])
def health_check():
    """
    Check IoT module health status.

    Returns:
        Health status information
    """
    return jsonify({
        'status': 'healthy',
        'service': 'phase23_iot',
        'timestamp': datetime.now().isoformat(),
        'active_projects': len(integrations),
    }), 200


@iot_bp.route('/stream/<project_id>', methods=['POST'])
def ingest_sensor_stream(project_id: str):
    """
    Ingest real-time sensor data stream for a project.

    Request body:
    {
        'sensor_id': str,
        'sensor_type': str (from SensorType enum),
        'value': float,
        'unit': str,
        'status': str (from SensorStatus enum),
        'battery_level': int (optional),
        'confidence': float (0-1),
        'location': str (optional),
    }

    Returns:
        Ingestion confirmation and immediate anomaly alerts
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        # Extract and validate sensor reading
        sensor_id = data.get('sensor_id')
        if not sensor_id:
            return jsonify({'error': 'sensor_id required'}), 400

        # Parse sensor status
        try:
            status = SensorStatus[data.get('status', 'ACTIVE').upper()]
        except KeyError:
            status = SensorStatus.ACTIVE

        # Create sensor reading
        reading = SensorReading(
            reading_id=f"{sensor_id}_{datetime.now().isoformat()}",
            sensor_id=sensor_id,
            reading_timestamp=data.get('timestamp', datetime.now().isoformat()),
            value=data.get('value', 0.0),
            unit=data.get('unit', 'unknown'),
            status=status,
            battery_level=data.get('battery_level'),
            confidence=data.get('confidence', 0.9),
            location=data.get('location'),
        )

        # Check for anomalies
        # In production, would maintain buffer of readings
        alerts = []

        # Immediate checks
        if reading.battery_level and reading.battery_level < 10:
            alerts.append({
                'type': 'low_battery',
                'severity': 'high',
                'sensor_id': sensor_id,
                'value': reading.battery_level,
                'message': f"Low battery detected: {reading.battery_level}%",
            })

        if reading.status == SensorStatus.OFFLINE:
            alerts.append({
                'type': 'sensor_offline',
                'severity': 'critical',
                'sensor_id': sensor_id,
                'message': f"Sensor {sensor_id} is offline",
            })

        return jsonify({
            'status': 'ingested',
            'sensor_id': sensor_id,
            'timestamp': reading.reading_timestamp,
            'alerts': alerts,
        }), 202

    except Exception as e:
        logger.error(f"Error ingesting sensor stream: {str(e)}")
        return jsonify({'error': str(e)}), 500


@iot_bp.route('/weather/<project_id>', methods=['POST'])
def update_weather_conditions(project_id: str):
    """
    Update current weather conditions for project site.

    Request body (all optional):
    {
        'weather_condition': str (WeatherCondition enum),
        'temperature_celsius': float,
        'humidity_percent': float (0-100),
        'wind_speed_kmh': float,
        'rainfall_mm': float,
        'visibility_meters': float,
        'location': str,
    }

    Returns:
        Processed weather with calculated risk scores
    """
    try:
        data = request.get_json() or {}
        integration = get_or_create_integration(project_id)

        # Parse weather condition
        weather_condition_str = data.get('weather_condition', 'CLEAR').upper()
        try:
            weather_condition = WeatherCondition[weather_condition_str]
        except KeyError:
            weather_condition = WeatherCondition.CLEAR

        # Create weather snapshot
        weather = WeatherSnapshot(
            location=data.get('location', 'site'),
            weather_condition=weather_condition,
            temperature_celsius=data.get('temperature_celsius', 20),
            humidity_percent=data.get('humidity_percent', 50),
            wind_speed_kmh=data.get('wind_speed_kmh', 0),
            rainfall_mm=data.get('rainfall_mm', 0),
            visibility_meters=data.get('visibility_meters', 9999),
        )

        # Process weather
        processed_weather = analyzer.process_weather_snapshot(weather)

        return jsonify({
            'status': 'processed',
            'weather_condition': processed_weather.weather_condition.value,
            'temperature_celsius': processed_weather.temperature_celsius,
            'humidity_percent': processed_weather.humidity_percent,
            'wind_speed_kmh': processed_weather.wind_speed_kmh,
            'delay_risk_score': processed_weather.delay_risk_score,
            'safety_risk_score': processed_weather.safety_risk_score,
            'safety_level': processed_weather.safety_level.value,
            'explanation': processed_weather.explanation,
        }), 200

    except Exception as e:
        logger.error(f"Error updating weather: {str(e)}")
        return jsonify({'error': str(e)}), 500


@iot_bp.route('/equipment/<project_id>', methods=['POST'])
def update_equipment_sensors(project_id: str):
    """
    Update equipment sensor data for health monitoring.

    Request body:
    {
        'equipment_id': str,
        'equipment_type': str,
        'status': str (EquipmentStatus enum),
        'operating_hours_total': int,
        'temperature_celsius': float (optional),
        'vibration_hz': float (optional),
        'maintenance_due_days': int (optional),
        'location_gps': {'lat': float, 'lon': float} (optional),
    }

    Returns:
        Equipment health analysis with failure probability
    """
    try:
        data = request.get_json()
        if not data or 'equipment_id' not in data:
            return jsonify({'error': 'equipment_id required'}), 400

        # Create equipment sensor
        equipment = EquipmentSensor(
            equipment_id=data['equipment_id'],
            equipment_type=data.get('equipment_type', 'unknown'),
            operating_hours_total=data.get('operating_hours_total', 0),
            temperature_celsius=data.get('temperature_celsius'),
            vibration_hz=data.get('vibration_hz'),
            maintenance_due_days=data.get('maintenance_due_days', 90),
            location_gps=data.get('location_gps'),
        )

        # Analyze equipment health
        analyzed = analyzer.analyze_equipment_health(equipment)

        return jsonify({
            'status': 'analyzed',
            'equipment_id': analyzed.equipment_id,
            'health_score': analyzed.health_score,
            'maintenance_risk_score': analyzed.maintenance_risk_score,
            'failure_probability': analyzed.failure_probability,
            'maintenance_due_days': analyzed.maintenance_due_days,
            'estimated_downtime_hours': analyzed.estimated_downtime_hours,
        }), 200

    except Exception as e:
        logger.error(f"Error updating equipment: {str(e)}")
        return jsonify({'error': str(e)}), 500


@iot_bp.route('/activity/<project_id>', methods=['POST'])
def update_site_activity(project_id: str):
    """
    Update site activity and safety monitoring data.

    Request body:
    {
        'active_workers_count': int,
        'active_equipment_count': int,
        'safety_violation_count': int,
        'restricted_area_breaches': int,
        'emergency_exits_clear': bool,
        'first_aid_station_accessible': bool,
        'equipment_concentration_risk': float (0-1),
    }

    Returns:
        Activity analysis with hazard detection
    """
    try:
        data = request.get_json() or {}

        # Create activity monitor
        activity = SiteActivityMonitor(
            active_workers_count=data.get('active_workers_count', 0),
            active_equipment_count=data.get('active_equipment_count', 0),
            safety_violation_count=data.get('safety_violation_count', 0),
            restricted_area_breaches=data.get('restricted_area_breaches', 0),
            emergency_exits_clear=data.get('emergency_exits_clear', True),
            first_aid_station_accessible=data.get('first_aid_station_accessible', True),
            equipment_concentration_risk=data.get('equipment_concentration_risk', 0.0),
        )

        # Analyze activity
        analyzed = analyzer.analyze_site_activity(activity)

        return jsonify({
            'status': 'analyzed',
            'active_workers': analyzed.active_workers_count,
            'active_equipment': analyzed.active_equipment_count,
            'worker_proximity_risk_score': analyzed.worker_proximity_risk_score,
            'hazard_detected': analyzed.hazard_detected,
            'hazard_description': analyzed.hazard_description,
            'safety_violations': analyzed.safety_violation_count,
        }), 200

    except Exception as e:
        logger.error(f"Error updating activity: {str(e)}")
        return jsonify({'error': str(e)}), 500


@iot_bp.route('/air-quality/<project_id>', methods=['POST'])
def update_air_quality(project_id: str):
    """
    Update air quality monitoring data.

    Request body:
    {
        'air_quality_index': float,
        'pm25_ugm3': float (optional),
        'pm10_ugm3': float (optional),
        'co2_ppm': float (optional),
        'co_ppm': float (optional),
        'no2_ppb': float (optional),
        'so2_ppb': float (optional),
        'o3_ppb': float (optional),
    }

    Returns:
        Air quality analysis with respiratory risk
    """
    try:
        data = request.get_json() or {}

        # Create air quality monitor
        air_quality = AirQualityMonitor(
            air_quality_index=data.get('air_quality_index', 0),
            pm25_ugm3=data.get('pm25_ugm3'),
            pm10_ugm3=data.get('pm10_ugm3'),
            co2_ppm=data.get('co2_ppm'),
            co_ppm=data.get('co_ppm'),
            no2_ppb=data.get('no2_ppb'),
            so2_ppb=data.get('so2_ppb'),
            o3_ppb=data.get('o3_ppb'),
        )

        # Analyze air quality
        analyzed = analyzer.analyze_air_quality(air_quality)

        return jsonify({
            'status': 'analyzed',
            'air_quality_index': analyzed.air_quality_index,
            'respiratory_risk_score': analyzed.respiratory_risk_score,
            'dust_storm_risk': analyzed.dust_storm_risk,
            'visibility_impact': analyzed.visibility_impact,
            'pm25': analyzed.pm25_ugm3,
        }), 200

    except Exception as e:
        logger.error(f"Error updating air quality: {str(e)}")
        return jsonify({'error': str(e)}), 500


@iot_bp.route('/intelligence/<project_id>', methods=['GET'])
def get_real_time_intelligence(project_id: str):
    """
    Get current real-time site intelligence for project.

    Query parameters:
    - task_id (optional): Get intelligence for specific task

    Returns:
        Complete RealTimeSiteIntelligence data
    """
    try:
        integration = get_or_create_integration(project_id)
        intelligence = integration.current_intelligence

        if not intelligence:
            return jsonify({
                'status': 'no_data',
                'message': 'No IoT data available yet for project',
                'project_id': project_id,
            }), 404

        return jsonify({
            'intelligence_id': intelligence.intelligence_id,
            'project_id': intelligence.project_id,
            'timestamp': intelligence.timestamp,
            'overall_site_risk_score': intelligence.overall_site_risk_score,
            'delay_risk_score': intelligence.delay_risk_score,
            'safety_risk_score': intelligence.safety_risk_score,
            'equipment_risk_score': intelligence.equipment_risk_score,
            'environmental_risk_score': intelligence.environmental_risk_score,
            'work_stoppable': intelligence.work_stoppable,
            'work_proceeding': intelligence.work_proceeding,
            'weather': {
                'condition': intelligence.weather_snapshot.weather_condition.value if intelligence.weather_snapshot else None,
                'temperature': intelligence.weather_snapshot.temperature_celsius if intelligence.weather_snapshot else None,
                'humidity': intelligence.weather_snapshot.humidity_percent if intelligence.weather_snapshot else None,
                'wind': intelligence.weather_snapshot.wind_speed_kmh if intelligence.weather_snapshot else None,
                'delay_risk': intelligence.weather_snapshot.delay_risk_score if intelligence.weather_snapshot else 0,
                'safety_risk': intelligence.weather_snapshot.safety_risk_score if intelligence.weather_snapshot else 0,
            },
            'equipment_count': len(intelligence.active_equipment),
            'equipment_at_risk': sum(1 for eq in intelligence.active_equipment if eq.failure_probability > 0.3),
            'active_alerts': len(intelligence.alerts_active),
            'alerts': intelligence.alerts_active,
            'recommendations': intelligence.recommendations,
            'summary': intelligence.project_summary,
        }), 200

    except Exception as e:
        logger.error(f"Error getting intelligence: {str(e)}")
        return jsonify({'error': str(e)}), 500


@iot_bp.route('/intelligence/<project_id>/history', methods=['GET'])
def get_intelligence_history(project_id: str):
    """
    Get historical intelligence records for project.

    Query parameters:
    - limit (optional, default=10): Maximum records to return

    Returns:
        List of historical intelligence records
    """
    try:
        integration = get_or_create_integration(project_id)
        limit = request.args.get('limit', 10, type=int)

        history = integration.get_intelligence_history(limit)

        return jsonify({
            'project_id': project_id,
            'total_records': len(history),
            'records': [
                {
                    'timestamp': record.timestamp,
                    'overall_risk': record.overall_site_risk_score,
                    'safety_risk': record.safety_risk_score,
                    'delay_risk': record.delay_risk_score,
                    'equipment_risk': record.equipment_risk_score,
                    'work_proceeding': record.work_proceeding,
                }
                for record in history
            ],
        }), 200

    except Exception as e:
        logger.error(f"Error getting history: {str(e)}")
        return jsonify({'error': str(e)}), 500


@iot_bp.route('/alerts/<project_id>', methods=['GET'])
def get_active_alerts(project_id: str):
    """
    Get all active alerts for project.

    Returns:
        List of current alerts with severity
    """
    try:
        integration = get_or_create_integration(project_id)
        intelligence = integration.current_intelligence

        alerts = []
        if intelligence:
            alerts = [
                {
                    'message': alert,
                    'timestamp': intelligence.timestamp,
                }
                for alert in intelligence.alerts_active
            ]

        return jsonify({
            'project_id': project_id,
            'active_alerts': len(alerts),
            'alerts': alerts,
        }), 200

    except Exception as e:
        logger.error(f"Error getting alerts: {str(e)}")
        return jsonify({'error': str(e)}), 500


@iot_bp.route('/risk-score/<project_id>', methods=['GET'])
def get_risk_scores(project_id: str):
    """
    Get current risk scores for Feature 1 core engine integration.

    Returns:
        Risk scores formatted for core engine
    """
    try:
        integration = get_or_create_integration(project_id)
        risk_data = integration.get_core_engine_input()

        return jsonify(risk_data), 200

    except Exception as e:
        logger.error(f"Error getting risk scores: {str(e)}")
        return jsonify({'error': str(e)}), 500


@iot_bp.route('/schedule-impact/<project_id>', methods=['GET'])
def get_schedule_impact(project_id: str):
    """
    Get estimated schedule impact from current conditions.

    Returns:
        Schedule impact estimation
    """
    try:
        integration = get_or_create_integration(project_id)
        impact = integration.estimate_schedule_impact()

        return jsonify({
            'project_id': project_id,
            'estimated_delay_hours': impact['estimated_delay_hours'],
            'work_availability_percent': impact['work_availability_percent'],
            'confidence': impact['confidence'],
            'factors': impact['contributing_factors'],
        }), 200

    except Exception as e:
        logger.error(f"Error getting schedule impact: {str(e)}")
        return jsonify({'error': str(e)}), 500


@iot_bp.route('/safety-constraints/<project_id>', methods=['GET'])
def get_safety_constraints(project_id: str):
    """
    Get worker safety constraints based on current conditions.

    Returns:
        Safety constraints for workforce scheduling
    """
    try:
        integration = get_or_create_integration(project_id)
        constraints = integration.get_worker_safety_constraints()

        return jsonify({
            'project_id': project_id,
            'work_allowed': constraints['work_allowed'],
            'max_work_hours': constraints['max_work_hours'],
            'required_ppe': constraints['required_ppe'],
            'restricted_activities': constraints['restricted_activities'],
            'safety_risk_score': constraints['safety_risk_score'],
        }), 200

    except Exception as e:
        logger.error(f"Error getting safety constraints: {str(e)}")
        return jsonify({'error': str(e)}), 500


@iot_bp.route('/compliance/<project_id>', methods=['GET'])
def get_compliance_status(project_id: str):
    """
    Get environmental compliance status.

    Returns:
        Compliance information for Feature 7 integration
    """
    try:
        integration = get_or_create_integration(project_id)
        compliance = integration.get_environmental_compliance_status()

        return jsonify({
            'project_id': project_id,
            'compliant': compliance['compliant'],
            'air_quality_compliant': compliance['air_quality_compliant'],
            'noise_compliant': compliance['noise_compliant'],
            'dust_control_needed': compliance['dust_control_needed'],
            'air_quality_index': compliance['air_quality_index'],
            'violations_detected': compliance['violations_detected'],
        }), 200

    except Exception as e:
        logger.error(f"Error getting compliance status: {str(e)}")
        return jsonify({'error': str(e)}), 500


@iot_bp.route('/monday-updates/<project_id>', methods=['GET'])
def get_monday_updates(project_id: str):
    """
    Get IoT data formatted for monday.com board integration.

    Returns:
        Column name -> value mappings for monday.com
    """
    try:
        integration = get_or_create_integration(project_id)
        updates = integration.get_monday_com_updates()

        return jsonify({
            'project_id': project_id,
            'updates': updates,
            'ready_for_monday': len(updates) > 0,
        }), 200

    except Exception as e:
        logger.error(f"Error preparing monday updates: {str(e)}")
        return jsonify({'error': str(e)}), 500


@iot_bp.route('/reset/<project_id>', methods=['DELETE'])
def reset_project_iot(project_id: str):
    """
    Reset IoT tracking for a project (for testing/reset scenarios).

    Returns:
        Confirmation of reset
    """
    try:
        if project_id in integrations:
            integrations[project_id].reset_project_state()
            del integrations[project_id]

        return jsonify({
            'status': 'reset',
            'project_id': project_id,
        }), 200

    except Exception as e:
        logger.error(f"Error resetting project: {str(e)}")
        return jsonify({'error': str(e)}), 500


# ============================================================================
# Alert Management Endpoints
# ============================================================================

@iot_bp.route('/alerts/<project_id>', methods=['GET'])
def get_project_alerts(project_id: str):
    """
    Get all current alerts for a project.

    Args:
        project_id: The project identifier

    Returns:
        List of active alerts
    """
    try:
        alert_manager = get_alert_manager()
        alerts = alert_manager.get_alerts(project_id)

        return jsonify({
            'project_id': project_id,
            'alerts': [alert.to_dict() for alert in alerts],
            'total': len(alerts),
        }), 200

    except Exception as e:
        logger.error(f"Error retrieving alerts for project {project_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500


@iot_bp.route('/alerts/<project_id>/<alert_id>', methods=['GET'])
def get_alert_detail(project_id: str, alert_id: str):
    """
    Get detailed information about a specific alert.

    Args:
        project_id: The project identifier
        alert_id: The alert identifier

    Returns:
        Alert details or 404 if not found
    """
    try:
        alert_manager = get_alert_manager()
        alert = alert_manager.get_alerts(project_id)
        
        # Find the specific alert
        alert_obj = next((a for a in alert if a.alert_id == alert_id), None)
        if not alert_obj:
            return jsonify({'error': 'Alert not found'}), 404

        return jsonify({
            'project_id': project_id,
            'alert': alert_obj.to_dict(),
        }), 200

    except Exception as e:
        logger.error(f"Error retrieving alert {alert_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500


@iot_bp.route('/alerts/<project_id>/<alert_id>/acknowledge', methods=['POST'])
def acknowledge_alert(project_id: str, alert_id: str):
    """
    Acknowledge an alert (mark as seen/acknowledged).

    Args:
        project_id: The project identifier
        alert_id: The alert identifier
        request.json: Optional notes from acknowledger

    Returns:
        Updated alert or error
    """
    try:
        alert_manager = get_alert_manager()
        notes = request.json.get('notes', '') if request.json else ''
        
        # Acknowledge the alert
        success = alert_manager.acknowledge_alert(project_id, alert_id)
        
        if not success:
            return jsonify({'error': 'Alert not found or already acknowledged'}), 404

        # Get updated alert
        alerts = alert_manager.get_alerts(project_id)
        alert_obj = next((a for a in alerts if a.alert_id == alert_id), None)

        return jsonify({
            'project_id': project_id,
            'alert': alert_obj.to_dict(),
            'status': 'acknowledged',
            'acknowledged_at': alert_obj.acknowledged_at.isoformat() if alert_obj.acknowledged_at else None,
        }), 200

    except Exception as e:
        logger.error(f"Error acknowledging alert {alert_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500


@iot_bp.route('/alerts/<project_id>/<alert_id>/resolve', methods=['POST'])
def resolve_alert(project_id: str, alert_id: str):
    """
    Resolve an alert (mark as resolved/closed).

    Args:
        project_id: The project identifier
        alert_id: The alert identifier
        request.json: Optional resolution notes

    Returns:
        Alert removal confirmation or error
    """
    try:
        alert_manager = get_alert_manager()
        notes = request.json.get('notes', '') if request.json else ''
        
        # Resolve the alert
        success = alert_manager.resolve_alert(project_id, alert_id)
        
        if not success:
            return jsonify({'error': 'Alert not found'}), 404

        return jsonify({
            'project_id': project_id,
            'alert_id': alert_id,
            'status': 'resolved',
            'resolved_at': datetime.utcnow().isoformat(),
        }), 200

    except Exception as e:
        logger.error(f"Error resolving alert {alert_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500


@iot_bp.route('/alerts-history/<project_id>', methods=['GET'])
def get_alerts_history(project_id: str):
    """
    Get alert statistics and history for a project.

    Query Parameters:
        alert_type: Filter by alert type (optional)
        severity: Filter by severity level (optional)
        days: Number of past days to include (default 7)

    Returns:
        Alert statistics and summary
    """
    try:
        alert_manager = get_alert_manager()
        alerts = alert_manager.get_alerts(project_id)
        
        # Filter by type if requested
        alert_type_filter = request.args.get('alert_type')
        if alert_type_filter:
            alerts = [a for a in alerts if a.alert_type.value == alert_type_filter]
        
        # Filter by severity if requested
        severity_filter = request.args.get('severity')
        if severity_filter:
            alerts = [a for a in alerts if a.severity.value == severity_filter]
        
        # Calculate statistics
        total_alerts = len(alerts)
        acknowledged = sum(1 for a in alerts if a.acknowledged_at)
        unacknowledged = total_alerts - acknowledged
        
        # Count by severity
        severity_counts = {}
        for alert in alerts:
            severity = alert.severity.value
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        # Count by type
        type_counts = {}
        for alert in alerts:
            alert_t = alert.alert_type.value
            type_counts[alert_t] = type_counts.get(alert_t, 0) + 1

        return jsonify({
            'project_id': project_id,
            'statistics': {
                'total_alerts': total_alerts,
                'acknowledged': acknowledged,
                'unacknowledged': unacknowledged,
                'by_severity': severity_counts,
                'by_type': type_counts,
            },
            'alerts': [alert.to_dict() for alert in alerts],
        }), 200

    except Exception as e:
        logger.error(f"Error retrieving alert history for project {project_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500


@iot_bp.route('/alerts/escalation-test/<project_id>', methods=['POST'])
def test_escalation_process(project_id: str):
    """
    Manually trigger escalation processor (for testing/debugging).

    This will process any alerts that are due for escalation based on their
    severity and the time they were created.

    Args:
        project_id: The project identifier

    Returns:
        Escalation results and statistics
    """
    try:
        alert_manager = get_alert_manager()
        
        # Get escalation candidates before processing
        candidates = alert_manager.get_escalation_candidates()
        candidates_for_project = [a for a in candidates if a.project_id == project_id]
        
        # Process escalations
        escalation_results = alert_manager.process_escalations()

        return jsonify({
            'project_id': project_id,
            'escalation_candidates_found': len(candidates_for_project),
            'total_escalations_processed': escalation_results['processed'],
            'next_escalations': escalation_results['next_escalations'],
        }), 200

    except Exception as e:
        logger.error(f"Error processing escalations for project {project_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500


@iot_bp.route('/scheduler/status', methods=['GET'])
def get_scheduler_status_endpoint():
    """
    Get the status of the background alert scheduler.

    Returns:
        Scheduler status including running jobs and timing information
    """
    if not SCHEDULER_AVAILABLE:
        return jsonify({
            'error': 'Scheduler not available',
            'status': 'unavailable',
        }), 503

    try:
        status = get_scheduler_status()

        return jsonify({
            'scheduler': status,
            'timestamp': datetime.utcnow().isoformat(),
            'description': 'Background task scheduler for alert escalation and cleanup',
        }), 200

    except Exception as e:
        logger.error(f"Error getting scheduler status: {str(e)}")
        return jsonify({'error': str(e)}), 500
