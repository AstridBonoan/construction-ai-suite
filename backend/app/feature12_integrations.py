"""
Feature 12: Portfolio Intelligence - Integration Layer
Connects to Features 1-11, Monday.com, and external data sources.
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import logging
import json

from feature12_portfolio_models import (
    ProjectSnapshot,
    PortfolioRiskExposure,
    DashboardDataContract,
    RiskLevel,
)

logger = logging.getLogger(__name__)


class Feature9RiskIntegration:
    """Integration with Feature 9: Deterministic Risk Synthesis"""
    
    @staticmethod
    def ingest_feature9_risk_scores(
        feature9_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Ingest deterministic risk scores from Feature 9.
        
        Args:
            feature9_data: Risk synthesis output from Feature 9
        
        Returns:
            Normalized risk data for portfolio aggregation
        """
        
        if not feature9_data:
            return {}
        
        normalized = {
            "project_id": feature9_data.get("project_id"),
            "overall_risk_score": feature9_data.get("risk_score", 0.5),
            "delay_risk": feature9_data.get("delay_risk", 0.3),
            "cost_risk": feature9_data.get("cost_risk", 0.3),
            "resource_risk": feature9_data.get("resource_risk", 0.2),
            "safety_risk": feature9_data.get("safety_risk", 0.1),
            "compliance_risk": feature9_data.get("compliance_risk", 0.05),
            "risk_drivers": feature9_data.get("risk_drivers", []),
            "confidence": feature9_data.get("confidence", 0.75),
            "last_updated": datetime.now().isoformat(),
        }
        
        logger.debug(f"Ingested Feature 9 data for project {normalized['project_id']}")
        return normalized
    
    @staticmethod
    def get_portfolio_risk_synthesis(
        feature9_scores: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Synthesize portfolio-level risk from individual Feature 9 scores.
        
        Args:
            feature9_scores: List of Feature 9 risk outputs
        
        Returns:
            Portfolio-level risk synthesis
        """
        
        if not feature9_scores:
            return {}
        
        # Aggregate scores
        avg_overall = sum(s.get("overall_risk_score", 0.5) for s in feature9_scores) / len(feature9_scores)
        avg_delay = sum(s.get("delay_risk", 0.3) for s in feature9_scores) / len(feature9_scores)
        avg_cost = sum(s.get("cost_risk", 0.3) for s in feature9_scores) / len(feature9_scores)
        avg_resource = sum(s.get("resource_risk", 0.2) for s in feature9_scores) / len(feature9_scores)
        avg_safety = sum(s.get("safety_risk", 0.1) for s in feature9_scores) / len(feature9_scores)
        
        # Collect all drivers
        all_drivers = []
        for score in feature9_scores:
            all_drivers.extend(score.get("risk_drivers", []))
        
        synthesis = {
            "portfolio_overall_risk": avg_overall,
            "portfolio_delay_risk": avg_delay,
            "portfolio_cost_risk": avg_cost,
            "portfolio_resource_risk": avg_resource,
            "portfolio_safety_risk": avg_safety,
            "systemic_risk_drivers": list(set(all_drivers))[:5],  # Top 5 unique drivers
            "num_projects_high_risk": sum(1 for s in feature9_scores if s.get("overall_risk_score", 0) > 0.6),
            "synthesis_timestamp": datetime.now().isoformat(),
        }
        
        return synthesis


class Feature10RecommendationsIntegration:
    """Integration with Feature 10: Deterministic Recommendations"""
    
    @staticmethod
    def ingest_feature10_recommendations(
        feature10_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Ingest recommendations from Feature 10.
        
        Args:
            feature10_data: Recommendation output from Feature 10
        
        Returns:
            Normalized recommendations for executive summary
        """
        
        if not feature10_data:
            return {}
        
        # Extract key recommendations
        recommendations = feature10_data.get("recommendations", [])
        
        # Classify by urgency
        critical_recs = [r for r in recommendations if r.get("urgency") == "critical"]
        high_recs = [r for r in recommendations if r.get("urgency") == "high"]
        medium_recs = [r for r in recommendations if r.get("urgency") == "medium"]
        
        normalized = {
            "project_id": feature10_data.get("project_id"),
            "total_recommendations": len(recommendations),
            "critical_count": len(critical_recs),
            "high_count": len(high_recs),
            "medium_count": len(medium_recs),
            "top_recommendation": critical_recs[0] if critical_recs else high_recs[0] if high_recs else None,
            "full_recommendations": recommendations[:10],  # Top 10
            "feature10_source": True,
            "ingestion_time": datetime.now().isoformat(),
        }
        
        logger.debug(f"Ingested {len(recommendations)} Feature 10 recommendations for project {normalized['project_id']}")
        return normalized
    
    @staticmethod
    def synthesize_portfolio_recommendations(
        feature10_project_recs: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Synthesize portfolio-level recommendations from Feature 10 project recommendations.
        
        Args:
            feature10_project_recs: List of Feature 10 recommendation sets
        
        Returns:
            Portfolio-level top recommendations
        """
        
        if not feature10_project_recs:
            return []
        
        # Collect all recommendations
        all_recs = []
        for proj_recs in feature10_project_recs:
            all_recs.extend(proj_recs.get("full_recommendations", []))
        
        # Grade by urgency
        critical = [r for r in all_recs if r.get("urgency") == "critical"]
        high = [r for r in all_recs if r.get("urgency") == "high"]
        medium = [r for r in all_recs if r.get("urgency") == "medium"]
        
        # Build portfolio synthesis
        portfolio_recs = []
        
        # Add top critical (if any)
        if critical:
            portfolio_recs.append({
                "category": "Critical",
                "count": len(critical),
                "examples": critical[:3],
            })
        
        # Add top high priority
        if high:
            portfolio_recs.append({
                "category": "High Priority",
                "count": len(high),
                "examples": high[:3],
            })
        
        logger.info(f"Synthesized portfolio recommendations: {len(critical)} critical, {len(high)} high priority")
        return portfolio_recs


class Feature11AllocationIntegration:
    """Integration with Feature 11: Resource Allocation Optimization"""
    
    @staticmethod
    def ingest_feature11_allocations(
        feature11_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Ingest resource allocations from Feature 11.
        
        Args:
            feature11_data: Allocation output from Feature 11
        
        Returns:
            Normalized allocation data for portfolio context
        """
        
        if not feature11_data:
            return {}
        
        allocations = feature11_data.get("allocations", [])
        tasks = feature11_data.get("tasks", [])
        
        # Calculate allocation metrics
        total_tasks = len(tasks)
        allocated_tasks = len([t for t in tasks if t.get("allocated")])
        unallocated_tasks = total_tasks - allocated_tasks
        
        # Calculate utilization
        resources = feature11_data.get("resources", [])
        total_capacity = sum(r.get("capacity", 0) for r in resources)
        allocated_capacity = sum(a.get("capacity_used", 0) for a in allocations)
        utilization = (allocated_capacity / total_capacity * 100) if total_capacity > 0 else 0
        
        normalized = {
            "project_id": feature11_data.get("project_id"),
            "total_tasks": total_tasks,
            "allocated_tasks": allocated_tasks,
            "unallocated_tasks": unallocated_tasks,
            "allocation_percentage": (allocated_tasks / total_tasks * 100) if total_tasks > 0 else 0,
            "total_resources": len(resources),
            "resource_utilization_percent": utilization,
            "critical_gaps": [a for a in allocations if a.get("is_critical_gap")],
            "optimization_recommendations": feature11_data.get("optimization_recommendations", []),
            "feature11_source": True,
            "ingestion_time": datetime.now().isoformat(),
        }
        
        logger.debug(f"Ingested Feature 11 allocations for project {normalized['project_id']}: {utilization:.1f}% utilization")
        return normalized
    
    @staticmethod
    def synthesize_portfolio_resource_status(
        feature11_project_data: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Synthesize portfolio resource status from Feature 11 project data.
        
        Args:
            feature11_project_data: List of Feature 11 allocation sets
        
        Returns:
            Portfolio resource summary
        """
        
        if not feature11_project_data:
            return {}
        
        total_tasks = sum(p.get("total_tasks", 0) for p in feature11_project_data)
        unallocated_total = sum(p.get("unallocated_tasks", 0) for p in feature11_project_data)
        avg_utilization = sum(p.get("resource_utilization_percent", 0) for p in feature11_project_data) / len(feature11_project_data) if feature11_project_data else 0
        
        critical_gaps = []
        for proj in feature11_project_data:
            critical_gaps.extend(proj.get("critical_gaps", []))
        
        synthesis = {
            "total_portfolio_tasks": total_tasks,
            "unallocated_tasks": unallocated_total,
            "allocation_rate": ((total_tasks - unallocated_total) / total_tasks * 100) if total_tasks > 0 else 0,
            "avg_resource_utilization": avg_utilization,
            "critical_resource_gaps": len(critical_gaps),
            "projects_with_gaps": sum(1 for p in feature11_project_data if p.get("unallocated_tasks", 0) > 0),
            "top_optimization_need": "Increase resource allocation" if unallocated_total > total_tasks * 0.1 else "Optimize existing allocation",
            "synthesis_timestamp": datetime.now().isoformat(),
        }
        
        logger.info(f"Synthesized portfolio resource status: {synthesis['allocation_rate']:.1f}% allocation rate")
        return synthesis


class MondayComIntegrator:
    """Integration with Monday.com for dashboard output"""
    
    @staticmethod
    def convert_to_monday_format(
        dashboard_contract: DashboardDataContract,
    ) -> Dict[str, Any]:
        """
        Convert dashboard data contract to Monday.com compatible format.
        
        Args:
            dashboard_contract: Portfolio data contract
        
        Returns:
            Dictionary ready for Monday.com board/widget
        """
        
        # Use the built-in conversion method
        monday_data = dashboard_contract.to_monday_com_format()
        
        logger.debug(f"Converted portfolio {dashboard_contract.portfolio_id} to Monday.com format")
        return monday_data
    
    @staticmethod
    def create_portfolio_dashboard_structure(
        portfolio_id: str,
        portfolio_name: str,
        is_summary: bool = False,
    ) -> Dict[str, Any]:
        """
        Create structure for Monday.com portfolio dashboard.
        
        Args:
            portfolio_id: Portfolio identifier
            portfolio_name: Human-readable portfolio name
            is_summary: Whether this is a summary or detail view
        
        Returns:
            Dashboard structure for Monday.com
        """
        
        structure = {
            "board_name": f"Portfolio: {portfolio_name}" if not is_summary else f"Executive Summary: {portfolio_name}",
            "board_description": "Executive portfolio intelligence and dashboard",
            "widgets": [
                {
                    "type": "metric",
                    "name": "Portfolio Health",
                    "field": "portfolio_health_score",
                    "format": "percentage",
                },
                {
                    "type": "metric",
                    "name": "Overall Risk",
                    "field": "portfolio_risk_score",
                    "format": "risk_level",
                },
                {
                    "type": "summary",
                    "name": "Project Status",
                    "breakdown": ["critical", "at_risk", "healthy"],
                },
                {
                    "type": "timeline",
                    "name": "Schedule Variance",
                    "field": "schedule_variance_days",
                },
                {
                    "type": "kpi",
                    "name": "Budget",
                    "fields": ["total_budget", "forecasted_cost", "cost_variance"],
                },
                {
                    "type": "heatmap",
                    "name": "Risk Heatmap",
                    "dimensions": ["projects", "risk_factors"],
                },
            ],
            "auto_refresh": True,
            "refresh_interval_minutes": 15 if not is_summary else 60,
            "access_level": "view_only",  # No manual configuration needed
            "no_api_required": True,  # Data pushed, not pulled
            "data_source": "Feature 12 Portfolio Intelligence",
            "created_at": datetime.now().isoformat(),
        }
        
        return structure
    
    @staticmethod
    def prepare_batch_update(
        portfolio_updates: List[DashboardDataContract],
    ) -> Dict[str, Any]:
        """
        Prepare batch update for multiple portfolios.
        
        Args:
            portfolio_updates: List of updated dashboard contracts
        
        Returns:
            Batch update payload
        """
        
        batch = {
            "update_timestamp": datetime.now().isoformat(),
            "portfolio_count": len(portfolio_updates),
            "updates": [u.to_monday_com_format() for u in portfolio_updates],
            "sync_required": True,
            "sync_strategy": "upsert",  # Create or update
        }
        
        logger.info(f"Prepared batch update for {len(portfolio_updates)} portfolios")
        return batch


class CrossFeatureIntegrator:
    """Orchestrates integration across all features"""
    
    @staticmethod
    def build_integrated_context(
        project_snapshots: List[ProjectSnapshot],
        feature9_risks: Optional[List[Dict[str, Any]]] = None,
        feature10_recommendations: Optional[List[Dict[str, Any]]] = None,
        feature11_allocations: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Build integrated context combining all feature data.
        
        Args:
            project_snapshots: Core project data
            feature9_risks: Feature 9 risk synthesis
            feature10_recommendations: Feature 10 recommendations
            feature11_allocations: Feature 11 allocations
        
        Returns:
            Integrated context for portfolio intelligence
        """
        
        context = {
            "project_count": len(project_snapshots),
            "integration_timestamp": datetime.now().isoformat(),
            "base_data": {
                "projects": len(project_snapshots),
                "total_budget": sum(p.current_budget for p in project_snapshots),
            },
            "feature_integrations": {},
        }
        
        # Integrate Feature 9 Risk
        if feature9_risks:
            feature9_synthesis = Feature9RiskIntegration.get_portfolio_risk_synthesis(feature9_risks)
            context["feature_integrations"]["feature9_risk"] = feature9_synthesis
        
        # Integrate Feature 10 Recommendations
        if feature10_recommendations:
            feature10_synthesis = Feature10RecommendationsIntegration.synthesize_portfolio_recommendations(feature10_recommendations)
            context["feature_integrations"]["feature10_recommendations"] = feature10_synthesis
        
        # Integrate Feature 11 Allocations
        if feature11_allocations:
            feature11_synthesis = Feature11AllocationIntegration.synthesize_portfolio_resource_status(feature11_allocations)
            context["feature_integrations"]["feature11_allocations"] = feature11_synthesis
        
        logger.info(f"Built integrated context for {len(project_snapshots)} projects with {len(context['feature_integrations'])} feature integrations")
        return context
    
    @staticmethod
    def trace_risk_to_root_cause(
        risk_exposure: PortfolioRiskExposure,
        feature9_data: Optional[Dict[str, Any]] = None,
        feature10_data: Optional[Dict[str, Any]] = None,
        feature11_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Trace portfolio risk back to root causes across features.
        Maps portfolio risk to specific feature origins.
        
        Args:
            risk_exposure: Portfolio risk exposure
            feature9_data: Feature 9 risk data
            feature10_data: Feature 10 data
            feature11_data: Feature 11 data
        
        Returns:
            Risk traceability map
        """
        
        traceability = {
            "portfolio_risk_score": risk_exposure.portfolio_risk_score,
            "risk_components": {
                "delay_risk": {
                    "score": risk_exposure.delay_risk_score,
                    "source": "Feature 9 delay synthesis" if feature9_data else "Model estimate",
                    "projects_affected": len(risk_exposure.critical_projects),
                },
                "cost_risk": {
                    "score": risk_exposure.cost_risk_score,
                    "source": "Feature 10 cost forecast" if feature10_data else "Model estimate",
                    "projects_affected": len(risk_exposure.at_risk_projects),
                },
                "resource_risk": {
                    "score": risk_exposure.resource_risk_score,
                    "source": "Feature 11 allocation gaps" if feature11_data else "Model estimate",
                    "allocation_rate": feature11_data.get("allocation_percentage", 0) if feature11_data else 0,
                },
            },
            "integration_status": {
                "feature9_integrated": feature9_data is not None,
                "feature10_integrated": feature10_data is not None,
                "feature11_integrated": feature11_data is not None,
            },
            "traceability_depth": "full" if all([feature9_data, feature10_data, feature11_data]) else "partial",
            "trace_timestamp": datetime.now().isoformat(),
        }
        
        return traceability
