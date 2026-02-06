"""
Real-Time IoT Integration with Core Risk Engine for Phase 23
Bridges IoT sensor data and site intelligence into project risk calculations
"""
from datetime import datetime
from typing import Dict, Optional, List, Tuple
import logging

from phase23_iot_analyzer import IoTAnalyzer
from phase23_iot_types import RealTimeSiteIntelligence, SensorAlert

logger = logging.getLogger(__name__)


class IoTRiskIntegration:
    """
    Integrates real-time IoT site intelligence with core project risk engine.
    Provides deterministic risk scoring and recommendations to Feature 1 (Core AI).
    """

    def __init__(self, project_id: str):
        """
        Initialize IoT integration for a project.

        Args:
            project_id: Unique project identifier
        """
        self.project_id = project_id
        self.analyzer = IoTAnalyzer()
        self.current_intelligence: Optional[RealTimeSiteIntelligence] = None
        self.intelligence_history: List[RealTimeSiteIntelligence] = []
        self.active_alerts: Dict[str, SensorAlert] = {}
        self.risk_cache: Dict[str, float] = {}

    def register_iot_risk(
        self,
        iot_intelligence: RealTimeSiteIntelligence,
    ) -> Dict[str, float]:
        """
        Register IoT-derived risk scores with core engine.
        This is the primary integration point for Feature 1 (Core AI Risk Engine).

        Args:
            iot_intelligence: Complete site intelligence from IoT sensors

        Returns:
            Dictionary of risk components for core engine integration:
            {
                'iot_overall_risk': 0.0-1.0,
                'iot_delay_risk': 0.0-1.0,
                'iot_safety_risk': 0.0-1.0,
                'iot_equipment_risk': 0.0-1.0,
                'iot_environmental_risk': 0.0-1.0,
                'work_stoppable': bool,
                'work_proceeding': bool,
            }
        """
        # Store current intelligence
        self.current_intelligence = iot_intelligence
        self.intelligence_history.append(iot_intelligence)

        # Extract risk scores
        risk_output = {
            'iot_overall_risk': iot_intelligence.overall_site_risk_score,
            'iot_delay_risk': iot_intelligence.delay_risk_score,
            'iot_safety_risk': iot_intelligence.safety_risk_score,
            'iot_equipment_risk': iot_intelligence.equipment_risk_score,
            'iot_environmental_risk': iot_intelligence.environmental_risk_score,
            'work_stoppable': iot_intelligence.work_stoppable,
            'work_proceeding': iot_intelligence.work_proceeding,
        }

        # Cache for quick reference
        self.risk_cache = risk_output

        # Log integration
        logger.info(
            f"IoT Risk Registered for Project {self.project_id}: "
            f"Overall={risk_output['iot_overall_risk']:.2f}, "
            f"Delay={risk_output['iot_delay_risk']:.2f}, "
            f"Safety={risk_output['iot_safety_risk']:.2f}"
        )

        # Process alerts
        self._process_alerts(iot_intelligence.alerts_active)

        return risk_output

    def get_core_engine_input(self) -> Dict[str, any]:
        """
        Prepare IoT data for consumption by Feature 1 core risk engine.
        Maps IoT risks to the weighting model.

        Returns:
            Dictionary formatted for core engine calculate_project_risk()
        """
        if not self.current_intelligence:
            return self._get_default_iot_input()

        return {
            # Primary risk scores (0-1 scale)
            'iot_component': {
                'risk_score': self.current_intelligence.overall_site_risk_score,
                'delay_risk': self.current_intelligence.delay_risk_score,
                'safety_risk': self.current_intelligence.safety_risk_score,
                'equipment_risk': self.current_intelligence.equipment_risk_score,
                'environmental_risk': self.current_intelligence.environmental_risk_score,
            },

            # Flags for hard stops
            'work_stoppable': self.current_intelligence.work_stoppable,
            'work_proceeding': self.current_intelligence.work_proceeding,

            # Operational status
            'active_alerts': len(self.current_intelligence.alerts_active),
            'equipment_status': f"{len(self.current_intelligence.active_equipment)} operational",
            'site_activity_level': self.current_intelligence.site_activity.active_workers_count if self.current_intelligence.site_activity else 0,

            # Current conditions
            'weather_condition': self.current_intelligence.weather_snapshot.weather_condition.value if self.current_intelligence.weather_snapshot else None,
            'temperature_celsius': self.current_intelligence.weather_snapshot.temperature_celsius if self.current_intelligence.weather_snapshot else None,
            'air_quality_index': self.current_intelligence.air_quality.air_quality_index if self.current_intelligence.air_quality else None,

            # Summarization
            'project_summary': self.current_intelligence.project_summary,
            'recommendations': self.current_intelligence.recommendations,
            'timestamp': self.current_intelligence.timestamp,
        }

    def _get_default_iot_input(self) -> Dict[str, any]:
        """Get default IoT input when no intelligence available"""
        return {
            'iot_component': {
                'risk_score': 0.0,
                'delay_risk': 0.0,
                'safety_risk': 0.0,
                'equipment_risk': 0.0,
                'environmental_risk': 0.0,
            },
            'work_stoppable': False,
            'work_proceeding': True,
            'active_alerts': 0,
            'equipment_status': 'unknown',
            'site_activity_level': 0,
            'weather_condition': None,
            'temperature_celsius': None,
            'air_quality_index': None,
            'project_summary': 'No IoT data available',
            'recommendations': [],
            'timestamp': datetime.now().isoformat(),
        }

    def _process_alerts(self, alerts: List[str]) -> None:
        """
        Process active alerts and update internal alert tracking.

        Args:
            alerts: List of alert messages
        """
        for alert_msg in alerts:
            alert_id = f"alert_{len(self.active_alerts)}_{datetime.now().isoformat()}"
            # Track alerts for transmission to core engine
            logger.warning(f"Active Alert for {self.project_id}: {alert_msg}")

    def get_weather_impact_on_schedule(self) -> float:
        """
        Calculate weather impact on project schedule.
        Used by Feature 2 (Schedule Risk Module).

        Returns:
            Schedule impact score (0-1), where 1.0 = severe delay expected
        """
        if not self.current_intelligence or not self.current_intelligence.weather_snapshot:
            return 0.0

        # Weather delay risk directly impacts schedule
        weather = self.current_intelligence.weather_snapshot
        return weather.delay_risk_score

    def get_equipment_availability_impact(self) -> Tuple[int, float]:
        """
        Calculate equipment unavailability impact.
        Used by Feature 5 (Equipment Risk Module).

        Returns:
            Tuple of (unavailable_equipment_count, availability_risk_score)
        """
        if not self.current_intelligence:
            return (0, 0.0)

        unavailable = sum(
            1 for eq in self.current_intelligence.active_equipment
            if eq.failure_probability > 0.3
        )

        risk_score = self.current_intelligence.equipment_risk_score
        return (unavailable, risk_score)

    def get_worker_safety_constraints(self) -> Dict[str, any]:
        """
        Get worker safety constraints based on site conditions.
        Used by Feature 3 (Workforce Risk Module).

        Returns:
            Dictionary of safety constraints:
            {
                'work_allowed': bool,
                'max_work_hours': int,
                'required_ppe': List[str],
                'restricted_activities': List[str],
                'safety_risk_score': float,
            }
        """
        if not self.current_intelligence:
            return {
                'work_allowed': True,
                'max_work_hours': 8,
                'required_ppe': [],
                'restricted_activities': [],
                'safety_risk_score': 0.0,
            }

        constraints = {
            'work_allowed': not self.current_intelligence.work_stoppable,
            'max_work_hours': 8,
            'required_ppe': [],
            'restricted_activities': [],
            'safety_risk_score': self.current_intelligence.safety_risk_score,
        }

        # Adjust based on conditions
        if self.current_intelligence.weather_snapshot:
            weather = self.current_intelligence.weather_snapshot
            if weather.temperature_celsius < -10:
                constraints['required_ppe'].append('cold_weather_gear')
                constraints['max_work_hours'] = 4
            elif weather.temperature_celsius > 40:
                constraints['required_ppe'].append('heat_protection')
                constraints['max_work_hours'] = 6

            if weather.wind_speed_kmh > 50:
                constraints['restricted_activities'].append('crane_operations')
                constraints['restricted_activities'].append('high_elevation_work')

        if self.current_intelligence.air_quality:
            if self.current_intelligence.air_quality.air_quality_index > 200:
                constraints['required_ppe'].append('respiratory_protection')
                constraints['max_work_hours'] = 4

        if self.current_intelligence.safety_risk_score > 0.7:
            constraints['work_allowed'] = False

        return constraints

    def get_environmental_compliance_status(self) -> Dict[str, any]:
        """
        Get environmental compliance based on site conditions.
        Used by Feature 7 (Compliance Risk Module).

        Returns:
            Environmental compliance status
        """
        if not self.current_intelligence:
            return {
                'compliant': True,
                'air_quality_compliant': True,
                'noise_compliant': True,
                'dust_control_needed': False,
                'air_quality_index': None,
                'violations_detected': 0,
            }

        status = {
            'compliant': True,
            'air_quality_compliant': True,
            'noise_compliant': True,
            'dust_control_needed': False,
            'air_quality_index': None,
            'violations_detected': 0,
        }

        if self.current_intelligence.air_quality:
            air = self.current_intelligence.air_quality
            status['air_quality_index'] = air.air_quality_index
            if air.air_quality_index > 150:
                status['air_quality_compliant'] = False
                status['compliant'] = False
                status['violations_detected'] += 1
            if air.dust_storm_risk:
                status['dust_control_needed'] = True

        if self.current_intelligence.site_activity:
            if self.current_intelligence.site_activity.safety_violation_count > 0:
                status['violations_detected'] += self.current_intelligence.site_activity.safety_violation_count
                status['compliant'] = False

        return status

    def get_monday_com_updates(self) -> Dict[str, str]:
        """
        Get IoT data formatted for monday.com board updates.
        Integrates with Feature 3-7 monday.com mappings.

        Returns:
            Dictionary of column_name -> value for monday.com update
        """
        if not self.current_intelligence:
            return {}

        return self.current_intelligence.monday_updates

    def acknowledge_alert(self, sensor_id: str) -> bool:
        """
        Acknowledge/clear an active sensor alert.

        Args:
            sensor_id: Sensor that triggered alert

        Returns:
            True if alert was acknowledged
        """
        if sensor_id in self.active_alerts:
            self.active_alerts[sensor_id].acknowledged = True
            logger.info(f"Alert acknowledged for sensor {sensor_id}")
            return True
        return False

    def get_intelligence_history(self, limit: int = 100) -> List[RealTimeSiteIntelligence]:
        """
        Get historical intelligence records.

        Args:
            limit: Maximum records to return

        Returns:
            List of intelligence records sorted by timestamp (newest first)
        """
        return sorted(
            self.intelligence_history[-limit:],
            key=lambda x: x.timestamp,
            reverse=True
        )

    def estimate_schedule_impact(self) -> Dict[str, any]:
        """
        Estimate impact of current IoT conditions on project schedule.
        Used for Feature 2 (Schedule) integration.

        Returns:
            Schedule impact estimation
        """
        if not self.current_intelligence:
            return {
                'estimated_delay_hours': 0,
                'work_availability_percent': 100,
                'confidence': 'unknown',
            }

        # Calculate work availability based on conditions
        availability = 100.0

        # Weather impact
        if self.current_intelligence.weather_snapshot:
            availability -= self.current_intelligence.delay_risk_score * 50

        # Equipment impact
        if self.current_intelligence.equipment_risk_score > 0.3:
            availability -= self.current_intelligence.equipment_risk_score * 30

        # Safety impact (no work possible if safety critical)
        if not self.current_intelligence.work_proceeding:
            availability = 0.0

        # Estimate delay hours in 8-hour workday
        estimated_delay = (100 - availability) / 100 * 8

        return {
            'estimated_delay_hours': round(estimated_delay, 1),
            'work_availability_percent': max(0, min(100, availability)),
            'confidence': 'high' if self.current_intelligence else 'unknown',
            'contributing_factors': self.current_intelligence.recommendations if self.current_intelligence else [],
        }

    def reset_project_state(self) -> None:
        """Reset IoT tracking for project"""
        self.current_intelligence = None
        self.active_alerts.clear()
        self.risk_cache.clear()
        self.intelligence_history.clear()
        logger.info(f"IoT state reset for project {self.project_id}")


def create_iot_integration(project_id: str) -> IoTRiskIntegration:
    """
    Factory function to create IoT integration instance.

    Args:
        project_id: Project identifier

    Returns:
        Initialized IoTRiskIntegration instance
    """
    return IoTRiskIntegration(project_id)
