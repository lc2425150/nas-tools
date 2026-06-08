import enum
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, BigInteger, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class SyncMode(str, enum.Enum):
    DATE = "date"
    ORIGINAL = "original"
    CUSTOM = "custom"

class MatchType(str, enum.Enum):
    LABEL = "label"
    ALWAYS = "always"
    MANUAL = "manual"

class ConflictStrategy(str, enum.Enum):
    SKIP = "skip"
    OVERWRITE = "overwrite"
    RENAME = "rename"
    KEEP_BOTH = "keep_both"

class CopyMode(str, enum.Enum):
    COPY = "copy"
    MOVE = "move"

class SyncStatus(str, enum.Enum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class FileSyncStatus(str, enum.Enum):
    SYNCED = "synced"
    SKIPPED = "skipped"
    FAILED = "failed"

class QueueStatus(str, enum.Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class SyncProfile(Base):
    __tablename__ = "sync_profiles"
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    match_type = Column(String(20), nullable=False, default=MatchType.MANUAL)
    match_value = Column(String(200), nullable=True)
    destination = Column(String(500), nullable=False)
    sync_mode = Column(String(20), nullable=False, default=SyncMode.DATE)
    custom_template = Column(String(500), nullable=True)
    file_filters = Column(JSON, nullable=True)
    conflict_strategy = Column(String(20), nullable=False, default=ConflictStrategy.SKIP)
    copy_mode = Column(String(20), nullable=False, default=CopyMode.COPY)
    auto_eject = Column(Boolean, default=False)
    checksum_verify = Column(Boolean, default=True)
    auto_sync = Column(Boolean, default=False)
    poll_interval = Column(Integer, default=5)
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    histories = relationship("SyncHistory", back_populates="profile")

class SyncHistory(Base):
    __tablename__ = "sync_history"
    id = Column(Integer, primary_key=True)
    profile_id = Column(Integer, ForeignKey("sync_profiles.id"), nullable=True)
    profile_name = Column(String(200), nullable=True)
    status = Column(String(20), nullable=False, default=SyncStatus.RUNNING)
    total_files = Column(Integer, default=0)
    synced_files = Column(Integer, default=0)
    skipped_files = Column(Integer, default=0)
    failed_files = Column(Integer, default=0)
    total_bytes = Column(BigInteger, default=0)
    synced_bytes = Column(BigInteger, default=0)
    source_path = Column(String(1000), nullable=True)
    dest_path = Column(String(1000), nullable=True)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    profile = relationship("SyncProfile", back_populates="histories")
    files = relationship("SyncFile", back_populates="history")

class SyncFile(Base):
    __tablename__ = "sync_files"
    id = Column(Integer, primary_key=True)
    history_id = Column(Integer, ForeignKey("sync_history.id"), nullable=False)
    filename = Column(String(500), nullable=False)
    relative_path = Column(String(1000), nullable=True)
    source_path = Column(String(1000), nullable=False)
    dest_path = Column(String(1000), nullable=True)
    file_size = Column(BigInteger, default=0)
    checksum = Column(String(64), nullable=True)
    checksum_alg = Column(String(20), default="sha256")
    thumbnail_path = Column(String(500), nullable=True)
    status = Column(String(20), nullable=False, default=FileSyncStatus.SYNCED)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    history = relationship("SyncHistory", back_populates="files")

class FileRegistry(Base):
    __tablename__ = "file_registry"
    file_hash = Column(String(64), primary_key=True)
    original_path = Column(String(1000), nullable=False)
    file_size = Column(BigInteger, default=0)
    dest_path = Column(String(1000), nullable=True)
    first_synced_at = Column(DateTime(timezone=True), server_default=func.now())
    last_synced_at = Column(DateTime(timezone=True), server_default=func.now())

class SyncQueue(Base):
    __tablename__ = "sync_queue"
    id = Column(Integer, primary_key=True)
    card_path = Column(String(1000), nullable=False)
    card_label = Column(String(200), nullable=True)
    profile_id = Column(Integer, ForeignKey("sync_profiles.id"), nullable=True)
    status = Column(String(20), nullable=False, default=QueueStatus.QUEUED)
    queued_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    history_id = Column(Integer, nullable=True)

class SyncLog(Base):
    __tablename__ = "sync_logs"
    id = Column(Integer, primary_key=True)
    history_id = Column(Integer, ForeignKey("sync_history.id"), nullable=True)
    level = Column(String(10), nullable=False, default="INFO")
    message = Column(Text, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

class Setting(Base):
    __tablename__ = "settings"
    key = Column(String(100), primary_key=True)
    value = Column(JSON, nullable=False)

class NotificationConfig(Base):
    __tablename__ = "notification_configs"
    id = Column(Integer, primary_key=True)
    type = Column(String(50), nullable=False)
    enabled = Column(Boolean, default=True)
    config = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
