from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    
    LLM_PROVIDER: str = "cerebras"
    EMBEDDING_PROVIDER: str = "sentence_transformer"

    CEREBRAS_API_KEY: str
    CEREBRAS_BASE_URL: str = "https://api.cerebras.ai/v1"
    CEREBRAS_MODEL: str = "gemma-4-31b"
    
    EMBEDDING_MODEL: str = "intfloat/multilingual-e5-base"
    
    model_config = SettingsConfigDict(env_file=".env",extra="ignore")


settings = Settings()