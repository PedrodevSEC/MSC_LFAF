class AdaptationAgent:
    """
    Decide se deve manter ou reduzir a intensidade da exposição.

    A versão inicial não aumenta automaticamente a dificuldade.
    """

    def decide(self, emotion_result):
        if emotion_result["status"] != "ok":
            return {
                "status": "no_decision",
                "action": "maintain",
                "reason": "Insufficient information for adaptation.",
            }

        activation = emotion_result["activation"]

        if activation == "high":
            return {
                "status": "decision",
                "action": "reduce_intensity",
                "reason": "High estimated physiological activation.",
            }

        return {
            "status": "decision",
            "action": "maintain",
            "reason": "No sufficient basis for changing intensity.",
        }