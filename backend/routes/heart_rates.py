import math

from flask import (
    Blueprint,
    jsonify,
    request,
    current_app
)

from app.extensions import db


from services.session_service import SessionService
from services.heart_rate_service import HeartRateService
from services.agent_service import AgentService

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

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "error": "A JSON object is required"
        }), 400

    measurements = data.get("measurements")

    if not isinstance(measurements, list) or not measurements:
        return jsonify({
            "error": "measurements must be a non-empty list"
        }), 400

    # Validar a estrutura antes de persistir os dados.
    for measurement in measurements:

        if not isinstance(measurement, dict):
            return jsonify({
                "error": "Each measurement must be an object"
            }), 400

        bpm = measurement.get("bpm")

        if (
            isinstance(bpm, bool)
            or not isinstance(bpm, (int, float))
            or not math.isfinite(bpm)
        ):
            return jsonify({
                "error": "Each measurement must contain a valid numeric bpm"
            }), 400

    try:
        heart_rates = HeartRateService.save_measurements(
            session_id=session_id,
            measurements=measurements
        )

        agent_service = AgentService()

        agent_result = agent_service.process_measurements(
            session=session,
            measurements=[
                {"bpm": record.bpm}
                for record in heart_rates
            ]
        )

        return jsonify({
            "status": "ok",
            "session_id": session_id,
            "received": len(heart_rates),
            "agents": agent_result,
        }), 201

    except Exception:
        db.session.rollback()

        current_app.logger.exception(
            "Error processing heart-rate batch for session %s",
            session_id
        )

        return jsonify({
            "error": "Failed to process heart-rate measurements"
        }), 500