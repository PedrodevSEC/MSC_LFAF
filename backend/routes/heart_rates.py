from flask import Blueprint, jsonify, request

from services.session_service import SessionService
from services.heart_rate_service import HeartRateService


heart_rates_bp = Blueprint(
    "heart_rates",
    __name__,
    url_prefix="/sessions"
)


@heart_rates_bp.route(
    "/<int:session_id>/heart-rate",
    methods=["POST"]
)
def receive_heart_rate(session_id):

    session = SessionService.get_session(session_id)

    if not session:
        return jsonify({
            "error": "Session not found"
        }), 404

    if session.ended_at is not None:
        return jsonify({
            "error": "Session already finished"
        }), 400

    data = request.get_json()

    if not data or "measurements" not in data:
        return jsonify({
            "error": "measurements are required"
        }), 400

    measurements = data["measurements"]

    if not isinstance(measurements, list):
        return jsonify({
            "error": "measurements must be a list"
        }), 400

    if not measurements:
        return jsonify({
            "error": "measurements cannot be empty"
        }), 400

    heart_rates = HeartRateService.save_measurements(
        session_id=session_id,
        measurements=measurements
    )

    return jsonify({
        "status": "ok",
        "session_id": session_id,
        "received": len(heart_rates)
    }), 201