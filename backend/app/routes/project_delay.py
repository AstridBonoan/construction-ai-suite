from flask import Blueprint, jsonify

project_delay_bp = Blueprint("project_delay", __name__)


@project_delay_bp.route("/project-delay", methods=["GET"])
def get_delay_prediction():
    return jsonify({"message": "Project Delay Prediction API is live"})
