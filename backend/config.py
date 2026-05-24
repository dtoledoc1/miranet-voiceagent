import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from the project root
ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=ROOT_DIR / ".env")

class Config:
    # MySQL Database Config
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", "3306"))
    DB_USER: str = os.getenv("DB_USER", "root")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "root")
    DB_NAME: str = os.getenv("DB_NAME", "miranet_voiceagent")

    # Supabase Official SDK settings
    SUPABASE_URL: str | None = os.getenv("SUPABASE_URL")
    SUPABASE_KEY: str | None = os.getenv("SUPABASE_KEY")

    # Ollama Settings
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "mistral")

    # Whisper Local Model Settings
    WHISPER_MODEL_NAME: str = os.getenv("WHISPER_MODEL_NAME", "tiny")
    WHISPER_DOWNLOAD_ROOT: str = os.getenv("WHISPER_DOWNLOAD_ROOT", str(ROOT_DIR / "models" / "whisper"))

    # PyTorch Optimization Settings
    TORCH_NUM_THREADS: int = int(os.getenv("TORCH_NUM_THREADS", "2"))

    # FastAPI Server Settings
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))

    # Simulated Network Status
    ESTADO_RED: str = os.getenv("ESTADO_RED", "ESTABLE")

# Instantiate globally
settings = Config()
