"""
Phase 15: API Endpoints for Project Analysis with Explainability
Provides REST endpoints for analyzing construction projects with AI explanations
"""
from flask import Blueprint, request, jsonify
from app.phase15_explainability import RiskExplainer, DelayExplainer, format_explanation_for_api
import logging

logger = logging.getLogger(__name__)

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/analyze_project', methods=['POST'])
def analyze_project():
    """
    Analyze a single construction project with AI explanations.
    
    Request JSON:
    {
        "project_id": "PROJ_001",
        "project_name": "Project Name",
        "risk_score": 0.45,
        "delay_probability": 0.35,
        "predicted_delay_days": 10,
        "budget": 2500000,
        "complexity": "medium"
    }
    
    Response JSON:
    {
        "project_id": "PROJ_001",
        "risk_score": 0.45,
        "summary": "Plain-English risk explanation...",
        "confidence": {"level": "Medium", "percentage": "45%"},
        "recommendations": [...],
        "delay_explanation": "...",
        "key_factors": [...]
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        # Extract required fields
        project_id = data.get('project_id', 'UNKNOWN')
        project_name = data.get('project_name', 'Unknown Project')
        risk_score = float(data.get('risk_score', 0.5))
        delay_probability = float(data.get('delay_probability', 0.3))
        predicted_delay_days = int(data.get('predicted_delay_days', 0))
        
        # Validate ranges
        risk_score = max(0, min(1, risk_score))
        delay_probability = max(0, min(1, delay_probability))
        
        # Generate explanations
        risk_explainer = RiskExplainer()
        risk_explanation = risk_explainer.explain_risk_score(
            risk_score=risk_score,
            project_name=project_name,
            additional_context=data
        )
        
        delay_explainer = DelayExplainer()
        delay_explanation = delay_explainer.explain_delay_prediction(
            delay_days=predicted_delay_days,
            delay_probability=delay_probability,
            project_name=project_name
        )
        
        # Format for API
        api_output = format_explanation_for_api(risk_explanation)
        
        # Build complete response
        response = {
            "project_id": project_id,
            "project_name": project_name,
            "risk_score": risk_score,
            "delay_probability": delay_probability,
            "predicted_delay_days": predicted_delay_days,
            "summary": risk_explanation.summary,
            "confidence": {
                "level": risk_explanation.confidence_level,
                "percentage": f"{risk_explanation.confidence_percentage:.0f}%"
            },
            "risk_factors": risk_explanation.key_factors,
            "recommendations": risk_explanation.recommendations,
            "caveats": risk_explanation.caveats,
            "delay_summary": delay_explanation.summary,
            "delay_confidence": {
                "level": delay_explanation.confidence_level,
                "percentage": f"{delay_explanation.confidence_percentage:.0f}%"
            }
        }
        
        return jsonify(response), 200
        
    except ValueError as e:
        return jsonify({"error": f"Invalid data type: {str(e)}"}), 400
    except Exception as e:
        logger.error(f"Error analyzing project: {e}")
        return jsonify({"error": f"Analysis failed: {str(e)}"}), 500


@api_bp.route('/batch_analyze', methods=['POST'])
def batch_analyze():
    """
    Analyze multiple construction projects at once.
    
    Request JSON:
    {
        "projects": [
            {
                "project_id": "PROJ_001",
                "project_name": "Project 1",
                "risk_score": 0.45,
                ...
            },
            ...
        ]
    }
    
    Response JSON:
    {
        "analyzed_count": 2,
        "results": [
            {...analysis for project 1...},
            {...analysis for project 2...}
        ]
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'projects' not in data:
            return jsonify({"error": "Missing 'projects' array in request"}), 400
        
        projects = data.get('projects', [])
        results = []
        
        for project_data in projects:
            try:
                # Reuse the single project analysis logic
                risk_score = float(project_data.get('risk_score', 0.5))
                delay_probability = float(project_data.get('delay_probability', 0.3))
                predicted_delay_days = int(project_data.get('predicted_delay_days', 0))
                
                risk_score = max(0, min(1, risk_score))
                delay_probability = max(0, min(1, delay_probability))
                
                risk_explainer = RiskExplainer()
                risk_explanation = risk_explainer.explain_risk_score(
                    risk_score=risk_score,
                    project_name=project_data.get('project_name', 'Unknown'),
                    additional_context=project_data
                )
                
                result = {
                    "project_id": project_data.get('project_id', 'UNKNOWN'),
                    "project_name": project_data.get('project_name', 'Unknown'),
                    "risk_score": risk_score,
                    "summary": risk_explanation.summary,
                    "confidence": {
                        "level": risk_explanation.confidence_level,
                        "percentage": f"{risk_explanation.confidence_percentage:.0f}%"
                    },
                    "recommendations": risk_explanation.recommendations
                }
                results.append(result)
                
            except Exception as e:
                logger.warning(f"Failed to analyze project: {e}")
                continue
        
        return jsonify({
            "analyzed_count": len(results),
            "results": results
        }), 200
        
    except Exception as e:
        logger.error(f"Error in batch analysis: {e}")
        return jsonify({"error": f"Batch analysis failed: {str(e)}"}), 500


@api_bp.route('/version', methods=['GET'])
def version():
    """Get API version information."""
    return jsonify({
        "api_version": "1.0.0",
        "phase": 15,
        "features": [
            "risk_analysis",
            "delay_prediction",
            "explainability",
            "recommendations",
            "batch_processing"
        ]
    }), 200
