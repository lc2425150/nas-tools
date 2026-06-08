from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    app_name: str = "PhotoSync"
    app_version: str = "1.0.0"
    debug: bool = False
    database_url: str = "sqlite+aiosqlite:///app/data/photosync.db"
    scan_paths: List[str] = ["/media", "/mnt", "/run/media"]
    poll_interval: int = 5
    default_destination: str = "/photos"
    max_concurrent_copies: int = 4
    max_queue_size: int = 10000
    thumbnail_dir: str = "/app/data/thumbnails"
    thumbnail_size: int = 300
    log_retention_days: int = 90
    history_retention_days: int = 365
    tz: str = "Asia/Shanghai"
    model_config = {"env_prefix": "", "case_sensitive": False}

settings = Settings()
