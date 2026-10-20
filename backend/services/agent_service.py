from agents.monitoring_agent import MonitoringAgent
from agents.emotion_agent import EmotionAgent
from agents.adaptation_agent import AdaptationAgent


class AgentService:
    def __init__(self):
        self.monitoring_agent = MonitoringAgent()
        self.emotion_agent = EmotionAgent()
        self.adaptation_agent = AdaptationAgent()

    def process_measurements(self, measurements, baseline_bpm=None):
        monitoring_result = self.monitoring_agent.analyze(
            measurements
        )

        emotion_result = self.emotion_agent.analyze(
            monitoring=monitoring_result,
            baseline_bpm=baseline_bpm,
        )

        adaptation_result = self.adaptation_agent.decide(
            emotion_result
        )

        return {
            "monitoring": monitoring_result,
            "emotion": emotion_result,
            "adaptation": adaptation_result,
        }