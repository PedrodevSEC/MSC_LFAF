import os

from dotenv import load_dotenv


load_dotenv()


class Config:

    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    ADAPTATION_WINDOW_SAMPLES = int(os.getenv("ADAPTATION_WINDOW_SAMPLES", "5"))
    ADAPTATION_ALLOW_INCREASE = (
        os.getenv("ADAPTATION_ALLOW_INCREASE", "true").lower() == "true"
    )