from datetime import datetime
import json
import math
from queue import Empty
from time import monotonic

from flask import Blueprint, Response, current_app, jsonify, request

from app.extensions import db
from models.adaptation_cycle import AdaptationCycle
from models.heart_rate import HeartRate

from services.realtime_service import session_event_bus
from services.session_service import SessionService


sessions_bp = Blueprint(
    "sessions",
    __name__,
    url_prefix="/sessions"
)

@sessions_bp.route("", methods=["POST"])
def create_session():
    """
    ---
    tags:
      - Sessions
    summary: Cria uma nova sessão
    description: Cria uma nova sessão para um usuário informado.
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - user_name
          properties:
            user_name:
              type: string
              example: joao
            map_id:
              type: string
              example: mapa_arac_tarefas
              description: Mapa explícito com perfil configurado no backend.
    responses:
      201:
        description: Sessão criada com sucesso.
      400:
        description: Body inválido ou user_name ausente.
      404:
        description: Usuário ou vínculo não encontrado.
      500:
        description: Erro interno ao criar a sessão.
    """
    data = request.get_json()

    if not isinstance(data, dict) or not data:
        return jsonify({
            "error": "Request body is required"
        }), 400

    user_name = data.get("user_name")

    if not user_name:
        return jsonify({
            "error": "user_name is required"
        }), 400

    map_id = data.get("map_id")
    if map_id is not None and (
        not isinstance(map_id, str) or map_id not in current_app.config["MAP_PROFILES"]
    ):
        return jsonify({"error": "Map profile is unavailable"}), 400

    try:

        session = SessionService.create_session(
            user_name=user_name,
            map_id=map_id,
        )

        return jsonify({
            "id": session.id,
            "user_id": session.user_id,
            "user_name": session.user.name,
            "section": session.section,
            "map_name": session.map_name,
            "phobia": session.phobia.name,
            "started_at": session.started_at.isoformat()
        }), 201

    except ValueError as e:

        return jsonify({
            "error": str(e)
        }), 404

    except Exception as e:

        return jsonify({
            "error": "Error creating session",
            "details": str(e)
        }), 500

@sessions_bp.route(
    "/<int:session_id>/events",
    methods=["GET"]
)
def session_events(session_id):
    """
    Stream de eventos em tempo real para um jogo ou cliente monitorar
    adaptações durante a sessão.
    """

    session = SessionService.get_session(session_id)
    if not session:
        return jsonify({"error": "Session not found"}), 404

    if session.ended_at is not None:
        return jsonify({"error": "Session already finished"}), 409

    app = current_app._get_current_object()

    def generate():
        queue = session_event_bus.subscribe(session_id)

        try:
            initial_payload = {
                "event": "session_connected",
                "session_id": session_id,
                "data": {
                    "status": "connected",
                    "message": "Conectado ao stream da sessão.",
                },
            }
            yield f"event: session_connected\ndata: {json.dumps(initial_payload)}\n\n"

            next_check = 0
            next_heartbeat = monotonic() + 15
            sent_decision_id = None
            while True:
                if monotonic() >= next_check:
                    with app.app_context():
                        session = SessionService.get_session(session_id)
                        if not session or session.ended_at is not None:
                            return
                        cycle = AdaptationCycle.latest(session_id)
                        command = cycle.command_payload() if cycle and cycle.pending else None

                    next_check = monotonic() + 1
                    if command and command["decision_id"] != sent_decision_id:
                        sent_decision_id = command["decision_id"]
                        payload = json.dumps({
                            "event": "intensity_change",
                            "session_id": session_id,
                            "data": command,
                        })
                        yield f"event: intensity_change\nid: {sent_decision_id}\ndata: {payload}\n\n"

                if monotonic() >= next_heartbeat:
                    next_heartbeat = monotonic() + 15
                    yield ": keep-alive\n\n"

                try:
                    message = queue.get(timeout=max(0, next_check - monotonic()))
                except Empty:
                    continue

                if message["event"] == "intensity_change":
                    next_check = 0
                    continue
                payload = json.dumps(message)
                yield f"event: {message['event']}\ndata: {payload}\n\n"
        except GeneratorExit:
            pass
        finally:
            session_event_bus.unsubscribe(session_id, queue)

    return Response(
        generate(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@sessions_bp.route(
    "/<int:session_id>/decisions/<int:decision_id>/ack",
    methods=["POST"],
)
def acknowledge_decision(session_id, decision_id):
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"error": "A JSON object is required"}), 400

    outcome = payload.get("outcome")
    intensity = payload.get("applied_intensity")
    if outcome not in ("applied", "at_limit"):
        return jsonify({"error": "outcome must be applied or at_limit"}), 400
    if (
        isinstance(intensity, bool)
        or not isinstance(intensity, (int, float))
        or not math.isfinite(intensity)
    ):
        return jsonify({"error": "applied_intensity must be a finite number"}), 400

    session = SessionService.lock_session(session_id)
    if not session:
        return jsonify({"error": "Session not found"}), 404

    cycle = db.session.get(AdaptationCycle, decision_id)
    if (
        not cycle
        or cycle.decision.session_id != session_id
        or cycle.decision.action == "maintain"
    ):
        return jsonify({"error": "Command not found"}), 404

    if cycle.pending:
        if session.ended_at is not None:
            return jsonify({"error": "Session already finished"}), 409

        cycle.outcome = outcome
        cycle.applied_intensity = intensity
        cycle.acknowledged_at = datetime.utcnow()
        cycle.blocked_action = cycle.decision.action if outcome == "at_limit" else None
        cycle.last_sample_id = db.session.query(db.func.max(HeartRate.id)).filter(
            HeartRate.session_id == session_id,
        ).scalar() or cycle.last_sample_id
        db.session.commit()
    elif cycle.outcome != outcome or cycle.applied_intensity != intensity:
        return jsonify({"error": "Conflicting acknowledgement"}), 409

    return jsonify({
        "decision_id": decision_id,
        "outcome": cycle.outcome,
        "applied_intensity": cycle.applied_intensity,
    })


@sessions_bp.route(
    "/<int:session_id>",
    methods=["GET"]
)
def get_session(session_id):
    """
    ---
    tags:
      - Sessions
    summary: Busca uma sessão por ID
    description: Retorna os detalhes de uma sessão cadastrada.
    parameters:
      - in: path
        name: session_id
        type: integer
        required: true
        description: Identificador da sessão.
    responses:
      200:
        description: Sessão encontrada.
      404:
        description: Sessão não encontrada.
    """
    session = SessionService.get_session(
        session_id
    )

    if not session:
        return jsonify({
            "error": "Session not found"
        }), 404

    return jsonify({
        "id": session.id,
        "user_id": session.user_id,
        "user_name": session.user.name,
        "section": session.section,
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
    """
    ---
    tags:
      - Sessions
    summary: Finaliza uma sessão
    description: Atualiza a sessão para marcar o fim do atendimento.
    parameters:
      - in: path
        name: session_id
        type: integer
        required: true
        description: Identificador da sessão.
    responses:
      200:
        description: Sessão finalizada com sucesso.
      400:
        description: Sessão já finalizada.
      404:
        description: Sessão não encontrada.
    """
    session = SessionService.lock_session(
        session_id
    )

    if not session:
        return jsonify({
            "error": "Session not found"
        }), 404

    if session.ended_at is not None:
        return jsonify({
            "error": "Session already finished"
        }), 400

    session = SessionService.finish_session(
        session
    )

    return jsonify({
        "id": session.id,
        "ended_at": session.ended_at.isoformat()
    })