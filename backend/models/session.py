from datetime import datetime

from app.extensions import db


class Session(db.Model):

    __tablename__ = "sessions"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    phobia_id = db.Column(
        db.Integer,
        db.ForeignKey("phobias.id"),
        nullable=False
    )

    started_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    ended_at = db.Column(
        db.DateTime,
        nullable=True
    )

    current_section = db.Column(
        db.Integer,
        nullable=False,
        default=1
    )

    user = db.relationship(
        "User",
        back_populates="sessions"
    )

    phobia = db.relationship(
        "Phobia",
        back_populates="sessions"
    )

    heart_rates = db.relationship(
        "HeartRate",
        back_populates="session",
        cascade="all, delete-orphan"
    )