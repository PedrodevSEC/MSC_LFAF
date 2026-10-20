from datetime import datetime

from app.extensions import db


class AdaptationDecision(db.Model):

    __tablename__ = "adaptation_decisions"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    session_id = db.Column(
        db.Integer,
        db.ForeignKey("sessions.id"),
        nullable=False,
        index=True
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    mean_bpm = db.Column(
        db.Float,
        nullable=True
    )

    baseline_bpm = db.Column(
        db.Float,
        nullable=True
    )

    activation = db.Column(
        db.String(30),
        nullable=False
    )

    action = db.Column(
        db.String(50),
        nullable=False
    )

    reason = db.Column(
        db.String(255),
        nullable=False
    )

    session = db.relationship(
        "Session",
        backref=db.backref(
            "adaptation_decisions",
            lazy=True
        )
    )