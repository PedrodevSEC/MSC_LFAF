class HealthService:

    @staticmethod
    def get_status():
        return {
            "status": "ok",
            "project": "LFAF",
            "version": "0.2"
        }