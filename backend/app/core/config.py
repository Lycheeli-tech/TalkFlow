from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = "development"
    database_url: str = "postgresql+asyncpg://postgres:postgres@127.0.0.1:54322/postgres"
    supabase_url: str = "http://127.0.0.1:54321"
    supabase_jwks_url: str = "http://127.0.0.1:54321/auth/v1/.well-known/jwks.json"
    supabase_jwt_audience: str = "authenticated"
    supabase_jwt_secret: str = ""
    supabase_service_role_key: str = ""
    cors_origins: str = "http://localhost:3000"
    llm_provider: str = "fake"
    profile_extractor_provider: str = "fake"
    openai_api_key: str = ""
    openai_profile_model: str = "gpt-5.6-luna"
    stt_provider: str = "fake"
    tts_provider: str = "fake"
    max_resume_bytes: int = 5 * 1024 * 1024
    document_storage_provider: str = "fake"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
