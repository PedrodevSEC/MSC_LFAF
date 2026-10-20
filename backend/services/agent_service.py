from datetime import datetime
from statistics import mean

from app.extensions import db
from models.heart_rate import HeartRate
from models.adaptation_decision import AdaptationDecision

from agents.monitoring_agent import MonitoringAgent
from agents.emotion_agent import EmotionAgent
from agents.adaptation_agent import AdaptationAgent


BASELINE_REQUIRED_SAMPLES = 30


class AgentService:

    def __init__(self):
        self.monitoring_agent = MonitoringAgent()
        self.emotion_agent = EmotionAgent()
        self.adaptation_agent = AdaptationAgent()

    def process_measurements(self, session, measurements):

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

                return {
                    "status": "collecting_baseline",
                    "session_id": session.id,
                    "samples_collected": sample_count,
                    "samples_required": BASELINE_REQUIRED_SAMPLES,
                    "remaining": (
                        BASELINE_REQUIRED_SAMPLES - sample_count
                    ),
                    "adaptation": None,
                }

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

            # A janela que estabeleceu a referência não produz
            # uma decisão de adaptação.
            return {
                "status": "baseline_established",
                "session_id": session.id,
                "baseline_bpm": session.baseline_bpm,
                "samples_collected": (
                    session.baseline_samples_count
                ),
                "adaptation": None,
            }

        # 2. Analisar o lote atual após estabelecer a referência.
        monitoring_result = self.monitoring_agent.analyze(
            measurements
        )

        emotion_result = self.emotion_agent.analyze(
            monitoring=monitoring_result,
            baseline_bpm=session.baseline_bpm,
        )

        adaptation_result = self.adaptation_agent.decide(
            emotion_result
        )

        # 3. Persistir somente decisões válidas.
        if adaptation_result["status"] == "decision":

            decision = AdaptationDecision(
                session_id=session.id,
                mean_bpm=monitoring_result["mean_bpm"],
                baseline_bpm=session.baseline_bpm,
                activation=emotion_result["activation"],
                action=adaptation_result["action"],
                reason=adaptation_result["reason"],
            )

            db.session.add(decision)
            db.session.commit()

            decision_id = decision.id

        else:
            decision_id = None

        # 4. Devolver um resultado serializável pela API.
        return {
            "status": "processed",
            "session_id": session.id,
            "monitoring": monitoring_result,
            "emotion": emotion_result,
            "adaptation": adaptation_result,
            "decision_id": decision_id,
        }