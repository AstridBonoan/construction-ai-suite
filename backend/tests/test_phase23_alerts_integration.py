"""
Integration tests for Phase 23 Alert System
Tests end-to-end alert flow from IoK analyzer through API
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timedelta
import json
import sys
from pathlib import Path

# Add backend app to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'app'))

from phase23_iot_analyzer import IoTAnalyzer
from phase23_iot_types import (
    WeatherSnapshot,
    WeatherCondition,
    EquipmentSensor,
    SiteActivityMonitor,
    AirQualityMonitor,
    SafetyLevel,
    EquipmentCondition,
)
from phase23_alert_service import (
    get_alert_manager,
    AlertType,
    AlertSeverity,
    AlertEscalationLevel,
)


class TestAlertsFromWeatherAnalysis:
    """Test alert generation from weather analysis"""

    def test_critical_weather_generates_alert(self):
        """Test that critical weather conditions generate alerts"""
        with patch.object(IoTAnalyzer, '__init__', lambda x: None):
            analyzer = IoTAnalyzer()
            analyzer.alert_manager = get_alert_manager()

        # Create critical weather snapshot
        weather = WeatherSnapshot()
        weather.condition = WeatherCondition.THUNDERSTORM
        weather.wind_speed_kmh = 80  # High wind
        weather.temperature_celsius = 35  # Hot
        weather.safety_level = SafetyLevel.CRITICAL

        with patch.object(analyzer.alert_manager, 'create_and_send_alert') as mock_alert:
            analyzer.process_weather_snapshot("proj_001", weather)
            
            # Should generate an alert
            assert mock_alert.called
            call_args = mock_alert.call_args
            assert call_args[1]['alert_type'] == AlertType.WEATHER_CRITICAL
            assert call_args[1]['severity'] == AlertSeverity.CRITICAL

    def test_hazardous_weather_generates_alert(self):
        """Test that hazardous weather conditions generate alerts"""
        with patch.object(IoTAnalyzer, '__init__', lambda x: None):
            analyzer = IoTAnalyzer()
            analyzer.alert_manager = get_alert_manager()

        # Create hazardous weather snapshot
        weather = WeatherSnapshot()
        weather.condition = WeatherCondition.HEAVY_RAIN
        weather.wind_speed_kmh = 50
        weather.temperature_celsius = 15
        weather.safety_level = SafetyLevel.HAZARDOUS

        with patch.object(analyzer.alert_manager, 'create_and_send_alert') as mock_alert:
            analyzer.process_weather_snapshot("proj_001", weather)
            
            # Should generate an alert
            assert mock_alert.called
            call_args = mock_alert.call_args
            assert call_args[1]['alert_type'] == AlertType.WEATHER_CRITICAL
            assert call_args[1]['severity'] == AlertSeverity.HIGH

    def test_safe_weather_no_alert(self):
        """Test that safe weather doesn't generate alerts"""
        with patch.object(IoTAnalyzer, '__init__', lambda x: None):
            analyzer = IoTAnalyzer()
            analyzer.alert_manager = get_alert_manager()

        # Create safe weather snapshot
        weather = WeatherSnapshot()
        weather.condition = WeatherCondition.CLEAR_SKY
        weather.wind_speed_kmh = 10
        weather.temperature_celsius = 22
        weather.safety_level = SafetyLevel.SAFE

        with patch.object(analyzer.alert_manager, 'create_and_send_alert') as mock_alert:
            analyzer.process_weather_snapshot("proj_001", weather)
            
            # Should NOT generate an alert
            assert not mock_alert.called


