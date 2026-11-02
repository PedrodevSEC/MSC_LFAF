from flask import Blueprint, jsonify
from sqlalchemy import text

from app.extensions import db


health_bp = Blueprint("health", __name__)


@health_bp.route("/health", methods=["GET"])
def health():
    """
    ---
    tags:
      - Health
    summary: Health check da API
    description: Verifica se a API está funcionando e se a conexão com o banco está ativa.
    responses:
      200:
        description: API e banco funcionando.
        schema:
          type: object
          properties:
            status:
              type: string
              example: ok
            project:
              type: string
              example: LFAF
            version:
              type: string
              example: 0.3
            database:
              type: string
              example: connected
      500:
        description: Erro na conexão com o banco.
        schema:
          type: object
          properties:
            status:
              type: string
              example: error
            project:
              type: string
              example: LFAF
            database:
              type: string
              example: disconnected
            error:
              type: string
    """
    try:
        db.session.execute(text("SELECT 1"))

        return jsonify({
            "status": "ok",
            "project": "LFAF",
            "version": "0.3",
            "database": "connected"
        })

    except Exception as error:

        return jsonify({
            "status": "error",
            "project": "LFAF",
            "version": "0.3",
            "database": "disconnected",
            "error": str(error)
        }), 500