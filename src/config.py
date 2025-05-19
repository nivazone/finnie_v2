from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    MODEL_NAME: str = "gpt-4o"
    PARSER_MODEL_NAME: str = "gpt-4o"
    CLASSIFIER_MODEL_NAME: str = "gpt-4o"
    OPENAI_API_KEY: str | None = None
    OPENAI_BASE_URL: str | None = None

    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = ""
    POSTGRES_USER: str = ""
    POSTGRES_PASSWORD: str = ""

    TAVILY_API_KEY: str = ""
    LANGSMITH_TRACING: str = ""
    LANGSMITH_API_KEY: str = ""
    

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    """
    Return a cached Settings object.
    """
    
    return Settings()
