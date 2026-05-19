from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Research Intelligence API"
    app_env: str = "local"
    api_v1_prefix: str = "/api/v1"
    database_url: str = "postgresql+psycopg://research:research@localhost:5432/research_intel"
    redis_url: str = "redis://localhost:6379/0"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    ncbi_email: str = ""
    ncbi_api_key: str = ""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
