import os
from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
BASE_DIR = Path(__file__).resolve().parents[2]
APP_ENV = os.getenv("APP_ENV", "dev")
class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=( 
            BASE_DIR / ".env",
            BASE_DIR / f".env.{APP_ENV}",
        ),env_file_encoding="utf-8", extra="ignore")

    # Milvus
    milvus_uri: str = Field(default="http://localhost:19530", alias="MILVUS_URI")
    milvus_token: str = Field(default="", alias="MILVUS_TOKEN")
    milvus_collection: str = Field(default="document_kb", alias="MILVUS_COLLECTION")
    milvus_overwrite: bool = Field(default=False, alias="MILVUS_OVERWRITE")

    # MinIO
    minio_endpoint: str = Field(default="http://localhost:9000", alias="MINIO_ENDPOINT")
    minio_access_key: str = Field(default="minioadmin", alias="MINIO_ACCESS_KEY")
    minio_secret_key: str = Field(default="minioadmin", alias="MINIO_SECRET_KEY")
    minio_bucket: str = Field(default="user-uploads", alias="MINIO_BUCKET")
    minio_secure: Optional[bool] = Field(default=None, alias="MINIO_SECURE")

    # Embedding
    embed_model_name: str = Field(default="Qwen/Qwen3-Embedding-4B", alias="EMBED_MODEL_NAME")
    embed_dim: int = Field(default=2560, alias="EMBED_DIM")
    embed_device: str = Field(default="auto", alias="EMBED_DEVICE")
    embed_batch_size: int = Field(default=4, alias="EMBED_BATCH_SIZE")
    embed_max_length: int = Field(default=8192, alias="EMBED_MAX_LENGTH")

    # LLM
    dashscope_api_key: Optional[str] = Field(default=None, alias="DASHSCOPE_API_KEY")
    dashscope_basic_url: Optional[str] = Field(default=None, alias="DASHSCOPE_BASIC_URL")
    dashscope_max_tokens: Optional[str] = Field(default=None, alias="DASHSCOPE_MAX_TOKENS")
    qwen_llm_model: str = Field(default="qwen-max", alias="QWEN_LLM_MODEL")
    qwen3_reranker_model: str = Field(default=None, alias="QWEN3_RERANKER_MODEL")


    kimi_llm_model: Optional[str] = Field(default=None, alias="KIMI_LLM_MODEL")
    kimi_api_key: Optional[str] = Field(default=None, alias="KIMI_API_KEY")
    kimi_base_url: Optional[str] = Field(default=None, alias="KIMI_BASE_URL")
    kimi_max_tokens: Optional[str] = Field(default=None, alias="KIMI_MAX_TOKENS")



    # RAG
    chunk_size: int = Field(default=800, alias="CHUNK_SIZE")
    chunk_overlap: int = Field(default=120, alias="CHUNK_OVERLAP")
    similarity_top_k: int = Field(default=20, alias="SIMILARITY_TOP_K")



    # API
    langsmith_api_key: str = Field(default="dev-secret", alias="LANGSMITH_API_KEY")
    api_key: str = Field(default="dev-secret", alias="API_KEY")
    enable_api_key: bool = Field(default=False, alias="ENABLE_API_KEY")

    # Redis
    redis_host: str = Field(default="localhost", alias="REDIS_HOST")
    redis_port: int = Field(default=6379, alias="REDIS_PORT")
    redis_db: int = Field(default=0, alias="REDIS_DB")
    redis_password: Optional[str] = Field(default=None, alias="REDIS_PASSWORD")
    redis_session_key_prefix: str = Field(default="agent:context", alias="REDIS_SESSION_KEY_PREFIX")
    redis_session_ttl_seconds: int = Field(default=0, alias="REDIS_SESSION_TTL_SECONDS")

    # NEO4J
    neo4j_url: str = Field(default="bolt://localhost:7687", alias="NEO4J_URL")
    neo4j_username: str = Field(default="neo4j", alias="NEO4J_USERNAME")
    neo4j_password: str = Field(default="password", alias="NEO4J_PASSWORD")
    neo4j_database: str = Field(default="neo4j", alias="NEO4J_DATABASE")



@lru_cache
def get_settings() -> AppSettings:
    return AppSettings()
