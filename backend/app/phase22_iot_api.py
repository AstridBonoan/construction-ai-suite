"""Phase 22 - Real-Time IoT & Site Conditions API

REST API for real-time site condition monitoring and risk amplification.

Endpoints:
- GET /phase22/real-time/<project_id> - Get current site conditions and risk
"""

from flask import Blueprint, request, jsonify, make_response
from datetime import datetime

from phase22_iot_types import iot_to_dict
from phase22_iot_analyzer import RealTimeSiteAnalyzer

iot_bp = Blueprint("phase22_iot", __name__, url_prefix="/phase22")


@iot_bp.route("/real-time/<project_id>", methods=["GET", "OPTIONS"])
def get_real_time_intelligence(project_id: str):
    """Get real-time site conditions and intelligence (simulated).
    
    Response (200 OK):
    {
        "status": "success",
        "real_time_intelligence": {...},
        "update_frequency_seconds": 60
    }
    """
    if request.method == "OPTIONS":
        resp = make_response(('', 204))
        resp.headers["Access-Control-Allow-Origin"] = "*"
        resp.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
        resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return resp
    
    analyzer = RealTimeSiteAnalyzer()
    
    # Generate simulated current conditions
    timestamp = datetime.now().isoformat()
    weather = analyzer.generate_simulated_weather(timestamp)
    activity = analyzer.generate_simulated_activity(timestamp)
    env_risk = analyzer.assess_environmental_risk(weather, activity)
    
    # Synthesize intelligence
    intelligence = analyzer.real_time_intelligence(
        project_id=project_id,
        weather=weather,
        activity=activity,
        environmental_risk=env_risk,
    )
    
    response = {
        "status": "success",
        "real_time_intelligence": iot_to_dict(intelligence),
        "update_frequency_seconds": 60,
        "note": "DEMO MODE: Site conditions are simulated for demonstration purposes",
    }
    
    resp = jsonify(response)
    resp.headers["Access-Control-Allow-Origin"] = "*"
    return resp, 200
