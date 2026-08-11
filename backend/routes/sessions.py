from flask import Blueprint, jsonify, request

from services.session_service import SessionService


sessions_bp = Blueprint(
    "sessions",
    __name__,
    url_prefix="/sessions"
)


@sessions_bp.route("", methods=["POST"])
def create_session():

    data = request.get_json()

    if not data:
        return jsonify({
            "error": "Request body is required"
        }), 400

    user_id = data.get("user_id")
    map_name = data.get("map_name")

    if not user_id or not map_name:
        return jsonify({
            "error": "user_id and map_name are required"
        }), 400

    session = SessionService.create_session(
        user_id=user_id,
        map_name=map_name
    )

    return jsonify({
        "id": session.id,
        "user_id": session.user_id,
        "map_name": session.map_name,
        "phobia": session.phobia.name,
        "started_at": session.started_at.isoformat()
    }), 201


@sessions_bp.route("/<int:session_id>", methods=["GET"])
def get_session(session_id):

    session = SessionService.get_session(session_id)

    if not session:
        return jsonify({
            "error": "Session not found"
        }), 404

    return jsonify({
        "id": session.id,
        "user_id": session.user_id,
        "map_name": session.map_name,
        "phobia": session.phobia.name,
        "started_at": session.started_at.isoformat(),
        "ended_at": (
            session.ended_at.isoformat()
            if session.ended_at
            else None
        )
    })


@sessions_bp.route(
    "/<int:session_id>/finish",
    methods=["POST"]
)
def finish_session(session_id):

    session = SessionService.get_session(session_id)

    if not session:
        return jsonify({
            "error": "Session not found"
        }), 404

    if session.ended_at is not None:
        return jsonify({
            "error": "Session already finished"
        }), 400

    session = SessionService.finish_session(session)

    return jsonify({
        "id": session.id,
        "ended_at": session.ended_at.isoformat()
    })