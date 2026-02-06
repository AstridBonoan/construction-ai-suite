"""
Material Ordering & Forecasting Analyzer for Phase 21
Implements demand forecasting, shortage prediction, and reorder recommendations
"""
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from phase21_material_types import (
    Material, SupplierInfo, StockRecord, DemandRecord, MaterialForecast,
    MaterialRiskInsight, MaterialHealthSummary, MaterialIntelligence,
    MaterialType, UnitType, StockStatus, ForecastUrgency
)


class MaterialOrderingAnalyzer:
    """Analyzer for material ordering, demand forecasting, and shortage detection"""
    
    def __init__(self):
        self.materials: Dict[str, Material] = {}
        self.suppliers: Dict[str, SupplierInfo] = {}
        self.stock_records: List[StockRecord] = []
        self.demand_records: List[DemandRecord] = []
        self.forecasts: Dict[str, MaterialForecast] = {}
    
    def add_material(self, material: Material) -> None:
        """Register a material"""
        self.materials[material.material_id] = material
    
    def add_supplier(self, supplier: SupplierInfo) -> None:
        """Register a supplier"""
        self.suppliers[supplier.supplier_id] = supplier
    
    def add_stock_record(self, stock: StockRecord) -> None:
        """Record current inventory level"""
        self.stock_records.append(stock)
    
    def add_demand_record(self, demand: DemandRecord) -> None:
        """Add predicted demand from a task"""
        self.demand_records.append(demand)
    
    def _get_stock_for_project_material(self, project_id: str, material_id: str) -> Optional[StockRecord]:
        """Retrieve stock record for project/material pair"""
        for record in self.stock_records:
            if record.project_id == project_id and record.material_id == material_id:
                return record
        return None
    
    def _get_demands_for_material(self, project_id: str, material_id: str) -> List[DemandRecord]:
        """Get all demand records for a material on a project"""
        return [d for d in self.demand_records 
                if d.project_id == project_id and d.material_id == material_id]
    
    def _calculate_consumption_rate(self, project_id: str, material_id: str) -> float:
        """
        Calculate expected consumption rate (units per day) based on task demands
        and scheduled dates
        """
        demands = self._get_demands_for_material(project_id, material_id)
        if not demands:
            return 0.0
        
        total_quantity = sum(d.quantity_needed for d in demands)
        
        # Parse earliest needed_by_date and latest to estimate duration
        earliest = min(parse_iso_date(d.needed_by_date) for d in demands)
        latest = max(parse_iso_date(d.needed_by_date) for d in demands)
        
        duration_days = (latest - earliest).days + 1
        if duration_days <= 0:
            duration_days = 1
        
        return total_quantity / duration_days
    
    def _predict_shortage_date(self, current_stock: float, consumption_rate: float,
                               lead_time_days: int, supplier_reliability: float) -> Optional[str]:
        """
        Predict when stock will run out, factoring in supplier reliability.
        Lower reliability → higher safety margin
        """
        if consumption_rate <= 0.0:
            return None
        
        days_until_empty = current_stock / consumption_rate
        
        # Apply supplier reliability discount: less reliable suppliers trigger earlier warning
        reliability_factor = 0.5 + (supplier_reliability * 0.5)  # 0.5-1.0
        adjusted_days = days_until_empty * reliability_factor
        
        if adjusted_days > lead_time_days * 2:  # Only flag if shortage is imminent
            return None
        
        shortage_date = datetime.now() + timedelta(days=adjusted_days)
        return shortage_date.date().isoformat()
    
    def _calculate_reorder_quantity(self, consumption_rate: float, lead_time_days: int,
                                     days_of_supply_target: float = 30.0) -> float:
        """
        Calculate optimal reorder quantity using Economic Order Quantity principles
        Targets: cover lead time + safety stock for 30 days
        """
        # Base reorder = consumption during lead time + buffer
        lead_time_demand = consumption_rate * lead_time_days
        safety_stock = consumption_rate * days_of_supply_target
        
        reorder_qty = lead_time_demand + safety_stock
        
        return max(0.0, reorder_qty)
    
    def calculate_material_forecast(self, project_id: str, material_id: str) -> MaterialForecast:
        """
        Calculate comprehensive forecast for a single material
        """
        material = self.materials.get(material_id)
        stock = self._get_stock_for_project_material(project_id, material_id)
        demands = self._get_demands_for_material(project_id, material_id)
        
        if not material or not stock:
            return MaterialForecast(
                material_id=material_id,
                project_id=project_id,
                material_name="Unknown",
                current_stock=0.0,
                explanation="Material or stock record not found"
            )
        
        consumption_rate = self._calculate_consumption_rate(project_id, material_id)
        supplier = self.suppliers.get(stock.supplier_id)
        lead_time = supplier.lead_time_days if supplier else 14
        reliability = supplier.reliability_score if supplier else 0.85
        
        shortage_date = self._predict_shortage_date(
            stock.quantity_on_hand, consumption_rate, lead_time, reliability
        )
        
        days_until_shortage = None
        if shortage_date:
            today = datetime.now().date()
            shortage_dt = datetime.fromisoformat(shortage_date)
            days_until_shortage = (shortage_dt.date() - today).days
        
        reorder_needed = (
            days_until_shortage is not None and days_until_shortage <= lead_time + 7
        )
        
        reorder_qty = self._calculate_reorder_quantity(consumption_rate, lead_time) if reorder_needed else 0.0
        
        # Determine urgency
        if days_until_shortage is None:
            urgency = ForecastUrgency.MINIMAL
        elif days_until_shortage < 0:
            urgency = ForecastUrgency.CRITICAL
        elif days_until_shortage <= lead_time:
            urgency = ForecastUrgency.HIGH
        elif days_until_shortage <= lead_time + 7:
            urgency = ForecastUrgency.MEDIUM
        else:
            urgency = ForecastUrgency.LOW
        
        explanation = self._generate_forecast_explanation(
            material.name, stock.quantity_on_hand, consumption_rate,
            lead_time, days_until_shortage, shortage_date, reliability
        )
        
        return MaterialForecast(
            material_id=material_id,
            project_id=project_id,
            material_name=material.name,
            current_stock=stock.quantity_on_hand,
            predicted_shortage=shortage_date is not None,
            shortage_date=shortage_date,
            days_until_shortage=days_until_shortage,
            reorder_needed=reorder_needed,
            reorder_quantity=reorder_qty,
            reorder_urgency=urgency,
            supplier_id=stock.supplier_id,
            supplier_lead_time_days=lead_time,
            confidence=0.85 if len(demands) > 2 else 0.6,
            explanation=explanation,
            recommended_action=self._generate_recommendation(
                material.name, reorder_qty, urgency, days_until_shortage
            ),
            explainability={
                "current_stock": stock.quantity_on_hand,
                "consumption_rate_daily": consumption_rate,
                "supplier_lead_time_days": lead_time,
                "supplier_reliability": reliability,
                "safety_stock_days": 30.0
            }
        )
    
    def _generate_forecast_explanation(self, material_name: str, current_stock: float,
                                       consumption_rate: float, lead_time: int,
                                       days_until_shortage: Optional[int], shortage_date: Optional[str],
                                       reliability: float) -> str:
        """Generate human-readable explanation of forecast"""
        if days_until_shortage is None:
            return f"{material_name}: Adequate stock available; no shortage predicted."
        
        if days_until_shortage < 0:
            return (f"{material_name}: CRITICAL - Stock has depleted or is depleting. "
                   f"Immediate reorder required. Last {current_stock:.1f} units available.")
        
        return (f"{material_name}: Stock will run out in ~{days_until_shortage} days "
               f"(predicted {shortage_date}). Current stock: {current_stock:.1f} units; "
               f"consumption rate: {consumption_rate:.2f} units/day. "
               f"Supplier {material_name} has {lead_time}-day lead time "
               f"(reliability: {reliability*100:.0f}%).")
    
    def _generate_recommendation(self, material_name: str, reorder_qty: float,
                                 urgency: ForecastUrgency, days_until_shortage: Optional[int]) -> str:
        """Generate procurement recommendation"""
        if urgency == ForecastUrgency.CRITICAL:
            return f"URGENT: Reorder {reorder_qty:.1f} units of {material_name} immediately."
        elif urgency == ForecastUrgency.HIGH:
            return f"Reorder {reorder_qty:.1f} units of {material_name} within 2-3 days."
        elif urgency == ForecastUrgency.MEDIUM:
            return f"Plan reorder of {reorder_qty:.1f} units of {material_name} within 1 week."
        else:
            return f"Monitor {material_name} stock; no immediate action required."
    
    def create_project_material_intelligence(
        self, project_id: str, project_name: str, material_ids: List[str]
    ) -> MaterialIntelligence:
        """
        Generate project-level material intelligence aggregating all materials
        """
        material_summaries: Dict[str, MaterialHealthSummary] = {}
        all_insights: List[MaterialRiskInsight] = []
        reorder_recs: List[Dict] = []
        critical_count = 0
        risk_scores = []
        
        for mat_id in material_ids:
            if mat_id not in self.materials:
                continue
            
            forecast = self.calculate_material_forecast(project_id, mat_id)
            material = self.materials[mat_id]
            stock = self._get_stock_for_project_material(project_id, mat_id)
            demands = self._get_demands_for_material(project_id, mat_id)
            
            # Determine stock status
            if stock:
                if stock.quantity_on_hand == 0:
                    status = StockStatus.OUT_OF_STOCK
                elif forecast.days_until_shortage is not None and forecast.days_until_shortage < 7:
                    status = StockStatus.CRITICAL
                elif forecast.days_until_shortage is not None and forecast.days_until_shortage < 14:
                    status = StockStatus.LOW
                else:
                    status = StockStatus.ADEQUATE
            else:
                status = StockStatus.OUT_OF_STOCK
            
            consumption_rate = self._calculate_consumption_rate(project_id, mat_id)
            days_of_supply = (stock.quantity_on_hand / consumption_rate) if consumption_rate > 0 else 999.0
            
            # Create risk insights for materials with shortages
            insights_for_material = []
            if forecast.predicted_shortage:
                insight = MaterialRiskInsight(
                    project_id=project_id,
                    material_id=mat_id,
                    material_name=material.name,
                    insight_type="shortage_risk",
                    severity="critical" if forecast.days_until_shortage is not None and forecast.days_until_shortage < 0 else "high",
                    description=forecast.explanation,
                    affected_tasks=[d.task_id for d in demands],
                    estimated_delay_days=max(0, (forecast.supplier_lead_time_days - (forecast.days_until_shortage or 0))),
                    recommended_action=forecast.recommended_action
                )
                insights_for_material.append(insight)
                all_insights.append(insight)
                critical_count += 1
            
            summary = MaterialHealthSummary(
                project_id=project_id,
                material_id=mat_id,
                material_name=material.name,
                current_stock=stock.quantity_on_hand if stock else 0.0,
                stock_status=status,
                total_demand=sum(d.quantity_needed for d in demands),
                consumption_rate_per_day=consumption_rate,
                days_of_supply=days_of_supply,
                forecast=forecast,
                risks=insights_for_material,
                generated_at=datetime.now().isoformat() + 'Z'
            )
            material_summaries[mat_id] = summary
            risk_scores.append(1.0 if forecast.predicted_shortage else 0.0)
            
            # Add to reorder recommendations
            if forecast.reorder_needed:
                reorder_recs.append({
                    "material_id": mat_id,
                    "material_name": material.name,
                    "reorder_quantity": forecast.reorder_quantity,
                    "reorder_urgency": forecast.reorder_urgency.value,
                    "reason": forecast.explanation,
                    "recommended_action": forecast.recommended_action
                })
        
        # Calculate project-level material risk score
        material_risk_score = sum(risk_scores) / len(risk_scores) if risk_scores else 0.0
        schedule_impact_risk = material_risk_score * 0.7  # Shortages have ~70% chance to delay
        
        project_summary = (
            f"Project '{project_name}' tracks {len(material_summaries)} material(s). "
            f"{critical_count} flagged with shortage risk. Overall material risk score: {material_risk_score:.2f}. "
            f"{len(reorder_recs)} reorder(s) recommended."
        )
        
        monday_updates = {
            "material_risk_score": f"{material_risk_score:.2f}",
            "critical_materials_count": str(critical_count),
            "reorders_needed": str(len(reorder_recs)),
            "schedule_impact_risk": f"{schedule_impact_risk:.2f}"
        }
        
        return MaterialIntelligence(
            project_id=project_id,
            project_name=project_name,
            material_summaries=material_summaries,
            material_risk_insights=all_insights,
            material_risk_score=material_risk_score,
            project_summary=project_summary,
            critical_material_count=critical_count,
            reorder_recommendations=reorder_recs,
            schedule_impact_risk=schedule_impact_risk,
            generated_at=datetime.now().isoformat() + 'Z',
            monday_updates=monday_updates
        )


def parse_iso_date(date_str: str) -> datetime:
    """Parse ISO date string to datetime"""
    try:
        return datetime.fromisoformat(date_str)
    except (ValueError, TypeError):
        return datetime.now()
