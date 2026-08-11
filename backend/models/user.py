from app.extensions import db


class User(db.Model):

    __tablename__ = "users"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(150),
        nullable=False
    )

    age = db.Column(
        db.Integer,
        nullable=False
    )

    phobia_id = db.Column(
        db.Integer,
        db.ForeignKey("phobias.id"),
        nullable=False
    )

    phobia = db.relationship(
        "Phobia",
        back_populates="users"
    )

    sessions = db.relationship(
        "Session",
        back_populates="user",
        cascade="all, delete-orphan"
    )