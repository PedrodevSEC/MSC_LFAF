from datetime import timezone

from app.extensions import db


class GameEvent(db.Model):
    __tablename__ = "game_events"
    __table_args__ = (
        db.UniqueConstraint("session_id", "event_id", name="uq_game_event_session_event"),
        db.Index("ix_game_event_session_id_id", "session_id", "id"),
    )

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(
        db.Integer, db.ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False
    )
    event_id = db.Column(db.String(100), nullable=False)
    event_type = db.Column(db.String(100), nullable=False)
    occurred_at = db.Column(db.DateTime, nullable=False)
    received_at = db.Column(db.DateTime, nullable=False)
    data = db.Column(db.JSON, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "session_id": self.session_id,
            "event_id": self.event_id,
            "event_type": self.event_type,
            "occurred_at": self.occurred_at.replace(tzinfo=timezone.utc).isoformat(),
            "received_at": self.received_at.replace(tzinfo=timezone.utc).isoformat(),
            "data": self.data,
        }
