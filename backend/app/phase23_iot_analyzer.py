"""
Real-Time IoT & Site Condition Analyzer for Phase 23
Processes live sensor data and detects unsafe/delay-prone conditions
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from statistics import mean, stdev
import logging

from phase23_iot_types import (
    SensorReading,
    WeatherSnapshot,
    WeatherCondition,
    EquipmentSensor,
    SiteActivityMonitor,
    AirQualityMonitor,
    RealTimeSiteIntelligence,
    SafetyLevel,
    AdaptiveAnomalyThreshold,
    SensorAlert,
    SensorStatus,
    EquipmentStatus,
)
from phase23_alert_service import (
    get_alert_manager,
    AlertType,
    AlertSeverity,
)

logger = logging.getLogger(__name__)


class IoTAnalyzer:
    """
    Analyzes real-time IoT sensor data for construction site conditions.
    Detects unsafe conditions and delay-prone situations with deterministic algorithms.
    """

    # Weather-based weather delay risk thresholds
    WEATHER_RISK_THRESHOLDS = {
        WeatherCondition.CLEAR: 0.0,
        WeatherCondition.SUNNY: 0.0,
        WeatherCondition.CLOUDY: 0.05,
        WeatherCondition.OVERCAST: 0.1,
        WeatherCondition.LIGHT_RAIN: 0.3,
        WeatherCondition.MODERATE_RAIN: 0.6,
        WeatherCondition.HEAVY_RAIN: 0.9,
        WeatherCondition.THUNDERSTORM: 0.95,
        WeatherCondition.SNOW: 0.85,
        WeatherCondition.SLEET: 0.9,
        WeatherCondition.HAIL: 0.95,
        WeatherCondition.FOG: 0.4,
        WeatherCondition.EXTREME_WIND: 0.85,
        WeatherCondition.EXTREME_HEAT: 0.5,
        WeatherCondition.EXTREME_COLD: 0.6,
    }

    # Temperature safety thresholds (Celsius)
    MIN_SAFE_TEMP = -10
    MAX_SAFE_TEMP = 45
    MIN_WORK_TEMP = 0
    MAX_WORK_TEMP = 40

    # Humidity safety threshold (%)
    MAX_HUMIDITY_PERCENT = 95

    # Wind speed threshold (km/h)
    MAX_SAFE_WIND_SPEED = 50

    # Air quality index thresholds
    AQI_SAFE = 50
    AQI_MODERATE = 100
    AQI_UNHEALTHY = 150

    def __init__(self, alert_manager=None):
        """Initialize analyzer"""
        self.sensor_readings_buffer: Dict[str, List[SensorReading]] = {}
        self.threshold_registry: Dict[str, AdaptiveAnomalyThreshold] = {}
        self.alert_history: Dict[str, List[SensorAlert]] = {}
        self.alert_manager = alert_manager or get_alert_manager()

    def process_weather_snapshot(self, weather: WeatherSnapshot) -> WeatherSnapshot:
        """
        Process weather data and calculate risk scores.

        Args:
            weather: WeatherSnapshot with current conditions

        Returns:
            Updated WeatherSnapshot with risk scores
        """
        # Calculate weather delay risk
        base_weather_risk = self.WEATHER_RISK_THRESHOLDS.get(weather.weather_condition, 0.3)

        # Temperature adjustment
        if weather.temperature_celsius < self.MIN_SAFE_TEMP or weather.temperature_celsius > self.MAX_SAFE_TEMP:
            base_weather_risk = min(base_weather_risk + 0.2, 1.0)

        # Wind speed adjustment
        if weather.wind_speed_kmh > self.MAX_SAFE_WIND_SPEED:
            base_weather_risk = min(base_weather_risk + 0.2, 1.0)

        # Humidity adjustment
        if weather.humidity_percent > self.MAX_HUMIDITY_PERCENT:
            base_weather_risk = min(base_weather_risk + 0.1, 1.0)

        weather.delay_risk_score = min(base_weather_risk, 1.0)

        # Calculate safety risk
        safety_risk = 0.0

        # Temperature extremes are unsafe
        if weather.temperature_celsius < self.MIN_SAFE_TEMP or weather.temperature_celsius > self.MAX_SAFE_TEMP:
            safety_risk = max(safety_risk, 0.7)

        # Lightning risk
        if weather.weather_condition == WeatherCondition.THUNDERSTORM:
            safety_risk = 0.95

        # Extreme wind is unsafe
        if weather.weather_condition == WeatherCondition.EXTREME_WIND:
            safety_risk = 0.85

        # Heavy precipitation increases slip risk
        if weather.weather_condition in [WeatherCondition.HEAVY_RAIN, WeatherCondition.SNOW, WeatherCondition.SLEET]:
            safety_risk = max(safety_risk, 0.6)

        # Ice/snow hazard
        if weather.weather_condition in [WeatherCondition.SNOW, WeatherCondition.SLEET, WeatherCondition.HAIL]:
            safety_risk = max(safety_risk, 0.5)

        weather.safety_risk_score = min(safety_risk, 1.0)

        # Determine safety level
        if weather.safety_risk_score > 0.8:
            weather.safety_level = SafetyLevel.CRITICAL
        elif weather.safety_risk_score > 0.6:
            weather.safety_level = SafetyLevel.HAZARDOUS
        elif weather.safety_risk_score > 0.4:
            weather.safety_level = SafetyLevel.WARNING
        elif weather.safety_risk_score > 0.2:
            weather.safety_level = SafetyLevel.CAUTION
        else:
            weather.safety_level = SafetyLevel.SAFE

        # Generate alerts for critical weather conditions
        if weather.safety_level == SafetyLevel.CRITICAL:
            self.alert_manager.create_and_send_alert(
                project_id="unknown",  # Will be set by caller
                alert_type=AlertType.WEATHER_CRITICAL,
                severity=AlertSeverity.CRITICAL,
                title=f"Critical Weather Alert: {weather.weather_condition.value}",
                description=f"Critical weather condition detected. Safety risk: {weather.safety_risk_score:.0%}",
                recommended_action="STOP all outdoor work immediately. Evacuate to safe shelter.",
                location=weather.location,
            )
        elif weather.safety_level == SafetyLevel.HAZARDOUS:
            self.alert_manager.create_and_send_alert(
                project_id="unknown",
                alert_type=AlertType.WEATHER_CRITICAL,
                severity=AlertSeverity.HIGH,
                title=f"Hazardous Weather Alert: {weather.weather_condition.value}",
                description=f"Hazardous weather condition detected. Safety risk: {weather.safety_risk_score:.0%}",
                recommended_action="Implement heightened safety measures. Monitor conditions closely.",
                location=weather.location,
            )

        # Generate explanation
        weather.explanation = self._generate_weather_explanation(weather)

        return weather

    def _generate_weather_explanation(self, weather: WeatherSnapshot) -> str:
        """Generate human-readable weather explanation"""
        parts = []

        if weather.safety_level == SafetyLevel.CRITICAL:
            parts.append(f"🚨 CRITICAL: {weather.weather_condition.value} detected - STOP OUTDOOR WORK")
        elif weather.safety_level == SafetyLevel.HAZARDOUS:
            parts.append(f"⚠️ HAZARDOUS: {weather.weather_condition.value} - HEIGHTENED PRECAUTIONS")
        elif weather.safety_level == SafetyLevel.WARNING:
            parts.append(f"⚠️ WARNING: {weather.weather_condition.value} - MONITOR CONDITIONS")
        else:
            parts.append(f"✅ Safe: {weather.weather_condition.value}")

        # Temperature info
        if weather.temperature_celsius < self.MIN_WORK_TEMP:
            parts.append(f"Temperature {weather.temperature_celsius}°C is below safe working range.")
        elif weather.temperature_celsius > self.MAX_WORK_TEMP:
            parts.append(f"Temperature {weather.temperature_celsius}°C is above safe working range.")

        # Wind info
        if weather.wind_speed_kmh > self.MAX_SAFE_WIND_SPEED:
            parts.append(f"Wind {weather.wind_speed_kmh} km/h exceeds safe limit.")

        # Humidity
        if weather.humidity_percent > self.MAX_HUMIDITY_PERCENT:
            parts.append(f"High humidity {weather.humidity_percent}% increases slip risk.")

        return " ".join(parts)

    def analyze_equipment_health(
        self,
        equipment: EquipmentSensor,
        historical_readings: Optional[List[SensorReading]] = None,
    ) -> EquipmentSensor:
        """
        Analyze equipment sensor data and calculate health/maintenance risk.

        Args:
            equipment: Equipment sensor data
            historical_readings: Optional historical vibration/temp readings

        Returns:
            Updated equipment with calculated risk scores
        """
        # Health score based on multiple factors
        health_score = 1.0

        # Operating hours impact
        if equipment.operating_hours_total > 10000:
            health_score *= 0.7
        elif equipment.operating_hours_total > 5000:
            health_score *= 0.85

        # Maintenance due
        if equipment.maintenance_due_days <= 30:
            health_score *= 0.6
        elif equipment.maintenance_due_days <= 90:
            health_score *= 0.8

        # Temperature impact (if available)
        if equipment.temperature_celsius is not None:
            if equipment.temperature_celsius > 80:
                health_score *= 0.7

        # Vibration impact
        if equipment.vibration_hz is not None:
            if equipment.vibration_hz > 50:  # High vibration = issues
                health_score *= 0.6
            elif equipment.vibration_hz > 30:
                health_score *= 0.8

        equipment.health_score = max(0.0, min(health_score, 1.0))

        # Calculate maintenance risk score
        maintenance_risk = 1.0 - equipment.health_score
        equipment.maintenance_risk_score = maintenance_risk

        # Estimate failure probability
        failure_probability = 0.0
        if equipment.health_score < 0.5:
            failure_probability = 0.8
        elif equipment.health_score < 0.7:
            failure_probability = 0.4
        elif equipment.health_score < 0.9:
            failure_probability = 0.1

        equipment.failure_probability = failure_probability

        # Estimate downtime if failure occurs
        if failure_probability > 0.1:
            equipment.estimated_downtime_hours = 24 * failure_probability

        # Generate alerts for high-risk equipment
        if failure_probability > 0.5:
            self.alert_manager.create_and_send_alert(
                project_id="unknown",
                alert_type=AlertType.EQUIPMENT_FAILURE,
                severity=AlertSeverity.CRITICAL,
                title=f"Critical Equipment Failure Risk: {equipment.equipment_id}",
                description=f"Equipment has {failure_probability:.0%} probability of failure. Health score: {equipment.health_score:.0%}",
                recommended_action=f"STOP operations immediately. Park equipment and conduct full inspection.",
                equipment_id=equipment.equipment_id,
            )
        elif failure_probability > 0.3:
            self.alert_manager.create_and_send_alert(
                project_id="unknown",
                alert_type=AlertType.EQUIPMENT_FAILURE,
                severity=AlertSeverity.HIGH,
                title=f"High Equipment Failure Risk: {equipment.equipment_id}",
                description=f"Equipment has {failure_probability:.0%} probability of failure.",
                recommended_action="Schedule maintenance inspection. Monitor equipment performance closely.",
                equipment_id=equipment.equipment_id,
            )

        # Maintenance urgency alert
        if equipment.maintenance_due_days <= 7:
            self.alert_manager.create_and_send_alert(
                project_id="unknown",
                alert_type=AlertType.MAINTENANCE_URGENT,
                severity=AlertSeverity.HIGH if equipment.maintenance_due_days <= 3 else AlertSeverity.MEDIUM,
                title=f"Urgent Maintenance Required: {equipment.equipment_id}",
                description=f"Maintenance is due in {equipment.maintenance_due_days} days.",
                recommended_action="Schedule maintenance immediately to prevent equipment failure.",
                equipment_id=equipment.equipment_id,
            )

        return equipment

    def analyze_site_activity(self, activity: SiteActivityMonitor) -> SiteActivityMonitor:
        """
        Analyze site activity for safety and operational risks.

        Args:
            activity: Site activity monitoring data

        Returns:
            Updated with risk scores
        """
        # Worker proximity risk
        proximity_risk = 0.0
        if activity.active_workers_count > 100:
            proximity_risk = 0.3
        if activity.active_workers_count > 200:
            proximity_risk = 0.6
        if activity.restricted_area_breaches > 0:
            proximity_risk = min(proximity_risk + 0.3, 1.0)
        if activity.equipment_concentration_risk > 0.5:
            proximity_risk = min(proximity_risk + 0.2, 1.0)

        activity.worker_proximity_risk_score = min(proximity_risk, 1.0)

        # Additional safety checks
        if activity.safety_violation_count > 5:
            activity.hazard_detected = True
            activity.hazard_description = f"{activity.safety_violation_count} safety violations detected"
            self.alert_manager.create_and_send_alert(
                project_id="unknown",
                alert_type=AlertType.SAFETY_HAZARD,
                severity=AlertSeverity.HIGH,
                title="Multiple Safety Violations Detected",
                description=f"{activity.safety_violation_count} safety violations detected on site.",
                recommended_action="Conduct safety briefing. Enforce compliance immediately.",
            )

        if not activity.emergency_exits_clear:
            activity.hazard_detected = True
            activity.hazard_description = "Emergency exits blocked - CRITICAL"
            self.alert_manager.create_and_send_alert(
                project_id="unknown",
                alert_type=AlertType.SAFETY_HAZARD,
                severity=AlertSeverity.CRITICAL,
                title="CRITICAL: Emergency Exits Blocked",
                description="Emergency exits are blocked or inaccessible.",
                recommended_action="Clear emergency exits immediately. This is a life safety violation.",
            )

        if not activity.first_aid_station_accessible:
            activity.hazard_detected = True
            self.alert_manager.create_and_send_alert(
                project_id="unknown",
                alert_type=AlertType.SAFETY_HAZARD,
                severity=AlertSeverity.MEDIUM,
                title="First Aid Station Not Accessible",
                description="First aid station is not accessible or available.",
                recommended_action="Open first aid station immediately.",
            )

        # Alert for high worker density
        if activity.active_workers_count > 150:
            self.alert_manager.create_and_send_alert(
                project_id="unknown",
                alert_type=AlertType.SAFETY_HAZARD,
                severity=AlertSeverity.MEDIUM,
                title="High Worker Density Alert",
                description=f"{activity.active_workers_count} workers on site. High density increases safety risks.",
                recommended_action="Monitor site activity closely. Deploy additional safety personnel.",
            )

        # Alert for restricted area breaches
        if activity.restricted_area_breaches > 0:
            self.alert_manager.create_and_send_alert(
                project_id="unknown",
                alert_type=AlertType.RESTRICTION_BREACH,
                severity=AlertSeverity.MEDIUM,
                title="Restricted Area Breach Detected",
                description=f"{activity.restricted_area_breaches} unauthorized access to restricted areas.",
                recommended_action="Review access control. Enforce restricted area policies.",
            )

        return activity

    def analyze_air_quality(self, air_quality: AirQualityMonitor) -> AirQualityMonitor:
        """
        Analyze air quality and calculate respiratory/visibility risk.

        Args:
            air_quality: Air quality data

        Returns:
            Updated with risk assessment
        """
        # Calculate respiratory risk from AQI
        respiratory_risk = 0.0
        if air_quality.air_quality_index > self.AQI_UNHEALTHY:
            respiratory_risk = min((air_quality.air_quality_index - self.AQI_UNHEALTHY) / 200.0, 1.0)
        elif air_quality.air_quality_index > self.AQI_MODERATE:
            respiratory_risk = min((air_quality.air_quality_index - self.AQI_MODERATE) / 50.0, 0.4)

        # PM2.5 additional risk
        if air_quality.pm25_ugm3 is not None and air_quality.pm25_ugm3 > 300:
            respiratory_risk = min(respiratory_risk + 0.3, 1.0)
            air_quality.dust_storm_risk = True
            self.alert_manager.create_and_send_alert(
                project_id="unknown",
                alert_type=AlertType.AIR_QUALITY,
                severity=AlertSeverity.CRITICAL,
                title="Dust Storm Alert",
                description=f"Dust storm detected. PM2.5: {air_quality.pm25_ugm3} µg/m³",
                recommended_action="Stop outdoor work immediately. Evacuate to sheltered areas. Provide respiratory protection.",
            )

        air_quality.respiratory_risk_score = min(respiratory_risk, 1.0)

        # Visibility impact (PM causes reduced visibility)
        if air_quality.pm10_ugm3 is not None and air_quality.pm10_ugm3 > 200:
            air_quality.visibility_impact = True
            self.alert_manager.create_and_send_alert(
                project_id="unknown",
                alert_type=AlertType.AIR_QUALITY,
                severity=AlertSeverity.HIGH,
                title="Reduced Visibility Alert",
                description=f"High PM10 level detected: {air_quality.pm10_ugm3} µg/m³. Visibility severely reduced.",
                recommended_action="Reduce equipment operation speed. Increase lighting. Position spotters.",
            )

        # General air quality alert
        if air_quality.air_quality_index > self.AQI_UNHEALTHY:
            self.alert_manager.create_and_send_alert(
                project_id="unknown",
                alert_type=AlertType.AIR_QUALITY,
                severity=AlertSeverity.HIGH,
                title="Unhealthy Air Quality Alert",
                description=f"Air quality index is {air_quality.air_quality_index}. Respiratory protection required.",
                recommended_action="Provide N95/P100 masks to all workers. Limit outdoor work duration to 4 hours maximum.",
            )

        return air_quality

    def generate_real_time_intelligence(
        self,
        project_id: str,
        task_id: Optional[str] = None,
        weather: Optional[WeatherSnapshot] = None,
        equipment_list: Optional[List[EquipmentSensor]] = None,
        activity: Optional[SiteActivityMonitor] = None,
        air_quality: Optional[AirQualityMonitor] = None,
    ) -> RealTimeSiteIntelligence:
        """
        Generate comprehensive real-time site intelligence.

        Args:
            project_id: Project identifier
            task_id: Optional task identifier
            weather: Current weather snapshot
            equipment_list: Active equipment with sensors
            activity: Site activity monitoring
            air_quality: Air quality data

        Returns:
            RealTimeSiteIntelligence with all integrated data and scores
        """
        intelligence = RealTimeSiteIntelligence(
            intelligence_id=f"intel_{project_id}_{datetime.now().isoformat()}",
            project_id=project_id,
            task_id=task_id,
            timestamp=datetime.now().isoformat(),
        )

        # Process weather
        if weather:
            intelligence.weather_snapshot = self.process_weather_snapshot(weather)
            intelligence.delay_risk_score = max(
                intelligence.delay_risk_score,
                intelligence.weather_snapshot.delay_risk_score
            )
            intelligence.safety_risk_score = max(
                intelligence.safety_risk_score,
                intelligence.weather_snapshot.safety_risk_score
            )

        # Process equipment
        if equipment_list:
            for eq in equipment_list:
                analyzed_eq = self.analyze_equipment_health(eq)
                intelligence.active_equipment.append(analyzed_eq)
                intelligence.equipment_risk_score = max(
                    intelligence.equipment_risk_score,
                    analyzed_eq.maintenance_risk_score
                )
                intelligence.delay_risk_score = max(
                    intelligence.delay_risk_score,
                    analyzed_eq.failure_probability * 0.3  # Equipment failure impacts schedule
                )

        # Process site activity
        if activity:
            intelligence.site_activity = self.analyze_site_activity(activity)
            intelligence.safety_risk_score = max(
                intelligence.safety_risk_score,
                intelligence.site_activity.worker_proximity_risk_score
            )

        # Process air quality
        if air_quality:
            intelligence.air_quality = self.analyze_air_quality(air_quality)
            intelligence.environmental_risk_score = intelligence.air_quality.respiratory_risk_score
            intelligence.safety_risk_score = max(
                intelligence.safety_risk_score,
                intelligence.air_quality.respiratory_risk_score
            )

        # Calculate overall site risk
        intelligence.overall_site_risk_score = (
            (intelligence.delay_risk_score * 0.25) +
            (intelligence.safety_risk_score * 0.40) +
            (intelligence.equipment_risk_score * 0.20) +
            (intelligence.environmental_risk_score * 0.15)
        )
        intelligence.overall_site_risk_score = min(intelligence.overall_site_risk_score, 1.0)

        # Determine work stoppability
        if intelligence.safety_risk_score > 0.8:
            intelligence.work_stoppable = True
            intelligence.work_proceeding = False
            self.alert_manager.create_and_send_alert(
                project_id=project_id,
                alert_type=AlertType.WORK_STOPPABLE,
                severity=AlertSeverity.CRITICAL,
                title="CRITICAL: Work Must Stop - Site Conditions Unsafe",
                description=f"Overall safety risk exceeds critical threshold. Safety risk score: {intelligence.safety_risk_score:.0%}",
                recommended_action="STOP ALL WORK IMMEDIATELY. Evacuate site if necessary. Contact emergency services if in danger.",
            )

        # Generate alerts
        intelligence.alerts_active = self._generate_alerts(intelligence)

        # Generate recommendations
        intelligence.recommendations = self._generate_recommendations(intelligence)

        # Generate summary
        intelligence.project_summary = self._generate_summary(intelligence)

        # Prepare monday.com updates
        intelligence.monday_updates = self._prepare_monday_updates(intelligence)

        return intelligence

    def _generate_alerts(self, intelligence: RealTimeSiteIntelligence) -> List[str]:
        """Generate active alerts based on current conditions"""
        alerts = []

        # Weather alerts
        if intelligence.weather_snapshot:
            if intelligence.weather_snapshot.safety_level.value == "critical":
                alerts.append("🚨 CRITICAL WEATHER: Work must stop immediately")
            elif intelligence.weather_snapshot.safety_level.value == "hazardous":
                alerts.append("⚠️ HAZARDOUS WEATHER: Enhanced safety protocols required")

        # Equipment alerts
        for eq in intelligence.active_equipment:
            if eq.failure_probability > 0.5:
                alerts.append(f"⚠️ EQUIPMENT {eq.equipment_id}: High failure risk")
            if eq.maintenance_due_days <= 7:
                alerts.append(f"🔧 MAINTENANCE: {eq.equipment_id} has urgent maintenance due")

        # Site activity alerts
        if intelligence.site_activity:
            if intelligence.site_activity.hazard_detected:
                alerts.append(f"🚨 HAZARD: {intelligence.site_activity.hazard_description}")
            if intelligence.site_activity.restricted_area_breaches > 0:
                alerts.append(f"⚠️ BREACH: {intelligence.site_activity.restricted_area_breaches} restricted area breaches")

        # Air quality alerts
        if intelligence.air_quality:
            if intelligence.air_quality.air_quality_index > self.AQI_UNHEALTHY:
                alerts.append("🌫️ AIR QUALITY: Unhealthy air detected - respiratory protection required")

        return alerts

    def _generate_recommendations(self, intelligence: RealTimeSiteIntelligence) -> List[str]:
        """Generate action recommendations"""
        recommendations = []

        # Safety-first recommendations
        if intelligence.safety_risk_score > 0.7:
            recommendations.append("STOP: Safety risk is critical - evacuate if necessary")
        elif intelligence.safety_risk_score > 0.5:
            recommendations.append("Halt: Implement heightened safety measures before proceeding")

        # Weather recommendations
        if intelligence.weather_snapshot:
            if intelligence.delay_risk_score > 0.7:
                recommendations.append("Consider rescheduling outside work to different time")
            if intelligence.weather_snapshot.temperature_celsius < self.MIN_WORK_TEMP:
                recommendations.append("Provide heated shelters for workers")
            if intelligence.weather_snapshot.temperature_celsius > self.MAX_WORK_TEMP:
                recommendations.append("Increase hydration breaks; provide cooling stations")

        # Equipment recommendations
        for eq in intelligence.active_equipment:
            if eq.maintenance_due_days <= 14:
                recommendations.append(f"Schedule maintenance for {eq.equipment_id} within 2 weeks")
            if eq.failure_probability > 0.3:
                recommendations.append(f"Park {eq.equipment_id} and assess for repairs")

        # Activity recommendations
        if intelligence.site_activity and intelligence.site_activity.active_workers_count > 150:
            recommendations.append("Worker density is high - monitor safety closely")

        if not recommendations:
            recommendations.append("✅ Conditions are acceptable; continue work with standard precautions")

        return recommendations

    def _generate_summary(self, intelligence: RealTimeSiteIntelligence) -> str:
        """Generate human-readable site summary"""
        parts = []

        # Status
        if intelligence.work_stoppable:
            parts.append("🛑 WORK STOPPED: Site conditions are unsafe")
        elif intelligence.work_proceeding:
            parts.append("✅ WORK PROCEEDING with conditions")

        # Summary for each component
        if intelligence.weather_snapshot:
            parts.append(f"Weather: {intelligence.weather_snapshot.weather_condition.value} ({intelligence.weather_snapshot.temperature_celsius}°C)")

        if intelligence.active_equipment:
            failed_count = sum(1 for eq in intelligence.active_equipment if eq.failure_probability > 0.5)
            parts.append(f"Equipment: {len(intelligence.active_equipment)} active, {failed_count} at risk")

        if intelligence.site_activity:
            parts.append(f"Workers: {intelligence.site_activity.active_workers_count} on site")

        # Overall risk
        risk_level = "LOW"
        if intelligence.overall_site_risk_score > 0.7:
            risk_level = "CRITICAL"
        elif intelligence.overall_site_risk_score > 0.5:
            risk_level = "HIGH"
        elif intelligence.overall_site_risk_score > 0.3:
            risk_level = "MEDIUM"

        parts.append(f"Overall Risk: {risk_level} ({intelligence.overall_site_risk_score:.0%})")

        return " | ".join(parts)

    def _prepare_monday_updates(self, intelligence: RealTimeSiteIntelligence) -> Dict[str, str]:
        """Prepare data for monday.com integration"""
        updates = {
            "Site Risk Level": self._get_risk_level_emoji(intelligence.overall_site_risk_score),
            "Safety Status": "🛑 STOP" if intelligence.work_stoppable else "✅ OK",
            "Weather Condition": intelligence.weather_snapshot.weather_condition.value if intelligence.weather_snapshot else "N/A",
            "Temperature": f"{intelligence.weather_snapshot.temperature_celsius}°C" if intelligence.weather_snapshot else "N/A",
            "Equipment Status": f"{len(intelligence.active_equipment)} operational",
            "Active Alerts": str(len(intelligence.alerts_active)),
            "Delay Risk": f"{intelligence.delay_risk_score:.0%}",
            "Safety Risk": f"{intelligence.safety_risk_score:.0%}",
            "Summary": intelligence.project_summary[:100],
        }
        return updates

    def _get_risk_level_emoji(self, score: float) -> str:
        """Convert risk score to emoji and text"""
        if score > 0.75:
            return "🔴 CRITICAL"
        elif score > 0.5:
            return "🟠 HIGH"
        elif score > 0.25:
            return "🟡 MEDIUM"
        else:
            return "🟢 LOW"

    def detect_sensor_anomalies(
        self,
        sensor_id: str,
        readings: List[SensorReading],
    ) -> List[SensorAlert]:
        """
        Detect anomalies in sensor readings using adaptive thresholding.

        Args:
            sensor_id: Sensor identifier
            readings: List of recent readings

        Returns:
            List of alerts for detected anomalies
        """
        alerts = []

        if len(readings) < 2:
            return alerts

        # Calculate statistics
        values = [r.value for r in readings]
        current_value = values[-1]

        try:
            mean_value = mean(values)
            std_dev = stdev(values) if len(values) > 1 else 0.0

            # Detect outliers (> 3 std devs from mean)
            if std_dev > 0 and abs(current_value - mean_value) > 3 * std_dev:
                alert = SensorAlert(
                    alert_id=f"anomaly_{sensor_id}_{datetime.now().isoformat()}",
                    project_id="unknown",
                    sensor_id=sensor_id,
                    alert_timestamp=readings[-1].reading_timestamp,
                    alert_type="anomaly",
                    severity="high",
                    value=current_value,
                    threshold=mean_value + 3 * std_dev,
                    description=f"Anomalous reading detected: {current_value}",
                )
                alerts.append(alert)
        except Exception as e:
            logger.warning(f"Error calculating sensor statistics: {str(e)}")

        # Check for offline
        if readings[-1].status == SensorStatus.OFFLINE:
            alert = SensorAlert(
                alert_id=f"offline_{sensor_id}_{datetime.now().isoformat()}",
                project_id="unknown",
                sensor_id=sensor_id,
                alert_timestamp=readings[-1].reading_timestamp,
                alert_type="offline",
                severity="critical",
                description="Sensor is offline",
            )
            alerts.append(alert)

        # Check for low battery
        if readings[-1].battery_level is not None and readings[-1].battery_level < 10:
            alert = SensorAlert(
                alert_id=f"battery_{sensor_id}_{datetime.now().isoformat()}",
                project_id="unknown",
                sensor_id=sensor_id,
                alert_timestamp=readings[-1].reading_timestamp,
                alert_type="low_battery",
                severity="high",
                value=readings[-1].battery_level,
                description=f"Low battery: {readings[-1].battery_level}%",
            )
            alerts.append(alert)

        return alerts
