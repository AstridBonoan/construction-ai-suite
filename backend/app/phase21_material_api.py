"""
Flask API endpoints for Phase 21: Material Ordering & Forecasting
"""
from flask import Blueprint, request, jsonify
from typing import Dict, Any
import logging
from phase21_material_types import (
    Material, SupplierInfo, StockRecord, DemandRecord, MaterialType, UnitType
)
from phase21_material_analyzer import MaterialOrderingAnalyzer
from phase21_material_integration import (
    feed_material_to_core_risk_engine, create_material_risk_update,
    create_material_risk_score_detail
)

logger = logging.getLogger(__name__)
blueprint = Blueprint('phase21_material', __name__, url_prefix='/api/phase21/material')

# Global analyzer instance
analyzer = MaterialOrderingAnalyzer()
last_intelligence = None


@blueprint.route('/analyze', methods=['POST'])
def analyze_material_ordering():
    """
    Analyze material ordering and forecasting for a project.
    
    Request body:
    {
      "project_id": "P001",
      "project_name": "Site A",
      "materials": [ {...} ],
      "suppliers": [ {...} ],
      "stock_records": [ {...} ],
      "demand_records": [ {...} ]
    }
    """
    try:
        data = request.get_json()
        project_id = data.get('project_id', 'unknown')
        project_name = data.get('project_name', 'Project')
        
        # Reset analyzer for fresh analysis
        global analyzer, last_intelligence
        analyzer = MaterialOrderingAnalyzer()
        
        # Register materials
        for mat_data in data.get('materials', []):
            material = Material(
                material_id=mat_data.get('material_id'),
                name=mat_data.get('name'),
                material_type=MaterialType[mat_data.get('material_type', 'OTHER').upper()],
                unit_type=UnitType[mat_data.get('unit_type', 'PIECES').upper()],
                standard_unit_quantity=mat_data.get('standard_unit_quantity', 1.0),
                cost_per_unit=mat_data.get('cost_per_unit', 0.0),
                description=mat_data.get('description', '')
            )
            analyzer.add_material(material)
        
        # Register suppliers
        for sup_data in data.get('suppliers', []):
            supplier = SupplierInfo(
                supplier_id=sup_data.get('supplier_id'),
                name=sup_data.get('name'),
                lead_time_days=sup_data.get('lead_time_days', 14),
                reliability_score=sup_data.get('reliability_score', 0.85),
                price_per_unit=sup_data.get('price_per_unit', 0.0),
                primary_materials=sup_data.get('primary_materials', []),
                notes=sup_data.get('notes', '')
            )
            analyzer.add_supplier(supplier)
        
        # Register stock records
        for stock_data in data.get('stock_records', []):
            stock = StockRecord(
                project_id=stock_data.get('project_id', project_id),
                material_id=stock_data.get('material_id'),
                quantity_on_hand=stock_data.get('quantity_on_hand', 0.0),
                quantity_on_order=stock_data.get('quantity_on_order', 0.0),
                reorder_point=stock_data.get('reorder_point', 0.0),
                last_updated=stock_data.get('last_updated', ''),
                supplier_id=stock_data.get('supplier_id', ''),
                notes=stock_data.get('notes', '')
            )
            analyzer.add_stock_record(stock)
        
        # Register demand records
        for demand_data in data.get('demand_records', []):
            demand = DemandRecord(
                project_id=demand_data.get('project_id', project_id),
                task_id=demand_data.get('task_id'),
                material_id=demand_data.get('material_id'),
                quantity_needed=demand_data.get('quantity_needed', 0.0),
                needed_by_date=demand_data.get('needed_by_date'),
                unit_type=UnitType[demand_data.get('unit_type', 'PIECES').upper()],
                task_duration_days=demand_data.get('task_duration_days', 1),
                flexibility_days=demand_data.get('flexibility_days', 0),
                notes=demand_data.get('notes', '')
            )
            analyzer.add_demand_record(demand)
        
        # Generate intelligence
        material_ids = [m.get('material_id') for m in data.get('materials', [])]
        intelligence = analyzer.create_project_material_intelligence(
            project_id, project_name, material_ids
        )
        last_intelligence = intelligence
        
        # Feed to core risk engine
        feed_material_to_core_risk_engine(intelligence)
        
        # Convert to JSON-serializable format
        response = {
            "project_id": intelligence.project_id,
            "project_name": intelligence.project_name,
            "material_summaries": {
                mid: {
                    "material_id": summary.material_id,
                    "material_name": summary.material_name,
                    "current_stock": summary.current_stock,
                    "stock_status": summary.stock_status.value,
                    "total_demand": summary.total_demand,
                    "consumption_rate_per_day": round(summary.consumption_rate_per_day, 3),
                    "days_of_supply": round(summary.days_of_supply, 1),
                    "forecast": {
                        "material_id": summary.forecast.material_id,
                        "predicted_shortage": summary.forecast.predicted_shortage,
                        "shortage_date": summary.forecast.shortage_date,
                        "days_until_shortage": summary.forecast.days_until_shortage,
                        "reorder_needed": summary.forecast.reorder_needed,
                        "reorder_quantity": round(summary.forecast.reorder_quantity, 1),
                        "reorder_urgency": summary.forecast.reorder_urgency.value,
                        "confidence": summary.forecast.confidence,
                        "explanation": summary.forecast.explanation,
                        "recommended_action": summary.forecast.recommended_action
                    } if summary.forecast else None,
                    "risks_count": len(summary.risks)
                }
                for mid, summary in intelligence.material_summaries.items()
            },
            "material_risk_insights": [
                {
                    "material_id": i.material_id,
                    "material_name": i.material_name,
                    "insight_type": i.insight_type,
                    "severity": i.severity,
                    "description": i.description,
                    "affected_tasks": i.affected_tasks,
                    "estimated_delay_days": i.estimated_delay_days,
                    "estimated_cost_impact": i.estimated_cost_impact,
                    "recommended_action": i.recommended_action
                }
                for i in intelligence.material_risk_insights
            ],
            "material_risk_score": round(intelligence.material_risk_score, 3),
            "project_summary": intelligence.project_summary,
            "critical_material_count": intelligence.critical_material_count,
            "schedule_impact_risk": round(intelligence.schedule_impact_risk, 3),
            "reorder_recommendations": intelligence.reorder_recommendations,
            "integration_ready": intelligence.integration_ready
        }
        
        return jsonify(response), 200
    
    except Exception as e:
        logger.error(f"Error in material analysis: {e}")
        return jsonify({"error": str(e)}), 500


@blueprint.route('/intelligence', methods=['GET'])
def get_material_intelligence():
    """Retrieve last calculated material intelligence"""
    if not last_intelligence:
        return jsonify({"error": "No intelligence available"}), 404
    
    return jsonify({
        "project_id": last_intelligence.project_id,
        "material_risk_score": round(last_intelligence.material_risk_score, 3),
        "critical_materials": last_intelligence.critical_material_count,
        "schedule_impact_risk": round(last_intelligence.schedule_impact_risk, 3)
    }), 200


@blueprint.route('/score-detail', methods=['GET'])
def get_score_detail():
    """Get detailed breakdown of material risk score"""
    if not last_intelligence:
        return jsonify({"error": "No intelligence available"}), 404
    
    detail = create_material_risk_score_detail(last_intelligence)
    return jsonify(detail), 200


@blueprint.route('/monday-mapping', methods=['GET'])
def get_monday_mapping():
    """Get material intelligence formatted for monday.com integration"""
    if not last_intelligence:
        return jsonify({"error": "No intelligence available"}), 404
    
    mapping = create_material_risk_update(last_intelligence)
    return jsonify(mapping), 200


@blueprint.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "ok", "service": "phase21_material_ordering"}), 200
