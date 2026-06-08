import os
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import SyncProfile
from app.services.card_detector import CardDetector
from app.services.file_scanner import scan_files
from app.config import settings

router = APIRouter(prefix="/api/v1/cards", tags=["cards"])

@router.get("")
async def list_cards(db: AsyncSession = Depends(get_db)):
    cards = CardDetector(settings.scan_paths).scan()
    result = []
    for c in cards:
        matched = None
        if c.label:
            r = await db.execute(select(SyncProfile).where(SyncProfile.enabled==True, SyncProfile.match_type=="label", SyncProfile.match_value==c.label))
            p = r.scalar_one_or_none()
            if p: matched = p.name
        result.append({"path":c.path,"label":c.label,"total_space":c.total_space,"used_space":c.used_space,"matched_profile":matched})
    return result

@router.get("/{path:path}/preview")
async def preview_card(path: str, file_types: str = Query("photos")):
    if not os.path.isdir(path): raise HTTPException(404, {"code":"CARD_NOT_FOUND"})
    filters = {"photos": True, "videos": file_types == "all"}
    return [{"name":f['name'],"path":f['path'],"size":f['size'],"is_dir":False,"modified":str(f['mtime'])} for f in scan_files(path, filters)]
