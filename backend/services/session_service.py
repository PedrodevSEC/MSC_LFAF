from app.extensions import db
from models.session import Session


class SessionService:

    @staticmethod
    def create_session(user_id, map_name):

        session = Session(
            user_id=user_id,
            map_name=map_name
        )

        db.session.add(session)
        db.session.commit()

        return session

    @staticmethod
    def get_session(session_id):

        return db.session.get(Session, session_id)

    @staticmethod
    def finish_session(session):

        session.ended_at = db.func.now()

        db.session.commit()

        return session