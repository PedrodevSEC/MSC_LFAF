from app.extensions import db


class Phobia(db.Model):

    __tablename__ = "phobias"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(100),
        nullable=False,
        unique=True
    )

    sessions = db.relationship(
        "Session",
        back_populates="phobia"
    )