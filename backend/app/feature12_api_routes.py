"""
Feature 12: Portfolio Intelligence - API Routes
REST API endpoints for portfolio aggregation, intelligence, and dashboards.
"""

from flask import Blueprint, request, jsonify
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

from feature12_portfolio_models import (
    ProjectSnapshot,
    PortfolioRiskExposure,
    DashboardDataContract,
    PortfolioViewType,
)
from feature12_aggregation_service import PortfolioAggregationService
from feature12_intelligence_engine import ExecutiveIntelligenceEngine
from feature12_integrations import (
    Feature9RiskIntegration,
    Feature10RecommendationsIntegration,
    Feature11AllocationIntegration,
    MondayComIntegrator,
    CrossFeatureIntegrator,
)

logger = logging.getLogger(__name__)

# Create Blueprint
portfolio_bp = Blueprint("portfolio", __name__, url_prefix="/api/portfolio")

# Initialize services
aggregation_service = PortfolioAggregationService()
intelligence_engine = ExecutiveIntelligenceEngine()


@portfolio_bp.route("/aggregate", methods=["POST"])
def aggregate_portfolio():
    """
    Aggregate project-level data into portfolio risk exposure.
    
    Request JSON:
    {
        "portfolio_id": "PORT001",
        "projects": [...ProjectSnapshot...],
        "view_type": "client|region|program|division|portfolio"
    }
    
    Response: PortfolioRiskExposure
    """
    
    try:
        data = request.get_json()
        
        portfolio_id = data.get("portfolio_id")
        projects_data = data.get("projects", [])
        view_type = data.get("view_type", "portfolio")
        
        if not portfolio_id:
            return jsonify({"error": "portfolio_id required"}), 400
        
        # Convert project data to ProjectSnapshot objects
        projects = [ProjectSnapshot(**p) for p in projects_data]
        
        # Aggregate
        exposure = aggregation_service.aggregate_portfolio(
            portfolio_id=portfolio_id,
            projects=projects,
            view_type=PortfolioViewType[view_type.upper()],
        )
        
        logger.info(f"Aggregated portfolio {portfolio_id}: risk_score={exposure.portfolio_risk_score:.2f}")
        
        # Convert to dict for JSON response
        return jsonify(exposure.__dict__), 200
    
    except Exception as e:
        logger.error(f"Error aggregating portfolio: {str(e)}")
        return jsonify({"error": str(e)}), 500


@portfolio_bp.route("/drivers", methods=["POST"])
def identify_risk_drivers():
    """
    Identify systemic risk drivers in portfolio.
    
    Request JSON:
    {
        "portfolio_id": "PORT001",
        "exposure": {...PortfolioRiskExposure...},
        "projects": [...ProjectSnapshot...]
    }
    
    Response: List[RiskDriver]
    """
    
    try:
        data = request.get_json()
        
        portfolio_id = data.get("portfolio_id")
        exposure_data = data.get("exposure")
        projects_data = data.get("projects", [])
        
        if not portfolio_id or not exposure_data:
            return jsonify({"error": "portfolio_id and exposure required"}), 400
        
        # Reconstruct objects
        exposure = PortfolioRiskExposure(**exposure_data)
        projects = [ProjectSnapshot(**p) for p in projects_data]
        
        # Identify drivers
        drivers = aggregation_service.identify_risk_drivers(
            portfolio_id=portfolio_id,
            exposure=exposure,
            projects=projects,
        )
        
        logger.info(f"Identified {len(drivers)} risk drivers for portfolio {portfolio_id}")
        
        return jsonify([d.__dict__ for d in drivers]), 200
    
    except Exception as e:
        logger.error(f"Error identifying risk drivers: {str(e)}")
        return jsonify({"error": str(e)}), 500


@portfolio_bp.route("/summary", methods=["POST"])
def generate_executive_summary():
    """
    Generate executive-friendly portfolio summary.
    
    Request JSON:
    {
        "portfolio_id": "PORT001",
        "exposure": {...PortfolioRiskExposure...},
        "drivers": [...RiskDriver...],
        "projects": [...ProjectSnapshot...]
    }
    
    Response: ExecutiveSummary
    """
    
    try:
        data = request.get_json()
        
        portfolio_id = data.get("portfolio_id")
        exposure_data = data.get("exposure")
        drivers_data = data.get("drivers", [])
        projects_data = data.get("projects", [])
        
        if not portfolio_id or not exposure_data:
            return jsonify({"error": "portfolio_id and exposure required"}), 400
        
        # Reconstruct objects
        exposure = PortfolioRiskExposure(**exposure_data)
        projects = [ProjectSnapshot(**p) for p in projects_data]
        
        # Generate summary
        summary = aggregation_service.generate_executive_summary(
            portfolio_id=portfolio_id,
            exposure=exposure,
            drivers=[],  # Drivers not needed for basic summary
            projects=projects,
        )
        
        logger.info(f"Generated executive summary for portfolio {portfolio_id}")
        
        return jsonify(summary.__dict__), 200
    
    except Exception as e:
        logger.error(f"Error generating executive summary: {str(e)}")
        return jsonify({"error": str(e)}), 500