class TestAlertsFromEquipmentAnalysis:
    """Test alert generation from equipment analysis"""

    def test_critical_failure_risk_generates_alert(self):
        """Test that critical equipment failure risk generates alerts"""
        with patch.object(IoTAnalyzer, '__init__', lambda x: None):
            analyzer = IoTAnalyzer()
            analyzer.alert_manager = get_alert_manager()

        # Create equipment with high failure risk
        equipment = EquipmentSensor(sensor_id="eq_001", equipment_type="Excavator")
        equipment.condition = EquipmentCondition.DEGRADED
        equipment.failure_probability = 0.7  # 70% failure risk
        equipment.estimated_downtime_hours = 48

        with patch.object(analyzer.alert_manager, 'create_and_send_alert') as mock_alert:
            analyzer.analyze_equipment_health("proj_001", equipment)
            
            # Should generate a critical alert
            assert mock_alert.called
            call_args = mock_alert.call_args
            assert call_args[1]['alert_type'] == AlertType.EQUIPMENT_FAILURE
            assert call_args[1]['severity'] == AlertSeverity.CRITICAL

    def test_high_failure_risk_generates_alert(self):
        """Test that high equipment failure risk generates alerts"""
        with patch.object(IoTAnalyzer, '__init__', lambda x: None):
            analyzer = IoTAnalyzer()
            analyzer.alert_manager = get_alert_manager()

        # Create equipment with high failure risk
        equipment = EquipmentSensor(sensor_id="eq_001", equipment_type="Excavator")
        equipment.condition = EquipmentCondition.DEGRADED
        equipment.failure_probability = 0.4  # 40% failure risk
        equipment.estimated_downtime_hours = 24

        with patch.object(analyzer.alert_manager, 'create_and_send_alert') as mock_alert:
            analyzer.analyze_equipment_health("proj_001", equipment)
            
            # Should generate HIGH severity alert
            assert mock_alert.called
            call_args = mock_alert.call_args
            assert call_args[1]['severity'] == AlertSeverity.HIGH

    def test_maintenance_urgency_generates_alert(self):
        """Test that urgent maintenance needs generate alerts"""
        with patch.object(IoTAnalyzer, '__init__', lambda x: None):
            analyzer = IoTAnalyzer()
            analyzer.alert_manager = get_alert_manager()

        # Create equipment needing urgent maintenance
        equipment = EquipmentSensor(sensor_id="eq_001", equipment_type="Compressor")
        equipment.condition = EquipmentCondition.OPERATIONAL
        equipment.failure_probability = 0.1
        equipment.maintenance_due_days = 2  # Due in 2 days - urgent!

        with patch.object(analyzer.alert_manager, 'create_and_send_alert') as mock_alert:
            analyzer.analyze_equipment_health("proj_001", equipment)
            
            # Should generate MAINTENANCE_URGENT alert
            assert mock_alert.called
            call_args = mock_alert.call_args
            assert call_args[1]['alert_type'] == AlertType.MAINTENANCE_URGENT

    def test_good_equipment_no_alert(self):
        """Test that well-maintained equipment doesn't generate alerts"""
        with patch.object(IoTAnalyzer, '__init__', lambda x: None):
            analyzer = IoTAnalyzer()
            analyzer.alert_manager = get_alert_manager()

        # Create healthy equipment
        equipment = EquipmentSensor(sensor_id="eq_001", equipment_type="Crane")
        equipment.condition = EquipmentCondition.OPERATIONAL
        equipment.failure_probability = 0.05  # 5% - very low risk
        equipment.maintenance_due_days = 30  # Not due soon

        with patch.object(analyzer.alert_manager, 'create_and_send_alert') as mock_alert:
            analyzer.analyze_equipment_health("proj_001", equipment)
            
            # Should NOT generate an alert
            assert not mock_alert.called


