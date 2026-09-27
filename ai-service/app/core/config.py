from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "WhatToWatch AI Service"
    app_version: str = "0.1.0"
    environment: str = "development"

    qdrant_url: str = "http://localhost:6335"
    qdrant_collection: str = "movies"

    ollama_base_url: str = "http://localhost:11434"
    ollama_model_name: str = "qwen2.5:3b"

    embedding_model_name: str = "BAAI/bge-m3"
    embedding_device: str = "cpu"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()