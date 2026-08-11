from datetime import datetime

from app.extensions import db
from models.heart_rate import HeartRate


class HeartRateService:

    @staticmethod
    def save_measurements(session_id, measurements):

        heart_rates = []

        for measurement in measurements:

            timestamp = measurement.get("timestamp")

            if timestamp:
                timestamp = datetime.fromisoformat(
                    timestamp.replace("Z", "+00:00")
                )
            else:
                timestamp = datetime.utcnow()

            heart_rate = HeartRate(
                session_id=session_id,
                bpm=measurement["bpm"],
                timestamp=timestamp
            )

            db.session.add(heart_rate)

            heart_rates.append(heart_rate)

        db.session.commit()

        return heart_rates