class TestAlertsFromActivityAnalysis:
    """Test alert generation from activity analysis"""

    def test_safety_violations_generate_alert(self):
        """Test that multiple safety violations generate alerts"""
        with patch.object(IoTAnalyzer, '__init__', lambda x: None):
            analyzer = IoTAnalyzer()
            analyzer.alert_manager = get_alert_manager()

        # Create activity with safety violations
        activity = SiteActivityMonitor()
        activity.safety_violation_count = 8  # More than 5
        activity.hazard_detected = True

        with patch.object(analyzer.alert_manager, 'create_and_send_alert') as mock_alert:
            analyzer.analyze_site_activity("proj_001", activity)
            
            # Should generate SAFETY_HAZARD alert
            assert mock_alert.called
            call_args = mock_alert.call_args
            assert call_args[1]['alert_type'] == AlertType.SAFETY_HAZARD
            assert call_args[1]['severity'] == AlertSeverity.HIGH

    def test_blocked_emergency_exits_critical_alert(self):
        """Test that blocked emergency exits generate CRITICAL alerts"""
        with patch.object(IoTAnalyzer, '__init__', lambda x: None):
            analyzer = IoTAnalyzer()
            analyzer.alert_manager = get_alert_manager()

        # Create activity with blocked exits
        activity = SiteActivityMonitor()
        activity.emergency_exits_clear = False
        activity.hazard_detected = True

        with patch.object(analyzer.alert_manager, 'create_and_send_alert') as mock_alert:
            analyzer.analyze_site_activity("proj_001", activity)
            
            # Should generate CRITICAL alert
            assert mock_alert.called
            call_args = mock_alert.call_args
            assert call_args[1]['severity'] == AlertSeverity.CRITICAL

    def test_missing_first_aid_generates_alert(self):
        """Test that missing/inaccessible first aid generates alerts"""
        with patch.object(IoTAnalyzer, '__init__', lambda x: None):
            analyzer = IoTAnalyzer()
            analyzer.alert_manager = get_alert_manager()

        # Create activity with first aid issue
        activity = SiteActivityMonitor()
        activity.first_aid_station_accessible = False
        activity.hazard_detected = True

        with patch.object(analyzer.alert_manager, 'create_and_send_alert') as mock_alert:
            analyzer.analyze_site_activity("proj_001", activity)
            
            # Should generate alert
            assert mock_alert.called
            call_args = mock_alert.call_args
            assert call_args[1]['severity'] == AlertSeverity.MEDIUM

    def test_high_worker_density_generates_alert(self):
        """Test that excessive worker density generates alerts"""
        with patch.object(IoTAnalyzer, '__init__', lambda x: None):
            analyzer = IoTAnalyzer()
            analyzer.alert_manager = get_alert_manager()

        # Create activity with high density
        activity = SiteActivityMonitor()
        activity.active_workers_count = 200  # More than 150
        activity.hazard_detected = True

        with patch.object(analyzer.alert_manager, 'create_and_send_alert') as mock_alert:
            analyzer.analyze_site_activity("proj_001", activity)
            
            # Should generate alert
            assert mock_alert.called
            call_args = mock_alert.call_args
            assert call_args[1]['severity'] == AlertSeverity.MEDIUM

    def test_restricted_area_breach_generates_alert(self):
        """Test that restricted area breaches generate alerts"""
        with patch.object(IoTAnalyzer, '__init__', lambda x: None):
            analyzer = IoTAnalyzer()
            analyzer.alert_manager = get_alert_manager()

        # Create activity with breach
        activity = SiteActivityMonitor()
        activity.restricted_area_breaches = 3  # Multiple breaches
        activity.hazard_detected = True

        with patch.object(analyzer.alert_manager, 'create_and_send_alert') as mock_alert:
            analyzer.analyze_site_activity("proj_001", activity)
            
            # Should generate alert
            assert mock_alert.called
            call_args = mock_alert.call_args
            assert call_args[1]['alert_type'] == AlertType.RESTRICTED_AREA_BREACH


class TestAlertsFromAirQualityAnalysis:
    """Test alert generation from air quality analysis"""

    def test_dust_storm_generates_critical_alert(self):
        """Test that dust storm conditions generate critical alerts"""
        with patch.object(IoTAnalyzer, '__init__', lambda x: None):
            analyzer = IoTAnalyzer()
            analyzer.alert_manager = get_alert_manager()

        # Create dust storm air quality
        air_quality = AirQualityMonitor()
        air_quality.pm25_ugm3 = 400  # > 300 - dust storm!

        with patch.object(analyzer.alert_manager, 'create_and_send_alert') as mock_alert:
            analyzer.analyze_air_quality("proj_001", air_quality)
            
            # Should generate CRITICAL alert
            assert mock_alert.called
            call_args = mock_alert.call_args
            assert call_args[1]['alert_type'] == AlertType.AIR_QUALITY
            assert call_args[1]['severity'] == AlertSeverity.CRITICAL

    def test_visibility_impact_generates_alert(self):
        """Test that visibility-impacting PM10 generates alerts"""
        with patch.object(IoTAnalyzer, '__init__', lambda x: None):
            analyzer = IoTAnalyzer()
            analyzer.alert_manager = get_alert_manager()

        # Create high PM10 air quality
        air_quality = AirQualityMonitor()
        air_quality.pm10_ugm3 = 250  # > 200 - visibility impact

        with patch.object(analyzer.alert_manager, 'create_and_send_alert') as mock_alert:
            analyzer.analyze_air_quality("proj_001", air_quality)
            
            # Should generate alert
            assert mock_alert.called
            call_args = mock_alert.call_args
            assert call_args[1]['severity'] == AlertSeverity.HIGH

    def test_unhealthy_aqi_generates_alert(self):
        """Test that unhealthy AQI generates alerts"""
        with patch.object(IoTAnalyzer, '__init__', lambda x: None):
            analyzer = IoTAnalyzer()
            analyzer.alert_manager = get_alert_manager()

        # Create unhealthy air quality
        air_quality = AirQualityMonitor()
        air_quality.air_quality_index = 200  # UNHEALTHY level

        with patch.object(analyzer.alert_manager, 'create_and_send_alert') as mock_alert:
            analyzer.analyze_air_quality("proj_001", air_quality)
            
            # Should generate alert
            assert mock_alert.called
            call_args = mock_alert.call_args
            assert call_args[1]['severity'] == AlertSeverity.HIGH

    def test_good_air_quality_no_alert(self):
        """Test that good air quality doesn't generate alerts"""
        with patch.object(IoTAnalyzer, '__init__', lambda x: None):
            analyzer = IoTAnalyzer()
            analyzer.alert_manager = get_alert_manager()

        # Create good air quality
        air_quality = AirQualityMonitor()
        air_quality.pm25_ugm3 = 20  # Good
        air_quality.pm10_ugm3 = 50  # Good
        air_quality.air_quality_index = 50  # GOOD

        with patch.object(analyzer.alert_manager, 'create_and_send_alert') as mock_alert:
            analyzer.analyze_air_quality("proj_001", air_quality)
            
            # Should NOT generate an alert
            assert not mock_alert.called


