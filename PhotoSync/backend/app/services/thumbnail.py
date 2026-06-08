import os, hashlib, asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Optional
from PIL import Image
from io import BytesIO

_executor = ThreadPoolExecutor(max_workers=2)
THUMBNAIL_DIR = "/app/data/thumbnails"

def _get_jpeg_preview(raw_path: str) -> Optional[bytes]:
    try:
        with open(raw_path, 'rb') as f:
            data = f.read()
        idx = data.find(b'\xff\xd8\xff')
        if idx >= 0:
            eoi = data.find(b'\xff\xd9', idx)
            if eoi >= 0: return data[idx:eoi+2]
    except: pass
    return None

def _generate_thumb(image_path: str, thumb_path: str, size: int = 300) -> bool:
    try:
        ext = os.path.splitext(image_path)[1].lower()
        raw_exts = {'.arw','.cr2','.cr3','.nef','.raf','.dng','.orf','.rw2'}
        if ext in raw_exts:
            preview = _get_jpeg_preview(image_path)
            if preview: img = Image.open(BytesIO(preview))
            else: return False
        else:
            img = Image.open(image_path)
        img.thumbnail((size, size), Image.LANCZOS)
        os.makedirs(os.path.dirname(thumb_path), exist_ok=True)
        if img.mode in ('RGBA','P'): img = img.convert('RGB')
        img.save(thumb_path, 'JPEG', quality=85)
        return True
    except: return False

async def generate_thumbnail(image_path: str, thumbnail_dir: str = THUMBNAIL_DIR, size: int = 300) -> Optional[str]:
    fh = hashlib.sha256(image_path.encode()).hexdigest()[:16]
    tp = os.path.join(thumbnail_dir, f"{fh}.jpg")
    if os.path.exists(tp): return tp
    loop = asyncio.get_event_loop()
    return tp if await loop.run_in_executor(_executor, _generate_thumb, image_path, tp, size) else None
