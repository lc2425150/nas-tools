import os, shutil, asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, Callable
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func

from app.models import SyncHistory, SyncFile, FileRegistry, SyncProfile, SyncStatus, FileSyncStatus
from app.services.file_scanner import scan_files, detect_sidecar_files, sanitize_filename
from app.services.dedup import DedupService
from app.services.checksum import calculate_sha256, verify_checksum
from app.services.file_organizer import FileOrganizer
from app.services.thumbnail import generate_thumbnail
from app.services.ws_manager import ws_manager
from app.database import async_session

_executor = ThreadPoolExecutor(max_workers=4)
_sync_lock = asyncio.Lock()
_is_running = False
_current_progress = {}

def get_progress(): return _current_progress

class SyncEngine:
    def __init__(self, max_concurrent: int = 4):
        self.max_concurrent = max_concurrent; self._cancel = False
        self.semaphore = asyncio.Semaphore(max_concurrent)

    async def _copy(self, src, dst):
        loop = asyncio.get_event_loop()
        tmp = dst + ".partial"
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        await loop.run_in_executor(_executor, shutil.copy2, src, tmp)
        os.rename(tmp, dst)

    async def _move(self, src, dst):
        await self._copy(src, dst); os.remove(src)

    async def dry_run(self, profile: SyncProfile, source_path: str) -> dict:
        filters = profile.file_filters or {}
        org = FileOrganizer(profile.destination, profile.sync_mode, profile.custom_template)
        new, skipped, total_size = [], [], 0
        async with async_session() as db:
            dedup = DedupService(db)
            for fi in scan_files(source_path, filters):
                total_size += fi['size']
                fh = await calculate_sha256(fi['path'])
                is_dup = await dedup.is_duplicate(fh)
                item = {"name": fi['name'], "size": fi['size'], "will_copy": not is_dup,
                        "reason": "已同步过" if is_dup else "新文件"}
                (skipped if is_dup else new).append(item)
        return {"total_files": len(new)+len(skipped), "total_size": total_size,
                "new_files": len(new), "new_size": sum(f['size'] for f in new),
                "skipped_files": len(skipped), "skipped_size": sum(f['size'] for f in skipped),
                "files": new + skipped}

    async def run_sync(self, profile_id: int, source_path: str, progress_cb: Callable = None) -> int:
        global _is_running, _current_progress
        async with _sync_lock:
            if _is_running: raise RuntimeError("已有同步任务进行中")
            _is_running = True; self._cancel = False

        history_id = 0
        try:
            async with async_session() as db:
                profile = await db.get(SyncProfile, profile_id)
                if not profile: raise ValueError(f"配置 {profile_id} 不存在")
                hist = SyncHistory(profile_id=profile_id, profile_name=profile.name,
                                   status=SyncStatus.RUNNING, source_path=source_path,
                                   dest_path=profile.destination)
                db.add(hist); await db.commit(); await db.refresh(hist); history_id = hist.id

            filters = profile.file_filters or {}
            org = FileOrganizer(profile.destination, profile.sync_mode, profile.custom_template)
            all_files = list(scan_files(source_path, filters))
            _current_progress = {"current": 0, "total": len(all_files),
                "current_bytes": 0, "total_bytes": sum(f['size'] for f in all_files),
                "speed_mbps": None, "elapsed_seconds": 0, "eta_seconds": None, "current_file": None}

            sc, sk, fc, sbytes = 0, 0, 0, 0
            start = asyncio.get_event_loop().time()

            for fi in all_files:
                if self._cancel: break
                _current_progress["current"] += 1; _current_progress["current_file"] = fi['name']
                result = await self._process_one(fi, org, profile)
                _current_progress["current_bytes"] = sbytes + (result['size'] if result['status']==FileSyncStatus.SYNCED else 0)

                async with async_session() as db:
                    sf = SyncFile(history_id=history_id, filename=fi['name'],
                                  relative_path=fi.get('relative_path'), source_path=fi['path'],
                                  dest_path=result.get('dest_path'), file_size=fi['size'],
                                  checksum=result.get('checksum'), status=result['status'],
                                  error_message=result.get('error'))
                    db.add(sf)
                    if result['status'] == FileSyncStatus.SYNCED:
                        sc += 1; sbytes += fi['size']
                        if result.get('checksum'):
                            db.add(FileRegistry(file_hash=result['checksum'],
                                original_path=fi['path'], file_size=fi['size'],
                                dest_path=result.get('dest_path','')))
                    elif result['status'] == FileSyncStatus.SKIPPED: sk += 1
                    else: fc += 1
                    await db.commit()

                elapsed = asyncio.get_event_loop().time() - start
                _current_progress["elapsed_seconds"] = int(elapsed)
                if elapsed > 0 and sbytes > 0:
                    spd = sbytes / elapsed; _current_progress["speed_mbps"] = round(spd/1024/1024, 1)
                    rem = _current_progress["total_bytes"] - sbytes
                    _current_progress["eta_seconds"] = int(rem/spd) if spd > 0 else None
                await ws_manager.broadcast({"type":"sync_progress",**{k:v for k,v in _current_progress.items()}})
                if progress_cb: await progress_cb(_current_progress)

            async with async_session() as db:
                h = await db.get(SyncHistory, history_id)
                if h:
                    h.status = SyncStatus.CANCELLED if self._cancel else SyncStatus.COMPLETED
                    h.synced_files=sc; h.skipped_files=sk; h.failed_files=fc; h.synced_bytes=sbytes
                    h.completed_at = func.now(); await db.commit()

            await ws_manager.broadcast({"type":"sync_completed","history_id":history_id,
                "status":"cancelled" if self._cancel else "success",
                "synced":sc,"skipped":sk,"failed":fc})
            return history_id
        finally:
            _is_running = False; _current_progress = {}

    async def _process_one(self, fi, org, profile):
        result = {"status": FileSyncStatus.FAILED, "error": None, "dest_path": None, "checksum": None, "size": fi['size']}
        try:
            fh = await calculate_sha256(fi['path']); result['checksum'] = fh
            async with async_session() as db:
                if await DedupService(db).is_duplicate(fh):
                    return {**result, "status": FileSyncStatus.SKIPPED, "error": "已同步过"}
            dp = org.get_dest_path(fi['name'], fi['mtime']); result['dest_path'] = dp
            if profile.copy_mode == "move": await self._move(fi['path'], dp)
            else: await self._copy(fi['path'], dp)
            if profile.checksum_verify and not await verify_checksum(dp, fh):
                os.remove(dp); return {**result, "status": FileSyncStatus.FAILED, "error": "校验和不匹配"}
            for sc in detect_sidecar_files(fi['path']):
                await self._copy(sc, os.path.join(os.path.dirname(dp), sanitize_filename(os.path.basename(sc))))
            try: await generate_thumbnail(dp)
            except: pass
            return {**result, "status": FileSyncStatus.SYNCED}
        except Exception as e:
            return {**result, "status": FileSyncStatus.FAILED, "error": str(e)}

    def cancel(self): self._cancel = True
