from flask import Blueprint, jsonify
from sqlalchemy import text

from app.extensions import db


health_bp = Blueprint("health", __name__)


@health_bp.route("/health", methods=["GET"])
def health():

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