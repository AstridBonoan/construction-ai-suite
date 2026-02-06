"""
Data types for Phase 21: Automated Material Ordering & Forecasting
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional
from datetime import datetime


class MaterialType(Enum):
    """Categories of construction materials"""
    CONCRETE = "concrete"
    STEEL = "steel"
    LUMBER = "lumber"
    DRYWALL = "drywall"
    COPPER = "copper"
    ALUMINUM = "aluminum"
    INSULATION = "insulation"
    ROOFING = "roofing"
    PIPING = "piping"
    ELECTRICAL = "electrical"
    OTHER = "other"


class UnitType(Enum):
    """Units of measurement for materials"""
    METRIC_TONS = "metric_tons"
    CUBIC_METERS = "cubic_meters"
    LINEAR_METERS = "linear_meters"
    PIECES = "pieces"
    GALLONS = "gallons"
    LITERS = "liters"
    KILOGRAMS = "kilograms"
    SQUARE_METERS = "square_meters"


class StockStatus(Enum):
    """Status of material stock levels"""
    ADEQUATE = "adequate"
    LOW = "low"
    CRITICAL = "critical"
    OUT_OF_STOCK = "out_of_stock"


class ForecastUrgency(Enum):
    """Urgency level for reorder recommendations"""
    MINIMAL = "minimal"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Material:
    """Core material entity"""
    material_id: str
    name: str
    material_type: MaterialType
    unit_type: UnitType
    standard_unit_quantity: float = 1.0
    cost_per_unit: float = 0.0
    description: str = ""


@dataclass
class SupplierInfo:
    """Supplier details including reliability metrics"""
    supplier_id: str
    name: str
    lead_time_days: int
    reliability_score: float = 0.9  # 0.0-1.0; fraction of orders delivered on time
    price_per_unit: float = 0.0
    primary_materials: List[str] = field(default_factory=list)  # material_ids
    notes: str = ""


@dataclass
class StockRecord:
    """Current inventory level for a material on a project"""
    project_id: str
    material_id: str
    quantity_on_hand: float
    quantity_on_order: float = 0.0
    reorder_point: float = 0.0  # Minimum qty to trigger reorder
    last_updated: str = ""  # ISO datetime
    supplier_id: str = ""
    notes: str = ""


@dataclass
class DemandRecord:
    """Predicted demand for a material on a project"""
    project_id: str
    task_id: str
    material_id: str
    quantity_needed: float
    needed_by_date: str  # ISO date string
    unit_type: UnitType = UnitType.PIECES
    task_duration_days: int = 1
    flexibility_days: int = 0  # Days buffer before hard deadline
    notes: str = ""


@dataclass
class MaterialForecast:
    """Forecast of material supply/demand for a single material"""
    material_id: str
    project_id: str
    material_name: str
    current_stock: float
    predicted_shortage: bool = False
    shortage_date: Optional[str] = None  # ISO date when stock runs out
    days_until_shortage: Optional[int] = None
    reorder_needed: bool = False
    reorder_quantity: float = 0.0
    reorder_urgency: ForecastUrgency = ForecastUrgency.MINIMAL
    supplier_id: str = ""
    supplier_lead_time_days: int = 0
    confidence: float = 0.8  # 0.0-1.0 based on data completeness
    explanation: str = ""
    recommended_action: str = ""
    explainability: Dict[str, float] = field(default_factory=dict)


@dataclass
class MaterialRiskInsight:
    """Identified risk related to material shortage or supply"""
    project_id: str
    material_id: str
    material_name: str
    task_id: Optional[str] = None
    insight_type: str = "shortage_risk"  # shortage_risk, schedule_impact, cost_escalation
    severity: str = "medium"  # low, medium, high, critical
    description: str = ""
    affected_tasks: List[str] = field(default_factory=list)
    estimated_delay_days: float = 0.0
    estimated_cost_impact: float = 0.0  # USD
    recommended_action: str = ""


@dataclass
class MaterialHealthSummary:
    """Health summary for a single material in a project"""
    project_id: str
    material_id: str
    material_name: str
    current_stock: float
    stock_status: StockStatus = StockStatus.ADEQUATE
    total_demand: float = 0.0
    consumption_rate_per_day: float = 0.0
    days_of_supply: float = 999.0
    forecast: Optional[MaterialForecast] = None
    risks: List[MaterialRiskInsight] = field(default_factory=list)
    integration_ready: bool = True
    generated_at: str = ""


@dataclass
class MaterialIntelligence:
    """Project-level material ordering & forecasting intelligence"""
    project_id: str
    project_name: str
    material_summaries: Dict[str, MaterialHealthSummary] = field(default_factory=dict)
    material_risk_insights: List[MaterialRiskInsight] = field(default_factory=list)
    material_risk_score: float = 0.0  # 0.0-1.0 overall risk from material shortages
    project_summary: str = ""
    critical_material_count: int = 0
    reorder_recommendations: List[Dict] = field(default_factory=list)  # [{material_id, quantity, urgency, reason}]
    schedule_impact_risk: float = 0.0  # Probability that materials will delay project
    integration_ready: bool = True
    generated_at: str = ""
    monday_updates: Dict[str, str] = field(default_factory=dict)  # For monday mapping
