from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://helfy:helfy@localhost:5432/helfy"
    jwt_secret: str = "dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    jwt_expires_minutes: int = 60 * 24
    score_engine_url: str = "http://localhost:8001"
    score_cache_ttl_hours: int = 24
    off_base_url: str = "https://world.openfoodfacts.org"

    model_config = SettingsConfigDict(env_prefix="CORE_", env_file=".env", extra="ignore")


settings = Settings()