class TestAlertsFromIntelligenceGeneration:
    """Test alert generation from intelligence generation"""

    def test_work_stoppable_generates_critical_alert(self):
        """Test that work-stoppable conditions generate critical alerts"""
        with patch.object(IoTAnalyzer, '__init__', lambda x: None):
            analyzer = IoTAnalyzer()
            analyzer.alert_manager = get_alert_manager()

        # Set up conditions for work stoppable (high safety risk)
        weather = WeatherSnapshot()
        weather.condition = WeatherCondition.TORNADO
        weather.safety_level = SafetyLevel.CRITICAL

        equipment = EquipmentSensor(sensor_id="eq_001", equipment_type="Crane")
        equipment.condition = EquipmentCondition.CRITICAL
        equipment.failure_probability = 0.9

        activity = SiteActivityMonitor()
        activity.emergency_exits_clear = False

        with patch.object(analyzer.alert_manager, 'create_and_send_alert') as mock_alert:
            intelligence = analyzer.generate_real_time_intelligence(
                project_id="proj_001",
                weather=weather,
                equipment_sensors=[equipment],
                site_activity=activity,
            )

            # Should generate WORK_STOPPABLE alert
            assert mock_alert.called
            alerts = [call[1] for call in mock_alert.call_args_list]
            work_stoppable_alerts = [a for a in alerts if a.get('alert_type') == AlertType.WORK_STOPPABLE]
            assert len(work_stoppable_alerts) > 0


class TestAlertNotificationFlow:
    """Test alert notification flow through system"""

    def test_alert_notification_on_creation(self):
        """Test that alerts trigger notifications on creation"""
        from phase23_alert_service import AlertServiceManager

        manager = AlertServiceManager()

        with patch.object(manager.notification_service, 'send_notification') as mock_notify:
            alert = manager.create_and_send_alert(
                project_id="proj_001",
                alert_type=AlertType.EQUIPMENT_FAILURE,
                severity=AlertSeverity.CRITICAL,
                title="Critical Alert",
            )

            # Should attempt notifications
            assert mock_notify.called

    def test_escalation_triggers_more_notifications(self):
        """Test that escalating an alert triggers more notifications"""
        from phase23_alert_service import AlertServiceManager

        manager = AlertServiceManager()

        alert = manager.create_and_send_alert(
            project_id="proj_001",
            alert_type=AlertType.EQUIPMENT_FAILURE,
            severity=AlertSeverity.CRITICAL,
            title="Critical Alert",
        )

        with patch.object(manager.notification_service, 'send_notification') as mock_notify:
            escalated = manager.escalation_service.escalate_alert(alert)
            
            # Escalation should increase notification attempts
            assert escalated.notification_attempts > alert.notification_attempts

    def test_multiple_channels_for_critical_alerts(self):
        """Test that critical alerts use multiple notification channels"""
        from phase23_alert_service import get_alert_manager, NotificationChannel

        manager = get_alert_manager()

        with patch.object(manager.notification_service, 'send_notification') as mock_notify:
            alert = manager.create_and_send_alert(
                project_id="proj_001",
                alert_type=AlertType.EQUIPMENT_FAILURE,
                severity=AlertSeverity.CRITICAL,
                title="Critical Equipment Failure",
            )

            # Should attempt to send to multiple channels for critical alerts
            assert mock_notify.called
            # Should use Slack, SMS, and Email at minimum for critical alerts
            channels_used = [call[1]['channel'] for call in mock_notify.call_args_list if call[1]]
            assert len(set(channels_used)) >= 2


