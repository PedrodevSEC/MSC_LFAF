class AdaptationAgent:
    """
    Decide se deve manter, reduzir ou aumentar a intensidade da exposição.
    """

    def decide(self, emotion_result, allow_increase=False):
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

        if activation == "low" and allow_increase:
            return {
                "status": "decision",
                "action": "increase_intensity",
                "reason": "Low estimated physiological activation.",
            }

        return {
            "status": "decision",
            "action": "maintain",
            "reason": "No sufficient basis for changing intensity.",
        }