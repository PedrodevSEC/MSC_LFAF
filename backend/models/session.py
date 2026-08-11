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

    map_name = db.Column(
        db.String(150),
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

    user = db.relationship(
        "User",
        back_populates="sessions"
    )

    heart_rates = db.relationship(
        "HeartRate",
        back_populates="session",
        cascade="all, delete-orphan"
    )

    @property
    def phobia(self):
        return self.user.phobia