class TestAlertPersistence:
    """Test alert persistence and retrieval"""

    def test_alert_stored_after_creation(self):
        """Test that created alerts are stored"""
        from phase23_alert_service import get_alert_manager

        manager = get_alert_manager()
        manager.alert_store.clear_project_alerts("test_proj")

        with patch.object(manager.notification_service, 'send_notification'):
            alert = manager.create_and_send_alert(
                project_id="test_proj",
                alert_type=AlertType.SENSOR_ANOMALY,
                severity=AlertSeverity.HIGH,
                title="Test Alert",
            )

        # Retrieve and verify
        stored = manager.alert_store.get_alert(alert.alert_id)
        assert stored is not None
        assert stored.alert_id == alert.alert_id

    def test_alert_history_maintained(self):
        """Test that alert history is maintained"""
        from phase23_alert_service import get_alert_manager

        manager = get_alert_manager()
        manager.alert_store.clear_project_alerts("test_proj")

        with patch.object(manager.notification_service, 'send_notification'):
            # Create multiple alerts
            for i in range(3):
                manager.create_and_send_alert(
                    project_id="test_proj",
                    alert_type=AlertType.SENSOR_ANOMALY,
                    severity=AlertSeverity.HIGH,
                    title=f"Alert {i}",
                )

        # Retrieve all
        alerts = manager.get_alerts("test_proj")
        assert len(alerts) >= 3

    def test_acknowledged_alerts_tracked(self):
        """Test that acknowledgment is tracked"""
        from phase23_alert_service import get_alert_manager

        manager = get_alert_manager()

        with patch.object(manager.notification_service, 'send_notification'):
            alert = manager.create_and_send_alert(
                project_id="test_proj",
                alert_type=AlertType.SENSOR_ANOMALY,
                severity=AlertSeverity.HIGH,
                title="Test Alert",
            )

        # Acknowledge
        manager.acknowledge_alert("test_proj", alert.alert_id)

        # Check tracked
        stored = manager.alert_store.get_alert(alert.alert_id)
        assert stored.acknowledged_at is not None


class TestAlertEdgeCases:
    """Test edge cases and error handling"""

    def test_alert_with_missing_optional_fields(self):
        """Test creating alert with minimal required fields"""
        from phase23_alert_service import get_alert_manager

        manager = get_alert_manager()

        with patch.object(manager.notification_service, 'send_notification'):
            alert = manager.create_and_send_alert(
                project_id="proj_001",
                alert_type=AlertType.SENSOR_ANOMALY,
                severity=AlertSeverity.HIGH,
                title="Minimal Alert",
                # No description, sensor_id, equipment_id, etc.
            )

        assert alert is not None
        assert alert.title == "Minimal Alert"

    def test_alert_with_all_optional_fields(self):
        """Test creating alert with all fields"""
        from phase23_alert_service import get_alert_manager

        manager = get_alert_manager()

        with patch.object(manager.notification_service, 'send_notification'):
            alert = manager.create_and_send_alert(
                project_id="proj_001",
                alert_type=AlertType.EQUIPMENT_FAILURE,
                severity=AlertSeverity.CRITICAL,
                title="Full Alert",
                description="Complete description",
                sensor_id="sensor_001",
                equipment_id="equip_001",
                location="Site A, Building 2",
                recommended_action="Take immediate action",
            )

        assert alert is not None
        assert alert.sensor_id == "sensor_001"
        assert alert.equipment_id == "equip_001"
        assert alert.location == "Site A, Building 2"
        assert alert.recommended_action == "Take immediate action"

    def test_duplicate_alert_handling(self):
        """Test handling of duplicate/duplicate-like alerts"""
        from phase23_alert_service import get_alert_manager

        manager = get_alert_manager()
        manager.alert_store.clear_project_alerts("test_proj")

        with patch.object(manager.notification_service, 'send_notification'):
            # Create two similar alerts
            alert1 = manager.create_and_send_alert(
                project_id="test_proj",
                alert_type=AlertType.SENSOR_ANOMALY,
                severity=AlertSeverity.HIGH,
                title="Sensor Issue",
                sensor_id="sensor_001",
            )
            alert2 = manager.create_and_send_alert(
                project_id="test_proj",
                alert_type=AlertType.SENSOR_ANOMALY,
                severity=AlertSeverity.HIGH,
                title="Sensor Issue",
                sensor_id="sensor_001",
            )

        # Should have two distinct alerts (not deduplicated at alert level)
        alerts = manager.get_alerts("test_proj")
        assert len(alerts) >= 2
        assert alert1.alert_id != alert2.alert_id


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
