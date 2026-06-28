from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


DEFAULT_CORPID = "wwedd915ec24199490"
DEFAULT_SECRET = ""
DEFAULT_INTERVAL = 300


@dataclass(frozen=True)
class AppConfig:
    corp_id: str
    corp_secret: str
    check_interval: int
    state_dir: Path
    headless: bool

    @property
    def storage_state_path(self) -> Path:
        return self.state_dir / "wecom_auth.json"

    @property
    def last_ip_path(self) -> Path:
        return self.state_dir / "last_ip.txt"

    @property
    def log_path(self) -> Path:
        return self.state_dir / "sync.log"

    @property
    def screenshot_path(self) -> Path:
        return self.state_dir / "last_failure.png"


def load_config() -> AppConfig:
    state_dir = Path(os.environ.get("WECOM_STATE_DIR", "~/.wecom-ip-sync")).expanduser()
    state_dir.mkdir(parents=True, exist_ok=True)

    interval_raw = os.environ.get("WECOM_CHECK_INTERVAL", str(DEFAULT_INTERVAL))
    try:
        interval = max(60, int(interval_raw))
    except ValueError:
        interval = DEFAULT_INTERVAL

    headless_raw = os.environ.get("WECOM_HEADLESS", "0").strip().lower()

    return AppConfig(
        corp_id=os.environ.get("WECOM_CORPID", DEFAULT_CORPID).strip(),
        corp_secret=os.environ.get("WECOM_SECRET", DEFAULT_SECRET).strip(),
        check_interval=interval,
        state_dir=state_dir,
        headless=headless_raw in {"1", "true", "yes"},
    )
