from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import NotificationConfig
from app.schemas import NotificationConfigCreate, NotificationConfigUpdate
from app.services.notification import NotificationService

router = APIRouter(prefix="/api/v1/notification-configs", tags=["notifications"])

@router.get("")
async def list_configs(db: AsyncSession = Depends(get_db)):
    r = await db.execute(select(NotificationConfig))
    return [{"id":c.id,"type":c.type,"enabled":c.enabled,"config":c.config,"created_at":str(c.created_at)} for c in r.scalars().all()]

@router.post("", status_code=201)
async def create_config(data: NotificationConfigCreate, db: AsyncSession = Depends(get_db)):
    c = NotificationConfig(type=data.type, enabled=data.enabled, config=data.config)
    db.add(c); await db.commit(); await db.refresh(c); return c

@router.put("/{cid}")
async def update_config(cid: int, data: NotificationConfigUpdate, db: AsyncSession = Depends(get_db)):
    c = await db.get(NotificationConfig, cid)
    if not c: raise HTTPException(404, {"code":"NOTIFICATION_NOT_FOUND"})
    if data.enabled is not None: c.enabled = data.enabled
    if data.config is not None: c.config = data.config
    await db.commit(); await db.refresh(c); return c

@router.delete("/{cid}")
async def delete_config(cid: int, db: AsyncSession = Depends(get_db)):
    c = await db.get(NotificationConfig, cid)
    if not c: raise HTTPException(404, {"code":"NOTIFICATION_NOT_FOUND"})
    await db.delete(c); await db.commit(); return {"ok": True}

@router.post("/test")
async def test_notification(cid: int, db: AsyncSession = Depends(get_db)):
    c = await db.get(NotificationConfig, cid)
    if not c: raise HTTPException(404, {"code":"NOTIFICATION_NOT_FOUND"})
    try:
        await NotificationService(db)._send(c.type, c.config, "PhotoSync 测试", "这是一条测试消息", "info")
        return {"ok": True, "message": "测试消息已发送"}
    except Exception as e:
        return {"ok": False, "message": str(e)}
