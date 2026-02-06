"""
Integration Tests for Phase 23 Real-Time IoT
Tests complete workflows, live sensor streams, and multi-sensor scenarios
"""
import pytest
from datetime import datetime, timedelta

from phase23_iot_analyzer import IoTAnalyzer
from phase23_iot_integration import create_iot_integration
from phase23_iot_types import (
    WeatherSnapshot,
    WeatherCondition,
    EquipmentSensor,
    SiteActivityMonitor,
    AirQualityMonitor,
    RealTimeSiteIntelligence,
)


class TestRealTimeSensorStreamProcessing:
    """Test processing of real-time sensor streams"""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer for tests"""
        return IoTAnalyzer()

    @pytest.fixture
    def integration(self):
        """Create integration for tests"""
        return create_iot_integration('proj-integration-test')

    def test_weather_stream_rain_escalation(self, analyzer):
        """Test weather risk escalation as rain increases"""
        analyzer_inst = IoTAnalyzer()

        # Light rain
        light_rain = WeatherSnapshot(
            location='site',
            weather_condition=WeatherCondition.LIGHT_RAIN,
            temperature_celsius=18,
            humidity_percent=70,
            wind_speed_kmh=15,
        )
        light_result = analyzer_inst.process_weather_snapshot(light_rain)

        # Moderate rain
        moderate_rain = WeatherSnapshot(
            location='site',
            weather_condition=WeatherCondition.MODERATE_RAIN,
            temperature_celsius=16,
            humidity_percent=80,
            wind_speed_kmh=25,
        )
        moderate_result = analyzer_inst.process_weather_snapshot(moderate_rain)

        # Heavy rain
        heavy_rain = WeatherSnapshot(
            location='site',
            weather_condition=WeatherCondition.HEAVY_RAIN,
            temperature_celsius=14,
            humidity_percent=90,
            wind_speed_kmh=35,
        )
        heavy_result = analyzer_inst.process_weather_snapshot(heavy_rain)

        # Verify escalation
        assert light_result.delay_risk_score < moderate_result.delay_risk_score
        assert moderate_result.delay_risk_score < heavy_result.delay_risk_score
        assert light_result.safety_risk_score < moderate_result.safety_risk_score
        assert moderate_result.safety_risk_score < heavy_result.safety_risk_score

    def test_equipment_degradation_over_time(self, analyzer):
        """Test equipment risk increases with age"""
        analyzer_inst = IoTAnalyzer()

        # New equipment
        new_eq = EquipmentSensor(
            equipment_id='crane-new',
            equipment_type='Crane',
            operating_hours_total=500,
            temperature_celsius=35,
            vibration_hz=10,
            maintenance_due_days=300,
        )
        new_result = analyzer_inst.analyze_equipment_health(new_eq)

        # Aged equipment
        aged_eq = EquipmentSensor(
            equipment_id='crane-aged',
            equipment_type='Crane',
            operating_hours_total=8000,
            temperature_celsius=45,
            vibration_hz=35,
            maintenance_due_days=7,
        )
        aged_result = analyzer_inst.analyze_equipment_health(aged_eq)

        # Verify risk increase
        assert new_result.health_score > aged_result.health_score
        assert new_result.failure_probability < aged_result.failure_probability

    def test_simultaneous_hazards_compound_risk(self, analyzer):
        """Test that multiple simultaneous hazards compound safety risk"""
        analyzer_inst = IoTAnalyzer()

        # Single hazard: Bad weather
        bad_weather = WeatherSnapshot(
            location='site',
            weather_condition=WeatherCondition.HEAVY_RAIN,
            temperature_celsius=10,
            humidity_percent=95,
            wind_speed_kmh=45,
        )
        weather_only = analyzer_inst.generate_real_time_intelligence(
            project_id='proj-hazard-1',
            weather=bad_weather,
        )

        # Multiple hazards: Weather + Activity hazard
        bad_activity = SiteActivityMonitor(
            active_workers_count=200,
            active_equipment_count=30,
            safety_violation_count=5,
            restricted_area_breaches=2,
            emergency_exits_clear=False,
        )
        weather_and_activity = analyzer_inst.generate_real_time_intelligence(
            project_id='proj-hazard-2',
            weather=bad_weather,
            activity=bad_activity,
        )

        # Multiple hazards should have higher overall risk
        assert weather_and_activity.overall_site_risk_score > weather_only.overall_site_risk_score

    def test_multi_equipment_health_aggregation(self, analyzer):
        """Test aggregation of multiple equipment health scores"""
        analyzer_inst = IoTAnalyzer()

        equipment_list = [
            EquipmentSensor(
                equipment_id='excavator-1',
                equipment_type='Excavator',
                operating_hours_total=2000,
                temperature_celsius=40,
                vibration_hz=15,
                maintenance_due_days=150,
            ),
            EquipmentSensor(
                equipment_id='excavator-2',
                equipment_type='Excavator',
                operating_hours_total=50,
                temperature_celsius=35,
                vibration_hz=5,
                maintenance_due_days=300,
            ),
            EquipmentSensor(
                equipment_id='crane-1',
                equipment_type='Crane',
                operating_hours_total=10000,
                temperature_celsius=60,
                vibration_hz=45,
                maintenance_due_days=3,
            ),
        ]

        intelligence = analyzer_inst.generate_real_time_intelligence(
            project_id='proj-multi-eq',
            equipment_list=equipment_list,
        )

        # Equipment at risk should be identified
        at_risk = sum(1 for eq in intelligence.active_equipment if eq.failure_probability > 0.3)
        assert at_risk > 0

        # Equipment risk score should reflect worst equipment
        assert intelligence.equipment_risk_score > 0.1

    def test_work_stoppability_threshold(self, analyzer):
        """Test work becomes stoppable at critical safety threshold"""
        analyzer_inst = IoTAnalyzer()

        # Safe weather
        safe_weather = WeatherSnapshot(
            location='site',
            weather_condition=WeatherCondition.SUNNY,
            temperature_celsius=25,
            humidity_percent=50,
            wind_speed_kmh=10,
        )
        safe_intel = analyzer_inst.generate_real_time_intelligence(
            project_id='proj-safe',
            weather=safe_weather,
        )
        assert not safe_intel.work_stoppable

        # Critical weather
        critical_weather = WeatherSnapshot(
            location='site',
            weather_condition=WeatherCondition.THUNDERSTORM,
            temperature_celsius=22,
            humidity_percent=95,
            wind_speed_kmh=80,
        )
        critical_intel = analyzer_inst.generate_real_time_intelligence(
            project_id='proj-critical',
            weather=critical_weather,
        )
        assert critical_intel.work_stoppable


class TestIntegrationWithCoreEngine:
    """Test integration with Feature 1 core risk engine"""

    @pytest.fixture
    def integration(self):
        """Create IoT integration"""
        return create_iot_integration('proj-core-integration')

    def test_risk_registration_flow(self, integration):
        """Test complete risk registration flow"""
        weather = WeatherSnapshot(
            location='site',
            weather_condition=WeatherCondition.MODERATE_RAIN,
            temperature_celsius=18,
        )

        equipment = EquipmentSensor(
            equipment_id='excavator-1',
            equipment_type='Excavator',
            operating_hours_total=5000,
            temperature_celsius=42,
            vibration_hz=20,
        )

        analyzer_inst = IoTAnalyzer()
        intelligence = analyzer_inst.generate_real_time_intelligence(
            project_id='proj-core-integration',
            weather=weather,
            equipment_list=[equipment],
        )

        # Register with integration
        risk_output = integration.register_iot_risk(intelligence)

        # Verify output format
        assert 'iot_overall_risk' in risk_output
        assert 'iot_delay_risk' in risk_output
        assert 'iot_safety_risk' in risk_output
        assert 'iot_equipment_risk' in risk_output
        assert 'iot_environmental_risk' in risk_output
        assert 'work_stoppable' in risk_output
        assert 'work_proceeding' in risk_output

    def test_core_engine_input_all_features(self, integration):
        """Test core engine input includes all necessary fields"""
        weather = WeatherSnapshot(
            location='site',
            weather_condition=WeatherCondition.CLOUDY,
            temperature_celsius=20,
        )

        activity = SiteActivityMonitor(
            active_workers_count=75,
            active_equipment_count=12,
        )

        air = AirQualityMonitor(
            air_quality_index=80,
            pm25_ugm3=25,
        )

        analyzer_inst = IoTAnalyzer()
        intelligence = analyzer_inst.generate_real_time_intelligence(
            project_id='proj-core-integration',
            task_id='task-abc-123',
            weather=weather,
            activity=activity,
            air_quality=air,
        )

        integration.register_iot_risk(intelligence)
        core_input = integration.get_core_engine_input()

        # Verify all required fields
        assert core_input['iot_component']['risk_score'] is not None
        assert core_input['work_stoppable'] is not None
        assert core_input['active_alerts'] is not None
        assert core_input['weather_condition'] is not None
        assert core_input['recommendations'] is not None

    def test_schedule_impact_integration(self, integration):
        """Test schedule impact calculation for Feature 2"""
        weather = WeatherSnapshot(
            location='site',
            weather_condition=WeatherCondition.HEAVY_RAIN,
            temperature_celsius=15,
        )

        analyzer_inst = IoTAnalyzer()
        intelligence = analyzer_inst.generate_real_time_intelligence(
            project_id='proj-core-integration',
            weather=weather,
        )

        integration.register_iot_risk(intelligence)

        # Get schedule impact
        delay_hours = integration.estimate_schedule_impact()

        assert delay_hours['estimated_delay_hours'] > 0
        assert delay_hours['work_availability_percent'] < 100

    def test_safety_constraints_to_workforce(self, integration):
        """Test safety constraints formatting for Feature 3 (Workforce)"""
        weather = WeatherSnapshot(
            location='site',
            weather_condition=WeatherCondition.EXTREME_HEAT,
            temperature_celsius=48,
        )

        analyzer_inst = IoTAnalyzer()
        intelligence = analyzer_inst.generate_real_time_intelligence(
            project_id='proj-core-integration',
            weather=weather,
        )

        integration.register_iot_risk(intelligence)

        # Get safety constraints
        constraints = integration.get_worker_safety_constraints()

        assert 'heat_protection' in constraints['required_ppe']
        assert constraints['max_work_hours'] < 8

    def test_equipment_constraints_to_equipment_feature(self, integration):
        """Test equipment availability for Feature 5 (Equipment)"""
        equipment_list = [
            EquipmentSensor(
                equipment_id='crane-1',
                equipment_type='Crane',
                operating_hours_total=12000,
                temperature_celsius=55,
                vibration_hz=45,
                maintenance_due_days=2,
            ),
        ]

        analyzer_inst = IoTAnalyzer()
        intelligence = analyzer_inst.generate_real_time_intelligence(
            project_id='proj-core-integration',
            equipment_list=equipment_list,
        )

        integration.register_iot_risk(intelligence)

        # Get equipment impact
        unavailable_count, risk_score = integration.get_equipment_availability_impact()

        assert risk_score > 0
        assert unavailable_count >= 0

    def test_compliance_to_compliance_feature(self, integration):
        """Test compliance status for Feature 7 (Compliance)"""
        air = AirQualityMonitor(
            air_quality_index=220,
            pm25_ugm3=160,
        )

        analyzer_inst = IoTAnalyzer()
        intelligence = analyzer_inst.generate_real_time_intelligence(
            project_id='proj-core-integration',
            air_quality=air,
        )

        integration.register_iot_risk(intelligence)

        # Get compliance
        compliance = integration.get_environmental_compliance_status()

        assert compliance['compliant'] == False
        assert compliance['violations_detected'] > 0


class TestMondayComIntegration:
    """Test monday.com board integration"""

    def test_monday_updates_generation(self):
        """Test monday.com update generation"""
        analyzer_inst = IoTAnalyzer()

        weather = WeatherSnapshot(
            location='site',
            weather_condition=WeatherCondition.MODERATE_RAIN,
            temperature_celsius=16,
            humidity_percent=80,
            wind_speed_kmh=25,
        )

        equipment = [
            EquipmentSensor(
                equipment_id='crane-1',
                equipment_type='Crane',
                operating_hours_total=4000,
                temperature_celsius=45,
                vibration_hz=20,
            ),
        ]

        activity = SiteActivityMonitor(
            active_workers_count=80,
            active_equipment_count=10,
        )

        intelligence = analyzer_inst.generate_real_time_intelligence(
            project_id='proj-monday',
            weather=weather,
            equipment_list=equipment,
            activity=activity,
        )

        # Get monday updates
        monday_updates = intelligence.monday_updates

        # Verify required fields
        assert 'Site Risk Level' in monday_updates
        assert 'Safety Status' in monday_updates
        assert 'Weather Condition' in monday_updates
        assert 'Active Alerts' in monday_updates

    def test_monday_updates_emoji_status(self):
        """Test monday.com includes emoji status indicators"""
        analyzer_inst = IoTAnalyzer()

        # Safe conditions
        safe_weather = WeatherSnapshot(
            location='site',
            weather_condition=WeatherCondition.SUNNY,
            temperature_celsius=25,
        )
        safe_intel = analyzer_inst.generate_real_time_intelligence(
            project_id='proj-monday-safe',
            weather=safe_weather,
        )
        safe_updates = safe_intel.monday_updates

        # Unsafe conditions
        unsafe_weather = WeatherSnapshot(
            location='site',
            weather_condition=WeatherCondition.THUNDERSTORM,
            temperature_celsius=20,
        )
        unsafe_intel = analyzer_inst.generate_real_time_intelligence(
            project_id='proj-monday-unsafe',
            weather=unsafe_weather,
        )
        unsafe_updates = unsafe_intel.monday_updates

        # Verify different statuses
        assert '🟢' in safe_updates.get('Site Risk Level', '')
        assert '🔴' in unsafe_updates.get('Site Risk Level', '')


class TestRealWorldScenarios:
    """Test realistic construction site scenarios"""

    def test_typical_good_weather_day(self):
        """Test typical good weather day operations"""
        analyzer_inst = IoTAnalyzer()

        weather = WeatherSnapshot(
            location='site',
            weather_condition=WeatherCondition.SUNNY,
            temperature_celsius=24,
            humidity_percent=45,
            wind_speed_kmh=12,
            rainfall_mm=0,
        )

        equipment = [
            EquipmentSensor(
                equipment_id='excavator-1',
                equipment_type='Excavator',
                operating_hours_total=2000,
                temperature_celsius=38,
                vibration_hz=12,
                maintenance_due_days=200,
            ),
            EquipmentSensor(
                equipment_id='crane-1',
                equipment_type='Crane',
                operating_hours_total=3500,
                temperature_celsius=42,
                vibration_hz=18,
                maintenance_due_days=150,
            ),
        ]

        activity = SiteActivityMonitor(
            active_workers_count=120,
            active_equipment_count=8,
            safety_violation_count=0,
            emergency_exits_clear=True,
            first_aid_station_accessible=True,
        )

        air = AirQualityMonitor(
            air_quality_index=45,
            pm25_ugm3=12,
        )

        intelligence = analyzer_inst.generate_real_time_intelligence(
            project_id='proj-good-day',
            weather=weather,
            equipment_list=equipment,
            activity=activity,
            air_quality=air,
        )

        # Verify conditions are safe for normal operations
        assert intelligence.overall_site_risk_score < 0.4
        assert not intelligence.work_stoppable
        assert intelligence.work_proceeding
        assert len(intelligence.alerts_active) == 0

    def test_deteriorating_weather_scenario(self):
        """Test scenario where weather deteriorates"""
        analyzer_inst = IoTAnalyzer()

        # Morning: Good
        morning_weather = WeatherSnapshot(
            location='site',
            weather_condition=WeatherCondition.SUNNY,
            temperature_celsius=22,
        )
        morning_intel = analyzer_inst.generate_real_time_intelligence(
            project_id='proj-weather-change',
            weather=morning_weather,
        )

        # Afternoon: Rain moving in
        afternoon_weather = WeatherSnapshot(
            location='site',
            weather_condition=WeatherCondition.LIGHT_RAIN,
            temperature_celsius=18,
        )
        afternoon_intel = analyzer_inst.generate_real_time_intelligence(
            project_id='proj-weather-change',
            weather=afternoon_weather,
        )

        # Evening: Heavy storm
        evening_weather = WeatherSnapshot(
            location='site',
            weather_condition=WeatherCondition.THUNDERSTORM,
            temperature_celsius=15,
        )
        evening_intel = analyzer_inst.generate_real_time_intelligence(
            project_id='proj-weather-change',
            weather=evening_weather,
        )

        # Verify deterioration
        assert morning_intel.overall_site_risk_score < afternoon_intel.overall_site_risk_score
        assert afternoon_intel.overall_site_risk_score < evening_intel.overall_site_risk_score
        assert not evening_intel.work_proceeding

    def test_emergency_response_scenario(self):
        """Test response to sudden hazardous conditions"""
        analyzer_inst = IoTAnalyzer()
        integration = create_iot_integration('proj-emergency')

        # Normal operations
        normal_conditions = WeatherSnapshot(
            location='site',
            weather_condition=WeatherCondition.CLOUDY,
            temperature_celsius=20,
        )
        normal_intel = analyzer_inst.generate_real_time_intelligence(
            project_id='proj-emergency',
            weather=normal_conditions,
        )
        integration.register_iot_risk(normal_intel)

        assert integration.current_intelligence.work_proceeding

        # Emergency: Extreme wind + equipment failure
        emergency_weather = WeatherSnapshot(
            location='site',
            weather_condition=WeatherCondition.EXTREME_WIND,
            temperature_celsius=22,
            wind_speed_kmh=80,
        )
        failed_equipment = [
            EquipmentSensor(
                equipment_id='crane-failing',
                equipment_type='Crane',
                operating_hours_total=15000,
                temperature_celsius=75,
                vibration_hz=200,
                maintenance_due_days=0,
            ),
        ]

        emergency_intel = analyzer_inst.generate_real_time_intelligence(
            project_id='proj-emergency',
            weather=emergency_weather,
            equipment_list=failed_equipment,
        )
        integration.register_iot_risk(emergency_intel)

        # Verify emergency response
        assert integration.current_intelligence.safety_risk_score > 0.8
        assert integration.current_intelligence.work_stoppable
        constraints = integration.get_worker_safety_constraints()
        assert not constraints['work_allowed']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
