from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db, engine
from app.models import SyncLog

router = APIRouter(prefix="/api/v1/system", tags=["system"])

@router.get("/storage")
async def storage():
    import shutil
    result = []
    for path in ["/photos", "/media"]:
        try:
            u = shutil.disk_usage(path)
            result.append({"path":path,"total_gb":round(u.total/(1024**3),1),"used_gb":round(u.used/(1024**3),1),
                "free_gb":round(u.free/(1024**3),1),"usage_percent":round(u.used/u.total*100,1)})
        except: pass
    return result

@router.get("/logs")
async def get_logs(page: int = Query(1,ge=1), page_size: int = Query(50,ge=1,le=200),
    level: str = None, search: str = None, db: AsyncSession = Depends(get_db)):
    q = select(SyncLog).order_by(SyncLog.timestamp.desc())
    if level: q = q.where(SyncLog.level == level.upper())
    if search: q = q.where(SyncLog.message.contains(search))
    total = await db.scalar(select(func.count()).select_from(q.subquery()))
    r = await db.execute(q.offset((page-1)*page_size).limit(page_size))
    return {"items":[{"id":l.id,"level":l.level,"message":l.message,"timestamp":str(l.timestamp)} for l in r.scalars().all()],
        "total":total,"page":page,"page_size":page_size}
