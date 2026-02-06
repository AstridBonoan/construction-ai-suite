"""
Data types for Phase 23: Real-Time IoT & Site Condition Intelligence
Comprehensive sensor, environmental, and site activity monitoring
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any
from datetime import datetime


class SensorType(Enum):
    """Types of IoT sensors"""
    WEATHER_STATION = "weather_station"
    TEMPERATURE = "temperature"
    HUMIDITY = "humidity"
    WIND_SPEED = "wind_speed"
    RAIN_GAUGE = "rain_gauge"
    VIBRATION = "vibration"
    MOTION = "motion"
    LIGHT = "light"
    AIR_QUALITY = "air_quality"
    EQUIPMENT_GPS = "equipment_gps"
    EQUIPMENT_VIBRATION = "equipment_vibration"
    WORKER_PROXIMITY = "worker_proximity"
    SITE_ACCESS = "site_access"
    POWER_MONITOR = "power_monitor"
    WATER_LEVEL = "water_level"
    DUST_MONITOR = "dust_monitor"


class SensorStatus(Enum):
    """Status of sensor operation"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    CALIBRATING = "calibrating"
    OFFLINE = "offline"
    LOW_BATTERY = "low_battery"


class WeatherCondition(Enum):
    """Weather classification"""
    CLEAR = "clear"
    SUNNY = "sunny"
    CLOUDY = "cloudy"
    OVERCAST = "overcast"
    LIGHT_RAIN = "light_rain"
    MODERATE_RAIN = "moderate_rain"
    HEAVY_RAIN = "heavy_rain"
    THUNDERSTORM = "thunderstorm"
    SNOW = "snow"
    SLEET = "sleet"
    HAIL = "hail"
    FOG = "fog"
    EXTREME_WIND = "extreme_wind"
    EXTREME_HEAT = "extreme_heat"
    EXTREME_COLD = "extreme_cold"


class SafetyLevel(Enum):
    """Site safety classification"""
    SAFE = "safe"
    CAUTION = "caution"
    WARNING = "warning"
    HAZARDOUS = "hazardous"
    CRITICAL = "critical"


class EquipmentStatus(Enum):
    """Equipment operational status"""
    OPERATING = "operating"
    IDLE = "idle"
    MAINTENANCE = "maintenance"
    MOVING = "moving"
    PARKED = "parked"
    ERROR = "error"
    OFFLINE = "offline"


@dataclass
class SensorMetadata:
    """Sensor configuration and metadata"""
    sensor_id: str
    sensor_type: SensorType
    sensor_name: str
    location: str
    project_id: str
    task_id: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    elevation: Optional[float] = None
    installation_date: str = ""
    calibration_date: str = ""
    manufacturer: str = ""
    model: str = ""
    accuracy: str = ""
    read_frequency_seconds: int = 60
    alert_threshold_high: Optional[float] = None
    alert_threshold_low: Optional[float] = None
    timezone: str = "UTC"
    monday_column_mapping: Dict[str, str] = field(default_factory=dict)
    active: bool = True
    notes: str = ""


@dataclass
class SensorReading:
    """Single sensor data point"""
    reading_id: str
    sensor_id: str
    project_id: str
    reading_timestamp: str  # ISO datetime
    value: float
    unit: str
    status: SensorStatus
    signal_strength: Optional[int] = None  # 0-100 for wireless
    battery_level: Optional[int] = None  # 0-100
    reading_confidence: float = 1.0  # 0.0-1.0
    flag_alert: bool = False
    alert_condition: Optional[str] = None
    raw_value: Optional[str] = None  # Raw data for debugging
    notes: str = ""


@dataclass
class WeatherSnapshot:
    """Current weather conditions at site"""
    snapshot_id: str
    project_id: str
    timestamp: str  # ISO datetime
    weather_condition: WeatherCondition
    temperature_celsius: float
    feel_temp_celsius: float
    humidity_percent: float
    wind_speed_kmh: float
    wind_direction_degrees: Optional[int] = None
    rainfall_mm: float = 0.0
    pressure_hpa: Optional[float] = None
    visibility_meters: Optional[int] = None
    uv_index: Optional[float] = None
    air_quality_index: Optional[int] = None
    dew_point_celsius: Optional[float] = None
    safety_level: SafetyLevel = SafetyLevel.SAFE
    delay_risk_score: float = 0.0  # 0-1: likelihood of weather delays
    safety_risk_score: float = 0.0  # 0-1: unsafe condition probability
    explanation: str = ""


