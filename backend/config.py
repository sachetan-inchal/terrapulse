"""Application Configuration & Path Management."""
import os
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent

class Settings:
    HOST: str = os.getenv("HOST", "127.0.0.1")
    PORT: int = int(os.getenv("PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    PC_STAC_API_URL: str = os.getenv("PC_STAC_API_URL", "https://planetarycomputer.microsoft.com/api/stac/v1")
    PC_API_KEY: str = os.getenv("PC_API_KEY", "")
    CACHE_DIR: Path = ROOT_DIR / "cache" / "satellite"
    OUTPUT_DIR: Path = ROOT_DIR / "cache" / "reports"

settings = Settings()
settings.CACHE_DIR.mkdir(parents=True, exist_ok=True)
settings.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
