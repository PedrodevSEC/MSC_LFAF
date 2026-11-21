from app.extensions import db


class AdaptationCycle(db.Model):
    __tablename__ = "adaptation_cycles"

    decision_id = db.Column(
        db.Integer,
        db.ForeignKey("adaptation_decisions.id", ondelete="CASCADE"),
        primary_key=True,
    )
    last_sample_id = db.Column(db.Integer, nullable=False)
    acknowledged_at = db.Column(db.DateTime)
    outcome = db.Column(db.String(20))
    applied_intensity = db.Column(db.Float)
    blocked_action = db.Column(db.String(50))

    decision = db.relationship("AdaptationDecision")
    map_command = db.relationship("MapAdaptationCommand", uselist=False)

    @classmethod
    def latest(cls, session_id):
        return (
            cls.query.join(cls.decision)
            .filter_by(session_id=session_id)
            .order_by(cls.decision_id.desc())
            .first()
        )

    @property
    def pending(self):
        return self.outcome is None

    def command_payload(self):
        payload = {
            "action": self.decision.action,
            "reason": self.decision.reason,
            "activation": self.decision.activation,
            "mean_bpm": self.decision.mean_bpm,
            "decision_id": self.decision_id,
        }
        if self.map_command:
            payload.update(self.map_command.payload)
        return payload


class MapAdaptationCommand(db.Model):
    __tablename__ = "map_adaptation_commands"

    decision_id = db.Column(
        db.Integer,
        db.ForeignKey("adaptation_cycles.decision_id", ondelete="CASCADE"),
        primary_key=True,
    )
    level = db.Column(db.Integer, nullable=False)
    payload = db.Column(db.JSON, nullable=False)

    @classmethod
    def last_applied(cls, session_id):
        return (
            cls.query.join(AdaptationCycle, cls.decision_id == AdaptationCycle.decision_id)
            .join(AdaptationCycle.decision)
            .filter_by(session_id=session_id)
            .filter(AdaptationCycle.outcome == "applied")
            .order_by(cls.decision_id.desc())
            .first()
        )
