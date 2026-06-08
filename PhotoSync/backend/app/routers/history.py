from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from typing import Optional
from app.database import get_db
from app.models import SyncHistory, SyncFile

router = APIRouter(prefix="/api/v1/history", tags=["history"])

@router.get("")
async def list_history(page: int = Query(1,ge=1), page_size: int = Query(50,ge=1,le=100),
    status: Optional[str] = None, profile_id: Optional[int] = None, db: AsyncSession = Depends(get_db)):
    q = select(SyncHistory)
    if status: q = q.where(SyncHistory.status == status)
    if profile_id: q = q.where(SyncHistory.profile_id == profile_id)
    q = q.order_by(SyncHistory.started_at.desc())
    total = await db.scalar(select(func.count()).select_from(q.subquery()))
    r = await db.execute(q.offset((page-1)*page_size).limit(page_size))
    return {"items":[{"id":h.id,"profile_id":h.profile_id,"profile_name":h.profile_name,"status":h.status,
        "total_files":h.total_files,"synced_files":h.synced_files,"skipped_files":h.skipped_files,
        "failed_files":h.failed_files,"total_bytes":h.total_bytes,"synced_bytes":h.synced_bytes,
        "source_path":h.source_path,"dest_path":h.dest_path,"started_at":str(h.started_at),
        "completed_at":str(h.completed_at) if h.completed_at else None,"error_message":h.error_message}
        for h in r.scalars().all()],
        "total":total,"page":page,"page_size":page_size,"total_pages":(total+page_size-1)//page_size}

@router.get("/{hid}")
async def get_history(hid: int, db: AsyncSession = Depends(get_db)):
    h = await db.get(SyncHistory, hid)
    if not h: raise HTTPException(404, {"code":"HISTORY_NOT_FOUND"})
    return h

@router.get("/{hid}/files")
async def get_history_files(hid: int, page: int = Query(1,ge=1), page_size: int = Query(50,ge=1,le=200), db: AsyncSession = Depends(get_db)):
    total = await db.scalar(select(func.count()).where(SyncFile.history_id == hid))
    r = await db.execute(select(SyncFile).where(SyncFile.history_id == hid).offset((page-1)*page_size).limit(page_size))
    return {"items":[{"id":f.id,"filename":f.filename,"relative_path":f.relative_path,"file_size":f.file_size,
        "checksum":f.checksum,"status":f.status,"error_message":f.error_message,"created_at":str(f.created_at)}
        for f in r.scalars().all()],"total":total,"page":page,"page_size":page_size}

@router.delete("")
async def clean_history(days: int = Query(90, ge=1), db: AsyncSession = Depends(get_db)):
    from datetime import datetime, timedelta
    cut = datetime.utcnow() - timedelta(days=days)
    await db.execute(delete(SyncHistory).where(SyncHistory.started_at < cut))
    await db.commit(); return {"ok": True}
