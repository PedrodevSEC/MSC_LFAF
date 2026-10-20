from app.extensions import db

from models.session import Session
from models.user import User


class SessionService:

    @staticmethod
    def create_session(user_name):

        user = User.query.filter_by(
            name=user_name
        ).first()

        if not user:
            raise ValueError(
                f"Usuário '{user_name}' não encontrado."
            )

        # Próxima seção do usuário
        previous_sessions = Session.query.filter_by(
            user_id=user.id
        ).count()

        section = previous_sessions + 1

        # Mapa correspondente à seção
        map_name = f"spider_room_{section:02d}"

        session = Session(
            user_id=user.id,
            section=section,
            map_name=map_name
        )

        db.session.add(session)
        db.session.commit()

        return session

    @staticmethod
    def get_session(session_id):

        return db.session.get(
            Session,
            session_id
        )

    @staticmethod
    def finish_session(session):

        session.ended_at = db.func.now()

        db.session.commit()

        return session