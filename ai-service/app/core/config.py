from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "WhatToWatch AI Service"
    app_version: str = "0.1.0"
    environment: str = "development"

    qdrant_url: str = "http://localhost:6335"
    qdrant_collection: str = "movies"
    qdrant_user_profiles_collection: str = "user_profiles"

    ollama_base_url: str = "http://localhost:11434"
    ollama_model_name: str = "qwen2.5:3b"
    backend_base_url: str = "http://localhost:8080/movie-recommendation"

    embedding_model_name: str = "BAAI/bge-m3"
    embedding_device: str = "cpu"
    embedding_cpu_threads: int = 4
    embedding_model_path: str | None = None
    reranker_model_name: str = "BAAI/bge-reranker-v2-m3"
    reranker_model_path: str | None = None
    reranker_device: str = "cpu"
    retrieval_candidate_k: int = 50
    retrieval_final_k: int = 10
    recommendation_similarity_weight: float = 0.8
    recommendation_imdb_weight: float = 0.2

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
