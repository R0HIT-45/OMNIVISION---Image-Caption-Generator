"""Application configuration loaded from environment variables."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    fastapi_host: str = "0.0.0.0"
    fastapi_port: int = 8000
    streamlit_port: int = 8501
    api_base_url: str = "http://localhost:8000"

    # Phase 2: configurable model name (defaults to lightweight BLIP base)
    model_name: str = "Salesforce/blip-image-captioning-base"
    upload_dir: str = "static/uploads"
    max_upload_size_mb: int = 10

    @property
    def upload_path(self) -> Path:
        path = PROJECT_ROOT / self.upload_dir
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def max_upload_size_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024


settings = Settings()
