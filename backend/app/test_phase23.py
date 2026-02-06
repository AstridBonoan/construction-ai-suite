"""
Unit Tests for Phase 23 Real-Time IoT & Site Condition Intelligence
Tests analyzer, integration, and risk calculations with deterministic algorithms
"""
import pytest
from datetime import datetime
from unittest.mock import Mock, patch

from phase23_iot_analyzer import IoTAnalyzer
from phase23_iot_integration import IoTRiskIntegration, create_iot_integration
from phase23_iot_types import (
    WeatherSnapshot,
    WeatherCondition,
    EquipmentSensor,
    SiteActivityMonitor,
    AirQualityMonitor,
    RealTimeSiteIntelligence,
    SafetyLevel,
    SensorReading,
    SensorStatus,
    SensorType,
    EquipmentStatus,
)


class TestIoTAnalyzer:
    """Test IoT analyzer core functionality"""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance"""
        return IoTAnalyzer()

    def test_analyzer_initialization(self, analyzer):
        """Test analyzer initializes correctly"""
        assert analyzer is not None
        assert len(analyzer.sensor_readings_buffer) == 0

    def test_clear_weather_low_risk(self, analyzer):
        """Test clear weather produces minimal risk"""
        weather = WeatherSnapshot(
            location='site',
            weather_condition=WeatherCondition.CLEAR,
            temperature_celsius=20,
            humidity_percent=50,
            wind_speed_kmh=10,
        )

        result = analyzer.process_weather_snapshot(weather)

        assert result.delay_risk_score == 0.0
        assert result.safety_level == SafetyLevel.SAFE

    def test_heavy_rain_high_risk(self, analyzer):
        """Test heavy rain increases risk significantly"""
        weather = WeatherSnapshot(
            location='site',
            weather_condition=WeatherCondition.HEAVY_RAIN,
            temperature_celsius=20,
            humidity_percent=80,
            wind_speed_kmh=30,
        )

        result = analyzer.process_weather_snapshot(weather)

        assert result.delay_risk_score > 0.5
        assert result.safety_risk_score > 0.4

    def test_thunderstorm_critical_safety(self, analyzer):
        """Test thunderstorm is critical safety risk"""
        weather = WeatherSnapshot(
            location='site',
            weather_condition=WeatherCondition.THUNDERSTORM,
            temperature_celsius=20,
            humidity_percent=90,
            wind_speed_kmh=60,
        )

        result = analyzer.process_weather_snapshot(weather)

        assert result.safety_risk_score > 0.9
        assert result.safety_level == SafetyLevel.CRITICAL

    def test_extreme_heat_unsafe(self, analyzer):
        """Test extreme heat is unsafe"""
        weather = WeatherSnapshot(
            location='site',
            weather_condition=WeatherCondition.EXTREME_HEAT,
            temperature_celsius=50,
            humidity_percent=40,
            wind_speed_kmh=5,
        )

        result = analyzer.process_weather_snapshot(weather)

        assert result.safety_risk_score > 0.3

    def test_extreme_cold_unsafe(self, analyzer):
        """Test extreme cold is unsafe"""
        weather = WeatherSnapshot(
            location='site',
            weather_condition=WeatherCondition.EXTREME_COLD,
            temperature_celsius=-20,
            humidity_percent=60,
            wind_speed_kmh=20,
        )

        result = analyzer.process_weather_snapshot(weather)

        assert result.safety_risk_score > 0.3

    def test_extreme_wind_hazardous(self, analyzer):
        """Test extreme wind is hazardous"""
        weather = WeatherSnapshot(
            location='site',
            weather_condition=WeatherCondition.EXTREME_WIND,
            temperature_celsius=20,
            humidity_percent=50,
            wind_speed_kmh=70,
        )

        result = analyzer.process_weather_snapshot(weather)

        assert result.safety_risk_score > 0.8

    def test_equipment_healthy_low_risk(self, analyzer):
        """Test healthy equipment has low risk"""
        equipment = EquipmentSensor(
            equipment_id='crane-1',
            equipment_type='Crane',
            operating_hours_total=100,
            temperature_celsius=35,
            vibration_hz=10,
            maintenance_due_days=180,
        )

        result = analyzer.analyze_equipment_health(equipment)

        assert result.health_score > 0.8
        assert result.maintenance_risk_score < 0.2

    def test_equipment_high_hours_increased_risk(self, analyzer):
        """Test high operating hours increase maintenance risk"""
        equipment = EquipmentSensor(
            equipment_id='excavator-1',
            equipment_type='Excavator',
            operating_hours_total=12000,
            temperature_celsius=40,
            vibration_hz=25,
            maintenance_due_days=30,
        )

        result = analyzer.analyze_equipment_health(equipment)

        assert result.health_score < 0.7
        assert result.failure_probability > 0.1

    def test_equipment_overheating_risk(self, analyzer):
        """Test overheating equipment increases risk"""
        equipment = EquipmentSensor(
            equipment_id='diesel-gen',
            equipment_type='Generator',
            operating_hours_total=5000,
            temperature_celsius=95,
            vibration_hz=15,
            maintenance_due_days=60,
        )

        result = analyzer.analyze_equipment_health(equipment)

        assert result.health_score < 0.9

    def test_equipment_high_vibration_failure_risk(self, analyzer):
        """Test high vibration increases failure probability"""
        equipment = EquipmentSensor(
            equipment_id='pump-1',
            equipment_type='Pump',
            operating_hours_total=8000,
            temperature_celsius=40,
            vibration_hz=80,
            maintenance_due_days=14,
        )

        result = analyzer.analyze_equipment_health(equipment)

        assert result.failure_probability > 0.4

    def test_site_activity_safe_low_workers(self, analyzer):
        """Test low worker density is safe"""
        activity = SiteActivityMonitor(
            active_workers_count=10,
            active_equipment_count=5,
            safety_violation_count=0,
            restricted_area_breaches=0,
            emergency_exits_clear=True,
            first_aid_station_accessible=True,
        )

        result = analyzer.analyze_site_activity(activity)

        assert result.worker_proximity_risk_score < 0.3
        assert not result.hazard_detected

    def test_site_activity_crowded_hazard(self, analyzer):
        """Test high worker density is hazardous"""
        activity = SiteActivityMonitor(
            active_workers_count=250,
            active_equipment_count=20,
            safety_violation_count=8,
            restricted_area_breaches=2,
            emergency_exits_clear=True,
            first_aid_station_accessible=True,
        )

        result = analyzer.analyze_site_activity(activity)

        assert result.worker_proximity_risk_score > 0.5
        assert result.hazard_detected

    def test_site_activity_blocked_exits_critical(self, analyzer):
        """Test blocked emergency exits is critical"""
        activity = SiteActivityMonitor(
            active_workers_count=50,
            active_equipment_count=10,
            safety_violation_count=0,
            restricted_area_breaches=0,
            emergency_exits_clear=False,
            first_aid_station_accessible=True,
        )

        result = analyzer.analyze_site_activity(activity)

        assert result.hazard_detected
        assert 'exit' in result.hazard_description.lower()

    def test_air_quality_good(self, analyzer):
        """Test good air quality has low risk"""
        air = AirQualityMonitor(
            air_quality_index=40,
            pm25_ugm3=15,
            pm10_ugm3=25,
        )

        result = analyzer.analyze_air_quality(air)

        assert result.respiratory_risk_score < 0.2
        assert not result.dust_storm_risk

    def test_air_quality_unhealthy(self, analyzer):
        """Test unhealthy air quality increases risk"""
        air = AirQualityMonitor(
            air_quality_index=200,
            pm25_ugm3=150,
            pm10_ugm3=250,
        )

        result = analyzer.analyze_air_quality(air)

        assert result.respiratory_risk_score > 0.3

    def test_air_quality_dust_storm(self, analyzer):
        """Test dust storm detection"""
        air = AirQualityMonitor(
            air_quality_index=350,
            pm25_ugm3=320,
            pm10_ugm3=500,
        )

        result = analyzer.analyze_air_quality(air)

        assert result.dust_storm_risk

    def test_generate_real_time_intelligence_complete(self, analyzer):
        """Test complete intelligence generation with all components"""
        weather = WeatherSnapshot(
            location='site',
            weather_condition=WeatherCondition.CLOUDY,
            temperature_celsius=22,
            humidity_percent=60,
            wind_speed_kmh=15,
        )

        equipment_list = [
            EquipmentSensor(
                equipment_id='crane-1',
                equipment_type='Crane',
                operating_hours_total=2000,
                temperature_celsius=40,
                vibration_hz=15,
            ),
        ]

        activity = SiteActivityMonitor(
            active_workers_count=50,
            active_equipment_count=5,
            safety_violation_count=0,
            restricted_area_breaches=0,
        )

        air = AirQualityMonitor(
            air_quality_index=60,
            pm25_ugm3=20,
        )

        intelligence = analyzer.generate_real_time_intelligence(
            project_id='proj-123',
            weather=weather,
            equipment_list=equipment_list,
            activity=activity,
            air_quality=air,
        )

        assert intelligence.project_id == 'proj-123'
        assert 0 <= intelligence.overall_site_risk_score <= 1.0
        assert 0 <= intelligence.delay_risk_score <= 1.0
        assert 0 <= intelligence.safety_risk_score <= 1.0
        assert 0 <= intelligence.equipment_risk_score <= 1.0
        assert 0 <= intelligence.environmental_risk_score <= 1.0
        assert intelligence.work_proceeding == True

    def test_generate_intelligence_work_stopped(self, analyzer):
        """Test work stoppable when safety critical"""
        weather = WeatherSnapshot(
            location='site',
            weather_condition=WeatherCondition.THUNDERSTORM,
            temperature_celsius=20,
            humidity_percent=95,
            wind_speed_kmh=70,
        )

        intelligence = analyzer.generate_real_time_intelligence(
            project_id='proj-456',
            weather=weather,
        )

        assert intelligence.work_stoppable == True

    def test_sensor_anomaly_detection_outlier(self, analyzer):
        """Test anomaly detection for outlier values"""
        readings = [
            SensorReading(
                reading_id='r1',
                sensor_id='temp-1',
                reading_timestamp=datetime.now().isoformat(),
                value=20.0,
                unit='celsius',
            ),
            SensorReading(
                reading_id='r2',
                sensor_id='temp-1',
                reading_timestamp=datetime.now().isoformat(),
                value=21.0,
                unit='celsius',
            ),
            SensorReading(
                reading_id='r3',
                sensor_id='temp-1',
                reading_timestamp=datetime.now().isoformat(),
                value=19.5,
                unit='celsius',
            ),
            SensorReading(
                reading_id='r4',
                sensor_id='temp-1',
                reading_timestamp=datetime.now().isoformat(),
                value=85.0,  # Huge outlier
                unit='celsius',
            ),
        ]

        alerts = analyzer.detect_sensor_anomalies('temp-1', readings)

        assert len(alerts) > 0
        assert any(a.alert_type == 'anomaly' for a in alerts)

    def test_sensor_offline_alert(self, analyzer):
        """Test offline sensor detection"""
        readings = [
            SensorReading(
                reading_id='r1',
                sensor_id='wind-1',
                reading_timestamp=datetime.now().isoformat(),
                value=10.0,
                unit='kmh',
                status=SensorStatus.OFFLINE,
            ),
        ]

        alerts = analyzer.detect_sensor_anomalies('wind-1', readings)

        assert len(alerts) > 0
        assert any(a.alert_type == 'offline' for a in alerts)

    def test_sensor_low_battery(self, analyzer):
        """Test low battery detection"""
        readings = [
            SensorReading(
                reading_id='r1',
                sensor_id='humid-1',
                reading_timestamp=datetime.now().isoformat(),
                value=65.0,
                unit='percent',
                battery_level=5,
            ),
        ]

        alerts = analyzer.detect_sensor_anomalies('humid-1', readings)

        assert len(alerts) > 0
        assert any(a.alert_type == 'low_battery' for a in alerts)


class TestIoTIntegration:
    """Test IoT integration with core engine"""

    @pytest.fixture
    def integration(self):
        """Create integration instance"""
        return create_iot_integration('proj-test-123')

    def test_integration_creation(self, integration):
        """Test integration initializes correctly"""
        assert integration.project_id == 'proj-test-123'
        assert integration.current_intelligence is None

    def test_register_iot_risk(self, integration):
        """Test risk registration"""
        intelligence = RealTimeSiteIntelligence(
            intelligence_id='intel-1',
            project_id='proj-test-123',
            overall_site_risk_score=0.35,
            delay_risk_score=0.3,
            safety_risk_score=0.4,
            equipment_risk_score=0.2,
            environmental_risk_score=0.1,
        )

        result = integration.register_iot_risk(intelligence)

        assert result['iot_overall_risk'] == 0.35
        assert result['iot_delay_risk'] == 0.3
        assert result['iot_safety_risk'] == 0.4
        assert not result['work_stoppable']

    def test_core_engine_input_format(self, integration):
        """Test core engine input formatting"""
        intelligence = RealTimeSiteIntelligence(
            intelligence_id='intel-2',
            project_id='proj-test-123',
            weather_snapshot=WeatherSnapshot(
                location='site',
                weather_condition=WeatherCondition.CLOUDY,
                temperature_celsius=18,
            ),
        )
        integration.register_iot_risk(intelligence)

        core_input = integration.get_core_engine_input()

        assert 'iot_component' in core_input
        assert 'work_stoppable' in core_input
        assert 'timestamp' in core_input

    def test_weather_impact_on_schedule(self, integration):
        """Test weather schedule impact calculation"""
        weather = WeatherSnapshot(
            location='site',
            weather_condition=WeatherCondition.MODERATE_RAIN,
            temperature_celsius=15,
        )
        intelligence = RealTimeSiteIntelligence(
            intelligence_id='intel-3',
            project_id='proj-test-123',
            weather_snapshot=weather,
            delay_risk_score=0.6,
        )
        integration.register_iot_risk(intelligence)

        impact = integration.get_weather_impact_on_schedule()

        assert impact > 0

    def test_equipment_availability_impact(self, integration):
        """Test equipment availability calculation"""
        equipment = EquipmentSensor(
            equipment_id='excavator-1',
            equipment_type='Excavator',
        )
        intelligence = RealTimeSiteIntelligence(
            intelligence_id='intel-4',
            project_id='proj-test-123',
            active_equipment=[equipment],
            equipment_risk_score=0.4,
        )
        integration.register_iot_risk(intelligence)

        unavailable, risk = integration.get_equipment_availability_impact()

        assert risk == 0.4

    def test_worker_safety_constraints(self, integration):
        """Test worker safety constraints"""
        intelligence = RealTimeSiteIntelligence(
            intelligence_id='intel-5',
            project_id='proj-test-123',
            safety_risk_score=0.5,
        )
        integration.register_iot_risk(intelligence)

        constraints = integration.get_worker_safety_constraints()

        assert constraints['work_allowed'] == True
        assert constraints['safety_risk_score'] == 0.5

    def test_worker_constraints_extreme_cold(self, integration):
        """Test worker constraints with extreme cold"""
        weather = WeatherSnapshot(
            location='site',
            weather_condition=WeatherCondition.EXTREME_COLD,
            temperature_celsius=-15,
        )
        intelligence = RealTimeSiteIntelligence(
            intelligence_id='intel-6',
            project_id='proj-test-123',
            weather_snapshot=weather,
            safety_risk_score=0.6,
        )
        integration.register_iot_risk(intelligence)

        constraints = integration.get_worker_safety_constraints()

        assert 'cold_weather_gear' in constraints['required_ppe']
        assert constraints['max_work_hours'] == 4

    def test_worker_constraints_extreme_heat(self, integration):
        """Test worker constraints with extreme heat"""
        weather = WeatherSnapshot(
            location='site',
            weather_condition=WeatherCondition.EXTREME_HEAT,
            temperature_celsius=45,
        )
        intelligence = RealTimeSiteIntelligence(
            intelligence_id='intel-7',
            project_id='proj-test-123',
            weather_snapshot=weather,
        )
        integration.register_iot_risk(intelligence)

        constraints = integration.get_worker_safety_constraints()

        assert 'heat_protection' in constraints['required_ppe']

    def test_worker_constraints_high_wind(self, integration):
        """Test worker constraints restrict activities in high wind"""
        weather = WeatherSnapshot(
            location='site',
            weather_condition=WeatherCondition.EXTREME_WIND,
            temperature_celsius=20,
            wind_speed_kmh=60,
        )
        intelligence = RealTimeSiteIntelligence(
            intelligence_id='intel-8',
            project_id='proj-test-123',
            weather_snapshot=weather,
        )
        integration.register_iot_risk(intelligence)

        constraints = integration.get_worker_safety_constraints()

        assert 'crane_operations' in constraints['restricted_activities']
        assert 'high_elevation_work' in constraints['restricted_activities']

    def test_environmental_compliance_status(self, integration):
        """Test environmental compliance"""
        air = AirQualityMonitor(
            air_quality_index=80,
            pm25_ugm3=30,
        )
        intelligence = RealTimeSiteIntelligence(
            intelligence_id='intel-9',
            project_id='proj-test-123',
            air_quality=air,
        )
        integration.register_iot_risk(intelligence)

        compliance = integration.get_environmental_compliance_status()

        assert compliance['compliant'] == True
        assert compliance['air_quality_compliant'] == True

    def test_environmental_compliance_violation(self, integration):
        """Test compliance violation detection"""
        air = AirQualityMonitor(
            air_quality_index=200,
            pm25_ugm3=150,
        )
        intelligence = RealTimeSiteIntelligence(
            intelligence_id='intel-10',
            project_id='proj-test-123',
            air_quality=air,
        )
        integration.register_iot_risk(intelligence)

        compliance = integration.get_environmental_compliance_status()

        assert compliance['compliant'] == False
        assert compliance['air_quality_compliant'] == False

    def test_schedule_impact_estimation(self, integration):
        """Test schedule impact estimation"""
        intelligence = RealTimeSiteIntelligence(
            intelligence_id='intel-11',
            project_id='proj-test-123',
            delay_risk_score=0.5,
            equipment_risk_score=0.2,
        )
        integration.register_iot_risk(intelligence)

        impact = integration.estimate_schedule_impact()

        assert impact['estimated_delay_hours'] > 0
        assert impact['work_availability_percent'] < 100

    def test_intelligence_history(self, integration):
        """Test intelligence history tracking"""
        intel1 = RealTimeSiteIntelligence(
            intelligence_id='intel-h1',
            project_id='proj-test-123',
        )
        intel2 = RealTimeSiteIntelligence(
            intelligence_id='intel-h2',
            project_id='proj-test-123',
        )

        integration.register_iot_risk(intel1)
        integration.register_iot_risk(intel2)

        history = integration.get_intelligence_history()

        assert len(history) == 2

    def test_reset_project_state(self, integration):
        """Test project state reset"""
        intelligence = RealTimeSiteIntelligence(
            intelligence_id='intel-reset',
            project_id='proj-test-123',
        )
        integration.register_iot_risk(intelligence)

        integration.reset_project_state()

        assert integration.current_intelligence is None
        assert len(integration.intelligence_history) == 0


class TestRiskScoreConsistency:
    """Test risk score determinism and consistency"""

    def test_same_inputs_same_outputs(self):
        """Test deterministic risk calculation"""
        analyzer = IoTAnalyzer()

        # First calculation
        weather1 = WeatherSnapshot(
            location='site',
            weather_condition=WeatherCondition.HEAVY_RAIN,
            temperature_celsius=15,
            humidity_percent=85,
            wind_speed_kmh=40,
        )
        result1 = analyzer.process_weather_snapshot(weather1)

        # Second calculation with identical inputs
        weather2 = WeatherSnapshot(
            location='site',
            weather_condition=WeatherCondition.HEAVY_RAIN,
            temperature_celsius=15,
            humidity_percent=85,
            wind_speed_kmh=40,
        )
        result2 = analyzer.process_weather_snapshot(weather2)

        assert result1.delay_risk_score == result2.delay_risk_score
        assert result1.safety_risk_score == result2.safety_risk_score

    def test_risk_score_bounds(self):
        """Test all risk scores are bounded 0-1"""
        analyzer = IoTAnalyzer()

        # Extreme weather
        weather = WeatherSnapshot(
            location='site',
            weather_condition=WeatherCondition.THUNDERSTORM,
            temperature_celsius=-30,
            humidity_percent=100,
            wind_speed_kmh=150,
        )
        result = analyzer.process_weather_snapshot(weather)

        assert 0 <= result.delay_risk_score <= 1.0
        assert 0 <= result.safety_risk_score <= 1.0

        # High-stress equipment
        equipment = EquipmentSensor(
            equipment_id='eq-extreme',
            equipment_type='Type',
            operating_hours_total=100000,
            temperature_celsius=150,
            vibration_hz=500,
            maintenance_due_days=0,
        )
        eq_result = analyzer.analyze_equipment_health(equipment)

        assert 0 <= eq_result.health_score <= 1.0
        assert 0 <= eq_result.maintenance_risk_score <= 1.0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
