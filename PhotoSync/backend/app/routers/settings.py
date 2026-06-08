from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import Setting
from app.schemas import SettingsUpdate

router = APIRouter(prefix="/api/v1/settings", tags=["settings"])

DEFAULTS = {"scan_paths":["/media","/mnt","/run/media"],"poll_interval":5,"default_destination":"/photos",
    "max_concurrent_copies":4,"log_retention_days":90,"history_retention_days":365}

@router.get("")
async def get_settings(db: AsyncSession = Depends(get_db)):
    r = await db.execute(select(Setting)); d = dict(DEFAULTS)
    for row in r.scalars().all(): d[row.key] = row.value
    return d

@router.put("")
async def update_settings(data: SettingsUpdate, db: AsyncSession = Depends(get_db)):
    for k,v in data.model_dump(exclude_unset=True).items():
        existing = await db.get(Setting, k)
        if existing: existing.value = v
        else: db.add(Setting(key=k, value=v))
    await db.commit()
    r = await db.execute(select(Setting)); d = dict(DEFAULTS)
    for row in r.scalars().all(): d[row.key] = row.value
    return d