@portfolio_bp.route("/trends", methods=["POST"])
def generate_trends():
    """
    Generate portfolio trend analysis.
    
    Request JSON:
    {
        "portfolio_id": "PORT001",
        "current_exposure": {...PortfolioRiskExposure...},
        "time_period": "weekly|monthly|quarterly",
        "comparison_exposures": [...PortfolioRiskExposure...]
    }
    
    Response: PortfolioTrendData
    """
    
    try:
        data = request.get_json()
        
        portfolio_id = data.get("portfolio_id")
        current_exposure_data = data.get("current_exposure")
        time_period = data.get("time_period", "weekly")
        comparison_data = data.get("comparison_exposures", [])
        
        if not portfolio_id or not current_exposure_data:
            return jsonify({"error": "portfolio_id and current_exposure required"}), 400
        
        # Reconstruct
        current_exposure = PortfolioRiskExposure(**current_exposure_data)
        comparison_exposures = [PortfolioRiskExposure(**d) for d in comparison_data]
        
        # Generate trends
        trends = intelligence_engine.generate_trends(
            portfolio_id=portfolio_id,
            current_exposure=current_exposure,
            time_period=time_period,
            comparison_exposures=comparison_exposures or None,
        )
        
        logger.info(f"Generated {time_period} trends for portfolio {portfolio_id}")
        
        return jsonify(trends.__dict__), 200
    
    except Exception as e:
        logger.error(f"Error generating trends: {str(e)}")
        return jsonify({"error": str(e)}), 500


@portfolio_bp.route("/comparison", methods=["POST"])
def generate_period_comparison():
    """
    Generate period-over-period comparison.
    
    Request JSON:
    {
        "portfolio_id": "PORT001",
        "current_exposure": {...PortfolioRiskExposure...},
        "previous_exposure": {...PortfolioRiskExposure...}
    }
    
    Response: PortfolioComparison
    """
    
    try:
        data = request.get_json()
        
        portfolio_id = data.get("portfolio_id")
        current_exposure_data = data.get("current_exposure")
        previous_exposure_data = data.get("previous_exposure")
        
        if not portfolio_id or not current_exposure_data:
            return jsonify({"error": "portfolio_id and current_exposure required"}), 400
        
        # Reconstruct
        current_exposure = PortfolioRiskExposure(**current_exposure_data)
        previous_exposure = PortfolioRiskExposure(**previous_exposure_data) if previous_exposure_data else None
        
        # Generate comparison
        comparison = intelligence_engine.generate_period_comparison(
            portfolio_id=portfolio_id,
            current_exposure=current_exposure,
            previous_exposure=previous_exposure,
        )
        
        logger.info(f"Generated period comparison for portfolio {portfolio_id}")
        
        return jsonify(comparison.__dict__), 200
    
    except Exception as e:
        logger.error(f"Error generating comparison: {str(e)}")
        return jsonify({"error": str(e)}), 500


@portfolio_bp.route("/recommendations", methods=["POST"])
def generate_recommendations():
    """
    Generate portfolio recommendations.
    
    Request JSON:
    {
        "portfolio_id": "PORT001",
        "exposure": {...PortfolioRiskExposure...},
        "drivers": [...RiskDriver...],
        "projects": [...ProjectSnapshot...],
        "feature11_allocations": {...optional...},
        "feature10_recommendations": {...optional...}
    }
    
    Response: List[Dict]
    """
    
    try:
        data = request.get_json()
        
        portfolio_id = data.get("portfolio_id")
        exposure_data = data.get("exposure")
        drivers_data = data.get("drivers", [])
        projects_data = data.get("projects", [])
        feature11_data = data.get("feature11_allocations")
        feature10_data = data.get("feature10_recommendations")
        
        if not portfolio_id or not exposure_data:
            return jsonify({"error": "portfolio_id and exposure required"}), 400
        
        # Reconstruct
        exposure = PortfolioRiskExposure(**exposure_data)
        projects = [ProjectSnapshot(**p) for p in projects_data]
        
        # Generate recommendations
        recommendations = intelligence_engine.generate_recommendations(
            portfolio_id=portfolio_id,
            exposure=exposure,
            drivers=[],
            projects=projects,
            feature11_allocations=feature11_data,
            feature10_recommendations=feature10_data,
        )
        
        logger.info(f"Generated {len(recommendations)} recommendations for portfolio {portfolio_id}")
        
        return jsonify(recommendations), 200
    
    except Exception as e:
        logger.error(f"Error generating recommendations: {str(e)}")
        return jsonify({"error": str(e)}), 500


