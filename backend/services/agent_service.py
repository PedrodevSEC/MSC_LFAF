from datetime import datetime
from statistics import mean

from flask import current_app

from app.extensions import db
from config.map_profiles import MAPA_ARAC_TAREFAS
from models.adaptation_cycle import AdaptationCycle, MapAdaptationCommand
from models.heart_rate import HeartRate
from models.adaptation_decision import AdaptationDecision

from agents.monitoring_agent import MonitoringAgent
from agents.emotion_agent import EmotionAgent
from agents.adaptation_agent import AdaptationAgent
from services.realtime_service import session_event_bus


BASELINE_REQUIRED_SAMPLES = 30


class AgentService:

    def __init__(self):
        self.monitoring_agent = MonitoringAgent()
        self.emotion_agent = EmotionAgent()
        self.adaptation_agent = AdaptationAgent()

    def process_measurements(self, session):

        # 1. Estabelecer a referência fisiológica inicial.
        if session.baseline_bpm is None:

            valid_history = (
                HeartRate.query
                .filter(
                    HeartRate.session_id == session.id,
                    HeartRate.bpm >= 30,
                    HeartRate.bpm <= 220
                )
                .order_by(HeartRate.id.asc())
                .limit(BASELINE_REQUIRED_SAMPLES)
                .all()
            )

            sample_count = len(valid_history)

            if sample_count < BASELINE_REQUIRED_SAMPLES:
                session.baseline_samples_count = sample_count
                db.session.commit()

                response = {
                    "status": "collecting_baseline",
                    "session_id": session.id,
                    "samples_collected": sample_count,
                    "samples_required": BASELINE_REQUIRED_SAMPLES,
                    "remaining": (
                        BASELINE_REQUIRED_SAMPLES - sample_count
                    ),
                    "adaptation": None,
                }

                session_event_bus.publish(
                    session.id,
                    "baseline_status",
                    response,
                )

                return response

            baseline_values = [
                record.bpm for record in valid_history
            ]

            session.baseline_bpm = round(
                mean(baseline_values), 2
            )
            session.baseline_samples_count = (
                BASELINE_REQUIRED_SAMPLES
            )
            session.baseline_completed_at = datetime.utcnow()

            db.session.commit()

            response = {
                "status": "baseline_established",
                "session_id": session.id,
                "baseline_bpm": session.baseline_bpm,
                "samples_collected": (
                    session.baseline_samples_count
                ),
                "adaptation": None,
            }

            session_event_bus.publish(
                session.id,
                "baseline_established",
                response,
            )

            return response

        cycle = AdaptationCycle.latest(session.id)
        if cycle and cycle.pending:
            db.session.commit()
            return {
                "status": "awaiting_ack",
                "session_id": session.id,
                "decision_id": cycle.decision_id,
                "adaptation": None,
            }

        samples_required = current_app.config["ADAPTATION_WINDOW_SAMPLES"]
        query = HeartRate.query.filter(
            HeartRate.session_id == session.id,
            HeartRate.bpm.between(30, 220),
        )
        if session.baseline_completed_at:
            query = query.filter(HeartRate.timestamp > session.baseline_completed_at)
        elif not cycle:
            query = query.order_by(HeartRate.id).offset(session.baseline_samples_count)

        if cycle:
            query = query.filter(HeartRate.id > cycle.last_sample_id)
            # Preserve the last command's observation boundary across maintain decisions.
            if cycle.acknowledged_at:
                query = query.filter(HeartRate.timestamp > cycle.acknowledged_at)

        samples = query.order_by(HeartRate.id).limit(samples_required).all()
        if len(samples) < samples_required:
            db.session.commit()
            return {
                "status": "collecting_adaptation_window",
                "session_id": session.id,
                "samples_collected": len(samples),
                "samples_required": samples_required,
                "adaptation": None,
            }

        monitoring = self.monitoring_agent.analyze([{"bpm": sample.bpm} for sample in samples])
        emotion = self.emotion_agent.analyze(monitoring, session.baseline_bpm)
        adaptation = self.adaptation_agent.decide(
            emotion, allow_increase=current_app.config["ADAPTATION_ALLOW_INCREASE"]
        )

        blocked_action = cycle.blocked_action if cycle else None
        if blocked_action and adaptation["action"] == blocked_action:
            adaptation = {
                "status": "decision",
                "action": "maintain",
                "reason": "The game reported the intensity limit in this direction.",
            }

        profile = current_app.config["MAP_PROFILES"].get(session.map_name)
        next_level = None
        if profile and adaptation["action"] != "maintain":
            last_command = MapAdaptationCommand.last_applied(session.id)
            level = last_command.level if last_command else profile["initial_level"]
            step = 1 if adaptation["action"] == "increase_intensity" else -1
            candidate = level + step
            if 0 <= candidate < len(profile["levels"]):
                next_level = candidate
            else:
                adaptation = {
                    "status": "decision",
                    "action": "maintain",
                    "reason": "The map profile has no level in this direction.",
                }
        elif session.map_name == MAPA_ARAC_TAREFAS and not profile:
            adaptation = {
                "status": "decision",
                "action": "maintain",
                "reason": "The map profile is unavailable.",
            }

        decision = AdaptationDecision(
            session_id=session.id,
            mean_bpm=monitoring["mean_bpm"],
            baseline_bpm=session.baseline_bpm,
            activation=emotion["activation"],
            action=adaptation["action"],
            reason=adaptation["reason"],
        )
        next_cycle = AdaptationCycle(
            decision=decision,
            last_sample_id=samples[-1].id,
            blocked_action=blocked_action,
        )
        if decision.action == "maintain":
            next_cycle.outcome = "maintained"
            next_cycle.acknowledged_at = cycle.acknowledged_at if cycle else None

        db.session.add(next_cycle)
        db.session.flush()
        if next_level is not None:
            next_cycle.map_command = MapAdaptationCommand(
                level=next_level,
                payload={
                    "command_id": f"decision-{decision.id}",
                    "session_id": session.id,
                    "map_id": session.map_name,
                    "sequence": decision.id,
                    "command": profile["command"],
                    "parameters": profile["levels"][next_level],
                    "transition_seconds": 2,
                },
            )

        response = {
            "status": "processed",
            "session_id": session.id,
            "monitoring": monitoring,
            "emotion": emotion,
            "adaptation": adaptation,
            "decision_id": decision.id,
        }
        command = next_cycle.command_payload() if next_cycle.pending else None
        db.session.commit()

        session_event_bus.publish(session.id, "agent_result", response)
        if command:
            session_event_bus.publish(session.id, "intensity_change", command)

        return response