@dataclass
class EquipmentSensor:
    """Real-time equipment health monitoring"""
    equipment_id: str
    project_id: str
    task_id: Optional[str] = None
    equipment_type: str = ""
    status: EquipmentStatus = EquipmentStatus.IDLE
    operating_hours_total: int = 0
    operating_hours_session: int = 0
    vibration_hz: Optional[float] = None
    vibration_status: SensorStatus = SensorStatus.ACTIVE
    temperature_celsius: Optional[float] = None
    gps_latitude: Optional[float] = None
    gps_longitude: Optional[float] = None
    idle_time_seconds: int = 0
    maintenance_due_days: int = 365
    fuel_level_percent: Optional[int] = None
    last_reading_timestamp: str = ""
    health_score: float = 1.0  # 0.0-1.0, 1.0=perfect
    maintenance_risk_score: float = 0.0  # 0.0-1.0
    failure_probability: float = 0.0  # 0.0-1.0
    estimated_downtime_hours: float = 0.0
    notes: str = ""


@dataclass
class SiteActivityMonitor:
    """Site activity and worker presence tracking"""
    activity_id: str
    project_id: str
    timestamp: str  # ISO datetime
    active_workers_count: int = 0
    activity_level: str = "normal"  # low, normal, high, extreme
    hazard_detected: bool = False
    hazard_description: str = ""
    restricted_area_breaches: int = 0
    safety_violation_count: int = 0
    equipment_concentration_risk: float = 0.0  # 0.0-1.0
    worker_proximity_risk_score: float = 0.0  # 0.0-1.0
    crowd_density_per_sqm: Optional[float] = None
    emergency_exits_clear: bool = True
    first_aid_station_accessible: bool = True
    safety_equipment_visible: bool = True
    notes: str = ""


@dataclass
class AirQualityMonitor:
    """Environmental air quality metrics"""
    reading_id: str
    project_id: str
    timestamp: str  # ISO datetime
    pm25_ugm3: Optional[float] = None  # PM2.5 micrograms/m³
    pm10_ugm3: Optional[float] = None  # PM10
    co2_ppm: Optional[float] = None
    co_ppm: Optional[float] = None
    no2_ppb: Optional[float] = None
    so2_ppb: Optional[float] = None
    o3_ppb: Optional[float] = None
    air_quality_index: int = 0  # 0-500
    health_advisory: str = "Good"  # Good, Moderate, USG, Unhealthy, Very Unhealthy, Hazardous
    respiratory_risk_score: float = 0.0  # 0.0-1.0
    visibility_impact: bool = False
    dust_storm_risk: bool = False


@dataclass
class IoTDataStream:
    """Real-time data stream representation"""
    stream_id: str
    project_id: str
    stream_name: str
    source_type: str  # "live", "simulated", "historical"
    sensors: List[str] = field(default_factory=list)  # sensor IDs
    status: str = "initializing"  # initializing, active, paused, error
    total_readings: int = 0
    last_reading_timestamp: Optional[str] = None
    reading_interval_seconds: int = 60
    buffer_size: int = 1000
    connected_sensors: int = 0
    offline_sensors: int = 0
    error_count: int = 0
    created_at: str = ""
    notes: str = ""


@dataclass
class RealTimeSiteIntelligence:
    """Aggregated real-time site intelligence"""
    intelligence_id: str
    project_id: str
    task_id: Optional[str] = None
    timestamp: str  # ISO datetime
    weather_snapshot: Optional[WeatherSnapshot] = None
    active_equipment: List[EquipmentSensor] = field(default_factory=list)
    site_activity: Optional[SiteActivityMonitor] = None
    air_quality: Optional[AirQualityMonitor] = None
    overall_site_risk_score: float = 0.0  # 0.0-1.0
    delay_risk_score: float = 0.0  # 0.0-1.0
    safety_risk_score: float = 0.0  # 0.0-1.0
    equipment_risk_score: float = 0.0  # 0.0-1.0
    environmental_risk_score: float = 0.0  # 0.0-1.0
    work_stoppable: bool = False
    work_proceeding: bool = True
    alerts_active: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    project_summary: str = ""
    monday_updates: Dict[str, Any] = field(default_factory=dict)
    integration_ready: bool = True


@dataclass
class AdaptiveAnomalyThreshold:
    """Adaptive thresholds for anomaly detection"""
    threshold_id: str
    sensor_id: str
    metric_name: str
    baseline_mean: float
    baseline_std_dev: float
    current_threshold_low: float
    current_threshold_high: float
    sensitivity_level: str = "medium"  # low, medium, high
    adaptive: bool = True
    moving_average_window: int = 10
    alert_on_breach: bool = True
    last_adjusted: str = ""


@dataclass
class SensorAlert:
    """Alert generated from sensor anomalies"""
    alert_id: str
    project_id: str
    sensor_id: str
    alert_timestamp: str  # ISO datetime
    alert_type: str  # threshold_breach, anomaly, offline, low_battery, etc.
    severity: str = "medium"  # low, medium, high, critical
    value: float = 0.0
    threshold: float = 0.0
    description: str = ""
    recommended_action: str = ""
    acknowledged: bool = False
    resolved: bool = False
    resolution_timestamp: Optional[str] = None