@portfolio_bp.route("/insights", methods=["POST"])
def get_portfolio_insights():
    """
    Get comprehensive portfolio insights summary.
    
    Request JSON:
    {
        "portfolio_id": "PORT001",
        "exposure": {...PortfolioRiskExposure...},
        "summary": {...ExecutiveSummary...},
        "drivers": [...RiskDriver...]
    }
    
    Response: Dict with comprehensive insights
    """
    
    try:
        data = request.get_json()
        
        portfolio_id = data.get("portfolio_id")
        exposure_data = data.get("exposure")
        summary_data = data.get("summary")
        drivers_data = data.get("drivers", [])
        
        if not portfolio_id or not exposure_data or not summary_data:
            return jsonify({"error": "portfolio_id, exposure, and summary required"}), 400
        
        # Reconstruct (simplified for demo)
        exposure = PortfolioRiskExposure(**exposure_data)
        
        from feature12_portfolio_models import ExecutiveSummary
        summary = ExecutiveSummary(**summary_data)
        
        # Get insights
        insights = intelligence_engine.get_portfolio_insights(
            portfolio_id=portfolio_id,
            exposure=exposure,
            summary=summary,
            drivers=[],
        )
        
        logger.info(f"Generated insights for portfolio {portfolio_id}")
        
        return jsonify(insights), 200
    
    except Exception as e:
        logger.error(f"Error generating insights: {str(e)}")
        return jsonify({"error": str(e)}), 500


@portfolio_bp.route("/monday-format", methods=["POST"])
def convert_to_monday_format():
    """
    Convert portfolio data to Monday.com dashboard format.
    
    Request JSON:
    {
        "portfolio_id": "PORT001",
        "portfolio_name": "North Region Portfolio",
        "summary_metrics": {...}
    }
    
    Response: Dict in Monday.com format
    """
    
    try:
        data = request.get_json()
        
        portfolio_id = data.get("portfolio_id")
        portfolio_name = data.get("portfolio_name")
        summary_metrics = data.get("summary_metrics", {})
        
        if not portfolio_id:
            return jsonify({"error": "portfolio_id required"}), 400
        
        # Create dashboard contract
        contract = DashboardDataContract(
            portfolio_id=portfolio_id,
            portfolio_name=portfolio_name or portfolio_id,
            summary_metrics=summary_metrics,
        )
        
        # Convert to Monday format
        monday_data = MondayComIntegrator.convert_to_monday_format(contract)
        
        logger.info(f"Converted portfolio {portfolio_id} to Monday.com format")
        
        return jsonify(monday_data), 200
    
    except Exception as e:
        logger.error(f"Error converting to Monday format: {str(e)}")
        return jsonify({"error": str(e)}), 500


@portfolio_bp.route("/monday-dashboard", methods=["POST"])
def create_monday_dashboard_structure():
    """
    Create Monday.com dashboard structure for portfolio.
    
    Request JSON:
    {
        "portfolio_id": "PORT001",
        "portfolio_name": "North Region",
        "is_summary": false
    }
    
    Response: Dashboard structure configuration
    """
    
    try:
        data = request.get_json()
        
        portfolio_id = data.get("portfolio_id")
        portfolio_name = data.get("portfolio_name")
        is_summary = data.get("is_summary", False)
        
        if not portfolio_id:
            return jsonify({"error": "portfolio_id required"}), 400
        
        # Create structure
        structure = MondayComIntegrator.create_portfolio_dashboard_structure(
            portfolio_id=portfolio_id,
            portfolio_name=portfolio_name or portfolio_id,
            is_summary=is_summary,
        )
        
        logger.info(f"Created Monday.com dashboard structure for portfolio {portfolio_id}")
        
        return jsonify(structure), 200
    
    except Exception as e:
        logger.error(f"Error creating dashboard structure: {str(e)}")
        return jsonify({"error": str(e)}), 500


