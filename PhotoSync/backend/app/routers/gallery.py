import os, hashlib
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.models import SyncFile
from app.config import settings
from app.services.thumbnail import generate_thumbnail

router = APIRouter(prefix="/api/v1/gallery", tags=["gallery"])

@router.get("")
async def list_photos(page: int = Query(1,ge=1), page_size: int = Query(50,ge=1,le=100), db: AsyncSession = Depends(get_db)):
    total = await db.scalar(select(func.count()).where(SyncFile.status == "synced"))
    r = await db.execute(select(SyncFile).where(SyncFile.status=="synced").order_by(SyncFile.created_at.desc()).offset((page-1)*page_size).limit(page_size))
    return {"items":[{"id":f.id,"filename":f.filename,"file_size":f.file_size,"dest_path":f.dest_path,
        "created_at":str(f.created_at),"thumbnail_url":f"/api/v1/gallery/{f.id}/thumbnail",
        "image_url":f"/api/v1/gallery/{f.id}/image"} for f in r.scalars().all()],
        "total":total,"page":page,"page_size":page_size}

@router.get("/{fid}/thumbnail")
async def get_thumbnail(fid: int, db: AsyncSession = Depends(get_db)):
    f = await db.get(SyncFile, fid)
    if not f or not f.dest_path or not os.path.exists(f.dest_path): raise HTTPException(404, {"code":"FILE_NOT_FOUND"})
    tn = hashlib.sha256(f.dest_path.encode()).hexdigest()[:16]+".jpg"
    tp = os.path.join(settings.thumbnail_dir, tn)
    if os.path.exists(tp): return FileResponse(tp, media_type="image/jpeg")
    r = await generate_thumbnail(f.dest_path, settings.thumbnail_dir)
    if r: return FileResponse(r, media_type="image/jpeg")
    raise HTTPException(404, {"code":"THUMBNAIL_FAILED"})

@router.get("/{fid}/image")
async def get_image(fid: int, db: AsyncSession = Depends(get_db)):
    f = await db.get(SyncFile, fid)
    if not f or not f.dest_path or not os.path.exists(f.dest_path): raise HTTPException(404, {"code":"FILE_NOT_FOUND"})
    return FileResponse(f.dest_path)
