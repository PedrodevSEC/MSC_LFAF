from statistics import mean


class MonitoringAgent:
    """Analisa um lote de medições de frequência cardíaca."""

    def analyze(self, measurements):
        valid_bpm = []

        for measurement in measurements:
            bpm = measurement.get("bpm")

            if isinstance(bpm, bool):
                continue

            if isinstance(bpm, (int, float)) and 30 <= bpm <= 220:
                valid_bpm.append(float(bpm))

        if not valid_bpm:
            return {
                "status": "insufficient_data",
                "sample_count": 0,
                "mean_bpm": None,
                "min_bpm": None,
                "max_bpm": None,
                "trend": "unknown",
            }

        # Compara a média da primeira metade com a da segunda.
        midpoint = len(valid_bpm) // 2

        if len(valid_bpm) < 4:
            trend = "unknown"
        else:
            first_half = valid_bpm[:midpoint]
            second_half = valid_bpm[midpoint:]

            difference = mean(second_half) - mean(first_half)

            if difference >= 3:
                trend = "increasing"
            elif difference <= -3:
                trend = "decreasing"
            else:
                trend = "stable"

        return {
            "status": "ok",
            "sample_count": len(valid_bpm),
            "mean_bpm": round(mean(valid_bpm), 2),
            "min_bpm": min(valid_bpm),
            "max_bpm": max(valid_bpm),
            "trend": trend,
        }