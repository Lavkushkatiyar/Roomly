from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Roomly"
    app_version: str = "0.1.0"
    environment: str = "development"
    DATABASE_URL: str = "postgres"
    GNANI_API_KEY_ID: str = "yourAPI"
    model: str = "timbre-v3.0"
    REASONING_PROVIDER: str = "ollama"
    REASONING_MODEL: str = "qwen3:8b"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OPENROUTER_API_KEY: str = "your-api-key"
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
