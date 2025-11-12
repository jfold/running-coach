from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    strava_client_id: str
    strava_client_secret: str
    secret_key: str
    redirect_uri: str = "http://localhost:8000/auth/callback"

    # Strava OAuth URLs
    strava_authorize_url: str = "https://www.strava.com/oauth/authorize"
    strava_token_url: str = "https://www.strava.com/api/v3/oauth/token"
    strava_api_base: str = "https://www.strava.com/api/v3"

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings():
    return Settings()
