import os

from dotenv import load_dotenv


load_dotenv()

database_url = os.getenv("DATABASE_URL")
if database_url and database_url.startswith("postgresql://"):
    database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)


class Config:

    SQLALCHEMY_DATABASE_URI = database_url

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    ADAPTATION_WINDOW_SAMPLES = int(os.getenv("ADAPTATION_WINDOW_SAMPLES", "5"))
    ADAPTATION_ALLOW_INCREASE = (
        os.getenv("ADAPTATION_ALLOW_INCREASE", "true").lower() == "true"
    )
