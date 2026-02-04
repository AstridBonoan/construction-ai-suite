from flask import Flask, request
from flask_cors import CORS
from app.routes.project_delay import project_delay_bp
import json
from pathlib import Path

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
app.register_blueprint(project_delay_bp)


@app.route('/health', methods=['GET'])
def health_check():
    return (json.dumps({"status": "ok"}), 200, {'Content-Type': 'application/json'})


@app.route('/phase9/outputs', methods=['GET'])
def get_phase9_outputs():
    """Serve Phase 9 outputs for local development.

    Prefers `reports/phase9_outputs.json` if present, otherwise falls back
    to `frontend_phase10/src/mock/phase9_sample.json`.
    """
    # Prefer a canonical outputs file in `reports/phase9_outputs.json` if present
    # Use parents[1] to resolve to the repository root (module is at /app/app)
    reports_path = Path(__file__).resolve().parents[1] / 'reports' / 'phase9_outputs.json'
    if reports_path.exists():
        with open(reports_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    else:
        mock_path = Path(__file__).resolve().parents[1] / 'frontend_phase10' / 'src' / 'mock' / 'phase9_sample.json'
        if not mock_path.exists():
            return (json.dumps({"error": "mock not found"}), 500, {'Content-Type': 'application/json'})
        with open(mock_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

    variant = request.args.get('variant')

    if variant == 'live':
        for obj in data:
            obj['project_name'] = f"{obj.get('project_name','')} (LIVE)"
            if isinstance(obj.get('risk_score'), (int, float)):
                obj['risk_score'] = min(1.0, round(obj['risk_score'] + 0.13, 2))
            if isinstance(obj.get('delay_probability'), (int, float)):
                obj['delay_probability'] = min(1.0, round(obj['delay_probability'] + 0.1, 2))
            if isinstance(obj.get('predicted_delay_days'), (int, float)):
                obj['predicted_delay_days'] = int(obj.get('predicted_delay_days', 0)) + 8

    return (json.dumps(data), 200, {'Content-Type': 'application/json'})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
