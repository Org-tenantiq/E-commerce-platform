import os
from typing import Optional


class Settings:
    jwt_secret: str

    def __init__(self):
        self.jwt_secret = os.getenv("JWT_SECRET", "").strip()
        if not self.jwt_secret:
            raise ValueError("JWT_SECRET environment variable must be set")


def get_settings() -> Settings:
    return Settings()
