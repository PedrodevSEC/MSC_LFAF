from datetime import datetime, timezone
import json

from flask import Blueprint, jsonify, request

from app.extensions import db
from models.game_event import GameEvent
from services.session_service import SessionService


game_events_bp = Blueprint("game_events", __name__, url_prefix="/sessions")


@game_events_bp.post("/<int:session_id>/game-events")
def record_game_event(session_id):
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"error": "A JSON object is required"}), 400

    for field in ("event_id", "event_type"):
        value = payload.get(field)
        if not isinstance(value, str) or not value.strip() or len(value) > 100:
            return jsonify({"error": f"{field} must be a string with up to 100 characters"}), 400

    try:
        occurred_at = datetime.fromisoformat(payload.get("occurred_at"))
        if occurred_at.utcoffset() is None:
            raise ValueError("Timestamp has no UTC offset")
        occurred_at = occurred_at.astimezone(timezone.utc).replace(tzinfo=None)
    except (TypeError, ValueError, OverflowError):
        return jsonify({"error": "occurred_at must be an ISO 8601 timestamp with UTC offset"}), 400

    data = payload.get("data", {})
    if not isinstance(data, dict):
        return jsonify({"error": "data must be a JSON object"}), 400
    try:
        # O PostgreSQL exige JSON válido, inclusive para números em objetos aninhados.
        json.dumps(data, allow_nan=False)
    except (ValueError, RecursionError):
        return jsonify({"error": "data must contain valid JSON values"}), 400

    session = SessionService.lock_session(session_id)
    if not session:
        return jsonify({"error": "Session not found"}), 404

    event_id = payload["event_id"]
    event_type = payload["event_type"]
    existing = GameEvent.query.filter_by(session_id=session_id, event_id=event_id).first()
    if existing:
        if (existing.event_type, existing.occurred_at, existing.data) != (event_type, occurred_at, data):
            return jsonify({"error": "event_id already exists with different data"}), 409
        return jsonify(existing.to_dict()), 200

    if session.ended_at is not None:
        return jsonify({"error": "Session already finished"}), 409

    event = GameEvent(
        session_id=session_id,
        event_id=event_id,
        event_type=event_type,
        occurred_at=occurred_at,
        received_at=datetime.now(timezone.utc).replace(tzinfo=None),
        data=data,
    )
    db.session.add(event)
    db.session.commit()
    return jsonify(event.to_dict()), 201


@game_events_bp.get("/<int:session_id>/game-events")
def list_game_events(session_id):
    try:
        after_id = int(request.args.get("after_id", "0"))
        limit = int(request.args.get("limit", "100"))
        if not 0 <= after_id <= 2_147_483_647 or not 1 <= limit <= 500:
            raise ValueError("Invalid pagination")
    except ValueError:
        return jsonify({"error": "Provide a valid after_id and a limit from 1 to 500"}), 400

    if not SessionService.get_session(session_id):
        return jsonify({"error": "Session not found"}), 404

    events = (
        GameEvent.query.filter(GameEvent.session_id == session_id, GameEvent.id > after_id)
        .order_by(GameEvent.id)
        .limit(limit + 1)
        .all()
    )
    next_after_id = events[limit - 1].id if len(events) > limit else None
    return jsonify({
        "session_id": session_id,
        "events": [event.to_dict() for event in events[:limit]],
        "next_after_id": next_after_id,
    })
