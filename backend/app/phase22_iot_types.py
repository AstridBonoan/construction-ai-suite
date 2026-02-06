"""Phase 22 - Real-Time IoT & Site Condition Intelligence (Simulated)

Type definitions for simulated IoT sensor data, environmental conditions,
and real-time risk amplification.

Status: Production-ready type definitions (demo/simulated data mode)
IMPORTANT: This phase uses SIMULATED IoT inputs - no actual hardware integration yet.
"""

from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import List, Literal, Optional
from datetime import datetime


@dataclass
class WeatherCondition:
    """Simulated weather telemetry."""
    timestamp: str  # ISO 8601
    temperature_f: float
    humidity_pct: float
    wind_speed_mph: float
    precipitation_mm: float
    condition: Literal['clear', 'cloudy', 'rainy', 'foggy', 'extreme']


@dataclass
class SiteActivitySignal:
    """Simulated site activity/occupancy telemetry."""
    timestamp: str  # ISO 8601
    area_id: str
    worker_count: int
    equipment_count: int
    activity_level: Literal['low', 'normal', 'high', 'peak']
    has_safety_hazards: bool


@dataclass
class EnvironmentalRisk:
    """Environmental risk assessment from conditions."""
    timestamp: str  # ISO 8601
    weather_risk: Literal['low', 'medium', 'high']  # rain, wind, temperature
    site_congestion_risk: Literal['low', 'medium', 'high']
    safety_incident_risk_pct: float  # probability of incident
    productivity_loss_factor: float  # 0-1 multiplier
    equipment_impact: str  # description
    worker_safety_impact: str  # description


@dataclass
class RealTimeProjectIntelligence:
    """Real-time synthesis of site conditions and risk amplification."""
    project_id: str
    analysis_datetime: str  # ISO 8601
    
    # Current conditions
    current_weather: WeatherCondition
    current_activity: SiteActivitySignal
    environmental_risk: EnvironmentalRisk
    
    # Risk amplification (how conditions amplify project-level risk)
    risk_amplification_factor: float  # 1.0 = baseline, >1.0 = amplified
    schedule_impact_days: float
    cost_impact_estimate: float
    
    # Summary and recommendations
    summary: str
    immediate_actions: List[str]
    confidence: Literal['high', 'medium', 'low']


def iot_to_dict(obj: object) -> dict:
    """Serialize Phase 22 dataclass to dict."""
    if isinstance(obj, (WeatherCondition, SiteActivitySignal, EnvironmentalRisk, RealTimeProjectIntelligence)):
        data = asdict(obj)
        if 'current_weather' in data and data['current_weather']:
            if not isinstance(data['current_weather'], dict):
                data['current_weather'] = asdict(data['current_weather'])
        if 'current_activity' in data and data['current_activity']:
            if not isinstance(data['current_activity'], dict):
                data['current_activity'] = asdict(data['current_activity'])
        if 'environmental_risk' in data and data['environmental_risk']:
            if not isinstance(data['environmental_risk'], dict):
                data['environmental_risk'] = asdict(data['environmental_risk'])
        return data
    raise TypeError(f"Cannot serialize {type(obj)}")
