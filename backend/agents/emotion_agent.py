class EmotionAgent:
    """
    Estima ativação fisiológica relativa à linha de base individual.

    A estimativa não é um diagnóstico nem uma confirmação de medo.
    """

    def __init__(self, moderate_increase=10, high_increase=20):
        self.moderate_increase = moderate_increase
        self.high_increase = high_increase

    def analyze(self, monitoring, baseline_bpm):
        if monitoring["status"] != "ok":
            return {
                "status": "insufficient_data",
                "activation": "unknown",
                "increase_bpm": None,
            }

        if baseline_bpm is None or baseline_bpm <= 0:
            return {
                "status": "baseline_required",
                "activation": "unknown",
                "increase_bpm": None,
            }

        increase = monitoring["mean_bpm"] - baseline_bpm

        if increase >= self.high_increase:
            activation = "high"
        elif increase >= self.moderate_increase:
            activation = "moderate"
        else:
            activation = "low"

        return {
            "status": "ok",
            "activation": activation,
            "increase_bpm": round(increase, 2),
            "baseline_bpm": baseline_bpm,
        }