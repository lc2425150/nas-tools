from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.sql import func
from app.models import FileRegistry

class DedupService:
    def __init__(self, db: AsyncSession): self.db = db

    async def is_duplicate(self, file_hash: str) -> bool:
        r = await self.db.execute(select(FileRegistry).where(FileRegistry.file_hash == file_hash))
        return r.scalar_one_or_none() is not None

    async def register_file(self, file_hash: str, original_path: str, file_size: int, dest_path: str) -> FileRegistry:
        r = await self.db.execute(select(FileRegistry).where(FileRegistry.file_hash == file_hash))
        existing = r.scalar_one_or_none()
        if existing:
            existing.last_synced_at = func.now()
            return existing
        record = FileRegistry(file_hash=file_hash, original_path=original_path, file_size=file_size, dest_path=dest_path)
        self.db.add(record)
        await self.db.commit()
        return record
