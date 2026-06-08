from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import SyncProfile, SyncQueue, QueueStatus
from app.services.sync_engine import SyncEngine, get_progress

router = APIRouter(prefix="/api/v1/sync", tags=["sync"])
engine = SyncEngine()

@router.post("/trigger")
async def trigger_sync(profile_id: int = Query(...), source_path: str = Query(...), db: AsyncSession = Depends(get_db)):
    p = await db.get(SyncProfile, profile_id)
    if not p: raise HTTPException(404, {"code":"PROFILE_NOT_FOUND"})
    qi = SyncQueue(card_path=source_path, profile_id=profile_id, status=QueueStatus.QUEUED)
    db.add(qi); await db.commit(); return {"ok": True, "queue_id": qi.id}

@router.get("/status")
async def sync_status():
    p = get_progress() or {}
    return {"running": bool(p), "current_file": p.get("current_file"), "current": p.get("current",0),
        "total": p.get("total",0), "current_bytes": p.get("current_bytes",0), "total_bytes": p.get("total_bytes",0),
        "speed_mbps": p.get("speed_mbps"), "eta_seconds": p.get("eta_seconds"), "elapsed_seconds": p.get("elapsed_seconds",0), "queue_length": 0}

@router.post("/cancel")
async def cancel_sync(): engine.cancel(); return {"ok": True}

@router.post("/dry-run")
async def dry_run(profile_id: int = Query(...), source_path: str = Query(...), db: AsyncSession = Depends(get_db)):
    p = await db.get(SyncProfile, profile_id)
    if not p: raise HTTPException(404, {"code":"PROFILE_NOT_FOUND"})
    return await engine.dry_run(p, source_path)

@router.get("/queue")
async def list_queue(db: AsyncSession = Depends(get_db)):
    r = await db.execute(select(SyncQueue).order_by(SyncQueue.queued_at))
    return [{"id":q.id,"card_path":q.card_path,"card_label":q.card_label,"profile_id":q.profile_id,"status":q.status,"queued_at":str(q.queued_at)} for q in r.scalars().all()]

@router.post("/queue/{qid}/cancel")
async def cancel_queue(qid: int, db: AsyncSession = Depends(get_db)):
    q = await db.get(SyncQueue, qid)
    if not q: raise HTTPException(404, {"code":"QUEUE_NOT_FOUND"})
    if q.status == QueueStatus.RUNNING: raise HTTPException(409, {"code":"SYNC_IN_PROGRESS","message":"同步进行中，请先取消当前同步"})
    q.status = QueueStatus.CANCELLED; await db.commit(); return {"ok": True}
