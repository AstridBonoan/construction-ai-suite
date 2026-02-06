from flask import Blueprint, request, jsonify, make_response

api_bp = Blueprint("api", __name__)


@api_bp.route("/api/analyze_project", methods=["POST", "OPTIONS"])
def analyze_project():
    """Simple mock analyze endpoint used by the frontend during development.

    Returns a deterministic mock analysis based on the incoming payload.
    """
    # Handle CORS preflight
    if request.method == "OPTIONS":
        resp = make_response(('', 204))
        resp.headers["Access-Control-Allow-Origin"] = "*"
        resp.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return resp

    try:
        payload = request.get_json(force=True)
    except Exception:
        return jsonify({"error": "invalid JSON payload"}), 400

    # Build a simple mock response
    project_name = payload.get("project_name", "Unknown Project")
    risk_score = float(payload.get("risk_score", 0.5))

    summary = f"Project '{project_name}' shows a risk score of {risk_score:.2f}."
    recommendations = [
        "Increase monitoring of critical path tasks",
        "Validate subcontractor availability",
        "Review material lead times and buffer stock",
    ]

    delay_days = int(payload.get("predicted_delay_days", 10))
    delay_summary = f"Predicted delay: {delay_days} days (mock)."

    response = {
        "summary": summary,
        "risk_factors": ["budget_variance", "resource_shortage"],
        "recommendations": recommendations,
        "delay_summary": delay_summary,
        "confidence": {"level": "medium", "percentage": "65%"},
        "delay_confidence": {"level": "low", "percentage": "40%"},
    }

    resp = jsonify(response)
    # Ensure CORS headers are present for direct requests (bypass via proxy)
    resp.headers["Access-Control-Allow-Origin"] = "*"
    return resp, 200
