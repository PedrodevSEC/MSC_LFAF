from datetime import datetime

from app.extensions import db


class HeartRate(db.Model):

    __tablename__ = "heart_rates"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    session_id = db.Column(
        db.Integer,
        db.ForeignKey("sessions.id"),
        nullable=False
    )

    bpm = db.Column(
        db.Float,
        nullable=False
    )

    timestamp = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    session = db.relationship(
        "Session",
        back_populates="heart_rates"
    )