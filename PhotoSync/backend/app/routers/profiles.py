from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.models import SyncProfile
from app.schemas import ProfileCreate, ProfileUpdate

router = APIRouter(prefix="/api/v1/profiles", tags=["profiles"])

@router.get("")
async def list_profiles(page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=100), db: AsyncSession = Depends(get_db)):
    total = await db.scalar(select(func.count(SyncProfile.id)))
    r = await db.execute(select(SyncProfile).offset((page-1)*page_size).limit(page_size).order_by(SyncProfile.id))
    return {"items": [{"id":p.id,"name":p.name,"match_type":p.match_type,"match_value":p.match_value,
        "destination":p.destination,"sync_mode":p.sync_mode,"auto_sync":p.auto_sync,"enabled":p.enabled,
        "created_at":str(p.created_at)} for p in r.scalars().all()],
        "total":total,"page":page,"page_size":page_size,"total_pages":(total+page_size-1)//page_size}

@router.post("", status_code=201)
async def create_profile(data: ProfileCreate, db: AsyncSession = Depends(get_db)):
    p = SyncProfile(**data.model_dump()); db.add(p); await db.commit(); await db.refresh(p); return p

@router.get("/{pid}")
async def get_profile(pid: int, db: AsyncSession = Depends(get_db)):
    p = await db.get(SyncProfile, pid)
    if not p: raise HTTPException(404, {"code":"PROFILE_NOT_FOUND","message":f"配置 {pid} 不存在"})
    return p

@router.put("/{pid}")
async def update_profile(pid: int, data: ProfileUpdate, db: AsyncSession = Depends(get_db)):
    p = await db.get(SyncProfile, pid)
    if not p: raise HTTPException(404, {"code":"PROFILE_NOT_FOUND","message":f"配置 {pid} 不存在"})
    for k,v in data.model_dump(exclude_unset=True).items(): setattr(p, k, v)
    await db.commit(); await db.refresh(p); return p

@router.delete("/{pid}")
async def delete_profile(pid: int, db: AsyncSession = Depends(get_db)):
    p = await db.get(SyncProfile, pid)
    if not p: raise HTTPException(404, {"code":"PROFILE_NOT_FOUND","message":f"配置 {pid} 不存在"})
    await db.delete(p); await db.commit(); return {"ok": True}

@router.get("/{pid}/export")
async def export_profile(pid: int, db: AsyncSession = Depends(get_db)):
    p = await db.get(SyncProfile, pid)
    if not p: raise HTTPException(404, {"code":"PROFILE_NOT_FOUND"})
    return {k:getattr(p,k) for k in ['name','match_type','match_value','destination','sync_mode',
        'custom_template','file_filters','conflict_strategy','copy_mode','auto_eject','checksum_verify','auto_sync','poll_interval','enabled']}

@router.post("/import", status_code=201)
async def import_profile(data: ProfileCreate, db: AsyncSession = Depends(get_db)):
    p = SyncProfile(**data.model_dump()); db.add(p); await db.commit(); await db.refresh(p); return p
