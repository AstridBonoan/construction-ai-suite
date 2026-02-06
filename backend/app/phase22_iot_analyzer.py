"""Phase 22 - Real-Time IoT & Site Condition Analyzer (Simulated)

Analyzes simulated environmental conditions and amplifies project risk based
on real-time site conditions.

IMPORTANT: Demo mode uses SIMULATED sensor data - no real hardware integration.
"""

from __future__ import annotations
from datetime import datetime
import random

from phase22_iot_types import (
    WeatherCondition,
    SiteActivitySignal,
    EnvironmentalRisk,
    RealTimeProjectIntelligence,
)


class RealTimeSiteAnalyzer:
    """Analyzes site conditions and real-time risk amplification."""
    
    @staticmethod
    def generate_simulated_weather(timestamp: str = None) -> WeatherCondition:
        """Generate simulated weather data.
        
        Args:
            timestamp: ISO 8601 timestamp (defaults to now)
        
        Returns:
            WeatherCondition with simulated telemetry
        """
        if not timestamp:
            timestamp = datetime.now().isoformat()
        
        random.seed(hash(timestamp))
        
        # Simulate weather variations (typical range for construction)
        temp = random.uniform(50, 95)  # Fahrenheit
        humidity = random.uniform(30, 95)  # percent
        wind = random.uniform(0, 35)  # mph
        precip = random.uniform(0, 2)  # mm
        
        # Determine condition
        if precip > 1.0:
            condition = 'rainy'
        elif wind > 25:
            condition = 'extreme'
        elif humidity > 80:
            condition = 'foggy'
        elif random.random() > 0.6:
            condition = 'cloudy'
        else:
            condition = 'clear'
        
        return WeatherCondition(
            timestamp=timestamp,
            temperature_f=temp,
            humidity_pct=humidity,
            wind_speed_mph=wind,
            precipitation_mm=precip,
            condition=condition,
        )
    
    @staticmethod
    def generate_simulated_activity(timestamp: str = None) -> SiteActivitySignal:
        """Generate simulated site activity data.
        
        Args:
            timestamp: ISO 8601 timestamp (defaults to now)
        
        Returns:
            SiteActivitySignal with simulated occupancy/activity
        """
        if not timestamp:
            timestamp = datetime.now().isoformat()
        
        random.seed(hash(timestamp) + 1)
        
        # Simulate typical site activity
        workers = random.randint(5, 40)
        equipment = random.randint(2, 15)
        
        if workers > 30:
            activity = 'peak'
        elif workers > 20:
            activity = 'high'
        elif workers > 10:
            activity = 'normal'
        else:
            activity = 'low'
        
        hazards = random.random() > 0.8
        
        return SiteActivitySignal(
            timestamp=timestamp,
            area_id="SITE-01",
            worker_count=workers,
            equipment_count=equipment,
            activity_level=activity,
            has_safety_hazards=hazards,
        )
    
    @staticmethod
    def assess_environmental_risk(
        weather: WeatherCondition,
        activity: SiteActivitySignal,
    ) -> EnvironmentalRisk:
        """Assess risk from environmental conditions.
        
        Args:
            weather: Weather conditions
            activity: Site activity/occupancy
        
        Returns:
            EnvironmentalRisk with hazard assessment
        """
        timestamp = weather.timestamp
        
        # Weather risk
        if weather.condition in ['rainy', 'extreme']:
            weather_risk = 'high'
        elif weather.condition == 'foggy' or weather.wind_speed_mph > 20:
            weather_risk = 'medium'
        else:
            weather_risk = 'low'
        
        # Congestion risk
        if activity.activity_level == 'peak':
            congestion_risk = 'high'
        elif activity.activity_level in ['high', 'normal']:
            congestion_risk = 'medium'
        else:
            congestion_risk = 'low'
        
        # Safety incident probability (heuristic)
        base_prob = 5.0  # baseline 5% incident risk
        if weather_risk == 'high':
            base_prob *= 2.5
        elif weather_risk == 'medium':
            base_prob *= 1.5
        
        if congestion_risk == 'high':
            base_prob *= 1.8
        elif congestion_risk == 'medium':
            base_prob *= 1.3
        
        if activity.has_safety_hazards:
            base_prob *= 2.0
        
        safety_prob = min(80, base_prob)
        
        # Productivity loss (due to conditions and congestion)
        productivity_loss = 0
        if weather.condition == 'rainy':
            productivity_loss += 0.30
        if weather.condition == 'extreme':
            productivity_loss += 0.50
        if congestion_risk == 'high':
            productivity_loss += 0.15
        
        productivity_loss = min(1.0, productivity_loss)
        
        # Impacts
        equipment_impact = f"Weather: {weather.condition.title()} @ {weather.temperature_f:.0f}°F"
        if weather.wind_speed_mph > 20:
            equipment_impact += " | High wind may restrict crane/lift operations"
        if weather.precipitation_mm > 0.5:
            equipment_impact += " | Wet conditions reduce equipment traction and visibility"
        
        worker_impact = f"{activity.worker_count} workers on-site | Activity: {activity.activity_level.title()}"
        if activity.has_safety_hazards:
            worker_impact += " | ⚠️ Safety hazards present"
        if safety_prob > 10:
            worker_impact += f" | Incident risk elevated (~{safety_prob:.0f}%)"
        
        return EnvironmentalRisk(
            timestamp=timestamp,
            weather_risk=weather_risk,
            site_congestion_risk=congestion_risk,
            safety_incident_risk_pct=safety_prob,
            productivity_loss_factor=productivity_loss,
            equipment_impact=equipment_impact,
            worker_safety_impact=worker_impact,
        )
    
    @staticmethod
    def real_time_intelligence(
        project_id: str,
        weather: WeatherCondition,
        activity: SiteActivitySignal,
        environmental_risk: EnvironmentalRisk,
    ) -> RealTimeProjectIntelligence:
        """Synthesize real-time project intelligence.
        
        Args:
            project_id: Project identifier
            weather: Current weather
            activity: Site activity
            environmental_risk: Risk assessment
        
        Returns:
            RealTimeProjectIntelligence with synthesis and actions
        """
        # Risk amplification factor (relative to baseline)
        base_amplification = 1.0
        
        if environmental_risk.weather_risk == 'high':
            base_amplification *= 2.0
        elif environmental_risk.weather_risk == 'medium':
            base_amplification *= 1.3
        
        if environmental_risk.site_congestion_risk == 'high':
            base_amplification *= 1.5
        elif environmental_risk.site_congestion_risk == 'medium':
            base_amplification *= 1.2
        
        amplification_factor = min(5.0, base_amplification)
        
        # Schedule and cost impacts
        schedule_days = amplification_factor * 0.5  # rough estimate
        cost_impact = amplification_factor * 5000  # rough estimate
        
        # Summary
        summary_parts = [
            f"Weather: {weather.condition.title()} ({weather.temperature_f:.0f}°F, {weather.humidity_pct:.0f}% humidity)",
            f"Activity: {activity.activity_level.title()} ({activity.worker_count} workers, {activity.equipment_count} equipment)",
            f"Risk Amplification: {amplification_factor:.1f}x baseline",
        ]
        summary = " | ".join(summary_parts)
        
        # Immediate actions
        immediate_actions = []
        if environmental_risk.weather_risk == 'high':
            immediate_actions.append("Consider halting exposed work; high weather hazard")
            immediate_actions.append("Increase safety monitoring and incident response readiness")
        elif environmental_risk.weather_risk == 'medium':
            immediate_actions.append("Monitor weather; prepare for potential slowdowns")
        
        if environmental_risk.site_congestion_risk == 'high':
            immediate_actions.append("Stagger breaks/shifts to reduce crowding")
            immediate_actions.append("Increase traffic control and zone management")
        
        if activity.has_safety_hazards:
            immediate_actions.append("ALERT: Safety hazards detected - escalate to safety officer")
        
        if not immediate_actions:
            immediate_actions.append("Conditions normal; continue standard operations")
        
        return RealTimeProjectIntelligence(
            project_id=project_id,
            analysis_datetime=datetime.now().isoformat(),
            current_weather=weather,
            current_activity=activity,
            environmental_risk=environmental_risk,
            risk_amplification_factor=amplification_factor,
            schedule_impact_days=schedule_days,
            cost_impact_estimate=cost_impact,
            summary=summary,
            immediate_actions=immediate_actions,
            confidence='high',
        )