@portfolio_bp.route("/monday-batch-update", methods=["POST"])
def prepare_monday_batch_update():
    """
    Prepare batch portfolio update for Monday.com.
    
    Request JSON:
    {
        "portfolios": [
            {
                "portfolio_id": "", 
                "portfolio_name": "",
                "summary_metrics": {...}
            },
            ...
        ]
    }
    
    Response: Batch update payload
    """
    
    try:
        data = request.get_json()
        
        portfolios_data = data.get("portfolios", [])
        
        if not portfolios_data:
            return jsonify({"error": "portfolios required"}), 400
        
        # Create contracts
        contracts = [
            DashboardDataContract(
                portfolio_id=p.get("portfolio_id"),
                portfolio_name=p.get("portfolio_name"),
                summary_metrics=p.get("summary_metrics", {}),
            )
            for p in portfolios_data
        ]
        
        # Prepare batch
        batch = MondayComIntegrator.prepare_batch_update(contracts)
        
        logger.info(f"Prepared batch update for {len(contracts)} portfolios")
        
        return jsonify(batch), 200
    
    except Exception as e:
        logger.error(f"Error preparing batch update: {str(e)}")
        return jsonify({"error": str(e)}), 500


@portfolio_bp.route("/integrate", methods=["POST"])
def integrate_feature_data():
    """
    Build integrated context from multiple features.
    
    Request JSON:
    {
        "projects": [...ProjectSnapshot...],
        "feature9_risks": [...],
        "feature10_recommendations": [...],
        "feature11_allocations": [...]
    }
    
    Response: Integrated context dictionary
    """
    
    try:
        data = request.get_json()
        
        projects_data = data.get("projects", [])
        feature9_data = data.get("feature9_risks")
        feature10_data = data.get("feature10_recommendations")
        feature11_data = data.get("feature11_allocations")
        
        # Convert to objects
        projects = [ProjectSnapshot(**p) for p in projects_data]
        
        # Build integrated context
        context = CrossFeatureIntegrator.build_integrated_context(
            project_snapshots=projects,
            feature9_risks=feature9_data,
            feature10_recommendations=feature10_data,
            feature11_allocations=feature11_data,
        )
        
        logger.info(f"Built integrated context for {len(projects)} projects")
        
        return jsonify(context), 200
    
    except Exception as e:
        logger.error(f"Error building integrated context: {str(e)}")
        return jsonify({"error": str(e)}), 500


@portfolio_bp.route("/trace-risk", methods=["POST"])
def trace_risk_to_root_cause():
    """
    Trace portfolio risk back to root causes.
    
    Request JSON:
    {
        "portfolio_id": "PORT001",
        "exposure": {...PortfolioRiskExposure...},
        "feature9_data": {...},
        "feature10_data": {...},
        "feature11_data": {...}
    }
    
    Response: Risk traceability map
    """
    
    try:
        data = request.get_json()
        
        portfolio_id = data.get("portfolio_id")
        exposure_data = data.get("exposure")
        feature9_data = data.get("feature9_data")
        feature10_data = data.get("feature10_data")
        feature11_data = data.get("feature11_data")
        
        if not portfolio_id or not exposure_data:
            return jsonify({"error": "portfolio_id and exposure required"}), 400
        
        # Reconstruct
        exposure = PortfolioRiskExposure(**exposure_data)
        
        # Trace risk
        traceability = CrossFeatureIntegrator.trace_risk_to_root_cause(
            risk_exposure=exposure,
            feature9_data=feature9_data,
            feature10_data=feature10_data,
            feature11_data=feature11_data,
        )
        
        logger.info(f"Traced risk for portfolio {portfolio_id}")
        
        return jsonify(traceability), 200
    
    except Exception as e:
        logger.error(f"Error tracing risk: {str(e)}")
        return jsonify({"error": str(e)}), 500


@portfolio_bp.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    
    return jsonify({
        "status": "healthy",
        "service": "Feature 12 Portfolio Intelligence",
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "aggregate": "POST /api/portfolio/aggregate",
            "drivers": "POST /api/portfolio/drivers",
            "summary": "POST /api/portfolio/summary",
            "trends": "POST /api/portfolio/trends",
            "comparison": "POST /api/portfolio/comparison",
            "recommendations": "POST /api/portfolio/recommendations",
            "insights": "POST /api/portfolio/insights",
            "monday-format": "POST /api/portfolio/monday-format",
            "monday-dashboard": "POST /api/portfolio/monday-dashboard",
            "monday-batch": "POST /api/portfolio/monday-batch-update",
            "integrate": "POST /api/portfolio/integrate",
            "trace-risk": "POST /api/portfolio/trace-risk",
            "health": "GET /api/portfolio/health",
        }
    }), 200
