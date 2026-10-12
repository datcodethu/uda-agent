from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]  # thư mục ai-service/


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(BASE_DIR / ".env"), extra="ignore")

    internal_api_key: str = "doi-gia-tri-nay"

    # --- LLM / Embedding (Gemini) ---
    llm_provider: str = "gemini"          # gemini | mock
    google_api_key: str = ""
    gemini_chat_model: str = "gemini-2.5-flash"
    gemini_embedding_model: str = "models/gemini-embedding-001"
    llm_temperature: float = 0.0

    # --- Vector DB ---
    qdrant_url: str = ""                  # rỗng = chạy local
    qdrant_path: str = str(BASE_DIR / "data" / "qdrant_local")
    qdrant_collection: str = "donga_regulations"
    chunks_file: str = str(BASE_DIR / "data" / "chunks.jsonl")

    # --- Chunking ---
    chunk_max_chars: int = 1200
    chunk_overlap_chars: int = 150

    # --- Truy xuất ---
    top_k: int = 5
    candidate_k: int = 20
    min_dense_score: float = 0.0          # 0 = không dùng ngưỡng từ chối theo điểm
    max_context_chunks: int = 5
    history_turns: int = 4


settings = Settings()
