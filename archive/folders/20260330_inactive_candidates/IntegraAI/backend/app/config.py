from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "IntegraAI"
    app_version: str = "0.1.0"
    api_prefix: str = "/api/v1"
    database_url: str = "sqlite:///./integraai.db"
    cors_allow_origins: str = "*"


settings = Settings()
