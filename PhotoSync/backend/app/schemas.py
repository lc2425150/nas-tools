from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class ProfileCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    match_type: str = "manual"
    match_value: Optional[str] = None
    destination: str = "/photos"
    sync_mode: str = "date"
    custom_template: Optional[str] = None
    file_filters: Optional[dict] = None
    conflict_strategy: str = "skip"
    copy_mode: str = "copy"
    auto_eject: bool = False
    checksum_verify: bool = True
    auto_sync: bool = False
    poll_interval: int = 5
    enabled: bool = True

class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    match_type: Optional[str] = None
    match_value: Optional[str] = None
    destination: Optional[str] = None
    sync_mode: Optional[str] = None
    custom_template: Optional[str] = None
    file_filters: Optional[dict] = None
    conflict_strategy: Optional[str] = None
    copy_mode: Optional[str] = None
    auto_eject: Optional[bool] = None
    checksum_verify: Optional[bool] = None
    auto_sync: Optional[bool] = None
    poll_interval: Optional[int] = None
    enabled: Optional[bool] = None

class ProfileResponse(BaseModel):
    id: int; name: str; match_type: str; match_value: Optional[str]
    destination: str; sync_mode: str; custom_template: Optional[str]
    file_filters: Optional[dict]; conflict_strategy: str; copy_mode: str
    auto_eject: bool; checksum_verify: bool; auto_sync: bool
    poll_interval: int; enabled: bool; created_at: datetime; updated_at: datetime
    model_config = {"from_attributes": True}

class HistoryResponse(BaseModel):
    id: int; profile_id: Optional[int]; profile_name: Optional[str]
    status: str; total_files: int; synced_files: int; skipped_files: int
    failed_files: int; total_bytes: int; synced_bytes: int
    source_path: Optional[str]; dest_path: Optional[str]
    started_at: datetime; completed_at: Optional[datetime]; error_message: Optional[str]
    model_config = {"from_attributes": True}

class HistoryDetailResponse(HistoryResponse):
    files: List["SyncFileResponse"] = []

class SyncFileResponse(BaseModel):
    id: int; filename: str; relative_path: Optional[str]; file_size: int
    checksum: Optional[str]; status: str; error_message: Optional[str]; created_at: datetime
    model_config = {"from_attributes": True}

class CardInfo(BaseModel):
    path: str; label: str; total_space: Optional[int] = None
    used_space: Optional[int] = None; matched_profile: Optional[str] = None

class FilePreview(BaseModel):
    name: str; path: str; size: int; is_dir: bool; modified: Optional[str] = None

class SyncStatusResponse(BaseModel):
    running: bool; current_file: Optional[str] = None; current: int = 0
    total: int = 0; current_bytes: int = 0; total_bytes: int = 0
    speed_mbps: Optional[float] = None; eta_seconds: Optional[int] = None
    elapsed_seconds: int = 0; queue_length: int = 0

class DryRunResponse(BaseModel):
    total_files: int; total_size: int; new_files: int; new_size: int
    skipped_files: int; skipped_size: int; files: List[dict] = []

class SettingsUpdate(BaseModel):
    scan_paths: Optional[list] = None; poll_interval: Optional[int] = None
    default_destination: Optional[str] = None
    max_concurrent_copies: Optional[int] = None
    log_retention_days: Optional[int] = None; history_retention_days: Optional[int] = None

class NotificationConfigCreate(BaseModel):
    type: str = Field(..., pattern="^(telegram|dingtalk|wechat|email|webhook)$")
    enabled: bool = True; config: dict

class NotificationConfigUpdate(BaseModel):
    enabled: Optional[bool] = None; config: Optional[dict] = None

class NotificationConfigResponse(BaseModel):
    id: int; type: str; enabled: bool; config: dict; created_at: datetime
    model_config = {"from_attributes": True}

class QueueItemResponse(BaseModel):
    id: int; card_path: str; card_label: Optional[str]
    profile_id: Optional[int]; status: str; queued_at: datetime
    model_config = {"from_attributes": True}

class ErrorResponse(BaseModel):
    error: dict = Field(default_factory=lambda: {"code": "UNKNOWN", "message": "未知错误"})

class HealthResponse(BaseModel):
    status: str; worker: dict; db: dict; disk: dict

class StorageResponse(BaseModel):
    path: str; total_gb: float; used_gb: float; free_gb: float; usage_percent: float
