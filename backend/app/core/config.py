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
    supabase_jwt_leeway_seconds: int = 30
    supabase_jwt_secret: str = ""
    supabase_service_role_key: str = ""
    cors_origins: str = "http://localhost:3000"
    llm_provider: str = "fake"
    profile_extractor_provider: str = "fake"
    bailian_api_key: str = ""
    bailian_compatible_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    bailian_dashscope_base_url: str = "https://dashscope.aliyuncs.com/api/v1"
    bailian_text_model: str = "qwen3.7-flash"
    bailian_stt_model: str = "qwen3-asr-flash"
    bailian_tts_model: str = "qwen3-tts-flash"
    bailian_tts_voice: str = "Cherry"
    stt_provider: str = "fake"
    tts_provider: str = "fake"
    audio_storage_provider: str = "fake"
    max_audio_bytes: int = 20 * 1024 * 1024
    course_audio_cleanup_interval_seconds: int = 60 * 60
    max_resume_bytes: int = 5 * 1024 * 1024
    document_storage_provider: str = "fake"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
