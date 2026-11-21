from app.extensions import db

from models.session import Session
from models.user import User


class SessionStartConflict(Exception):
    pass


class SessionService:

    @staticmethod
    def create_session(user_name, map_id=None, protocol=()):
        # O bloqueio mantém consultas e criação serializadas para o voluntário.
        user = User.query.filter_by(name=user_name).order_by(User.id).with_for_update().first()
        if not user:
            raise ValueError(f"Usuário '{user_name}' não encontrado.")

        sessions = Session.query.filter_by(user_id=user.id)
        active = (
            sessions.filter(Session.ended_at.is_(None))
            .order_by(Session.section.desc(), Session.id.desc())
            .first()
        )
        if active:
            if map_id is not None and map_id != active.map_name:
                raise SessionStartConflict("A session is already open with a different map")
            db.session.commit()
            return active, False

        last_section = db.session.query(db.func.max(Session.section)).filter(
            Session.user_id == user.id,
            Session.ended_at.is_not(None),
        ).scalar()
        section = (last_section or 0) + 1

        if protocol:
            if section > len(protocol):
                raise SessionStartConflict("The user has completed the protocol")
            map_name = protocol[section - 1]
            if map_id is not None and map_id != map_name:
                raise SessionStartConflict("The requested map does not match the next protocol stage")
        else:
            map_name = map_id or f"spider_room_{section:02d}"

        session = Session(user_id=user.id, section=section, map_name=map_name)
        db.session.add(session)
        db.session.commit()
        return session, True

    @staticmethod
    def lock_session(session_id):
        return Session.query.filter_by(id=session_id).with_for_update().populate_existing().first()

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