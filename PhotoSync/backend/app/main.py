import asyncio, logging, sys
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from sqlalchemy import text

from app.config import settings
from app.database import init_db, engine
from app.services.ws_manager import ws_manager
from app.worker import start_worker, stop_worker

logging.basicConfig(level=logging.INFO, format='%(message)s', handlers=[logging.StreamHandler(sys.stdout)])
logger = logging.getLogger("photosync")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("PhotoSync 启动中..."); await init_db()
    worker_task = asyncio.create_task(start_worker())
    yield
    logger.info("PhotoSync 关闭中..."); await stop_worker(); worker_task.cancel()
    try: await worker_task
    except asyncio.CancelledError: pass
    await engine.dispose()

app = FastAPI(title="PhotoSync", description="NAS 相机储存卡自动同步系统", version="1.0.0", lifespan=lifespan)

try: app.mount("/static", StaticFiles(directory="/app/static"), name="static")
except: pass

@app.get("/")
async def root():
    return HTMLResponse('<html><head><meta http-equiv="refresh" content="0;url=/static/index.html"></head><body><p>PhotoSync - <a href="/static/index.html">打开管理界面</a></p></body></html>')

@app.get("/api/v1/system/health")
async def health():
    try:
        async with engine.connect() as conn: await conn.execute(text("SELECT 1"))
        return {"status": "healthy", "worker": {"alive": True}, "db": {"connected": True}, "version": "1.0.0"}
    except:
        return {"status": "degraded", "worker": {"alive": True}, "db": {"connected": False}, "version": "1.0.0"}

@app.websocket("/api/v1/ws/sync/status")
async def ws_endpoint(ws: WebSocket):
    await ws_manager.connect(ws)
    try:
        while True: await ws.receive_text()
    except (WebSocketDisconnect, Exception):
        ws_manager.disconnect(ws)

from app.routers import profiles, sync, cards, history, gallery, settings, notifications, system
app.include_router(profiles.router)
app.include_router(sync.router)
app.include_router(cards.router)
app.include_router(history.router)
app.include_router(gallery.router)
app.include_router(settings.router)
app.include_router(notifications.router)
app.include_router(system.router)
