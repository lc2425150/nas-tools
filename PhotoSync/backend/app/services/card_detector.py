import os, asyncio
from typing import List, Optional, Callable
from dataclasses import dataclass
from app.services.file_scanner import IGNORED_FILES

@dataclass
class DetectedCard:
    path: str; label: str
    total_space: Optional[int] = None; used_space: Optional[int] = None

class CardDetector:
    def __init__(self, scan_paths: List[str], poll_interval: int = 5):
        self.scan_paths = scan_paths; self.poll_interval = poll_interval
        self._previous_cards: set = set()
        self._on_insert: List[Callable] = []
        self._on_remove: List[Callable] = []

    def on_insert(self, cb): self._on_insert.append(cb)
    def on_remove(self, cb): self._on_remove.append(cb)

    def scan(self) -> List[DetectedCard]:
        cards = []
        for base_path in self.scan_paths:
            if not os.path.isdir(base_path): continue
            try:
                for entry in os.listdir(base_path):
                    ep = os.path.join(base_path, entry)
                    if os.path.isdir(ep) and entry.lower() not in IGNORED_FILES and not entry.startswith('.'):
                        stats = None
                        try:
                            vfs = os.statvfs(ep)
                            total = vfs.f_frsize * vfs.f_blocks
                            free = vfs.f_frsize * vfs.f_bfree
                            stats = (total, total - free)
                        except: pass
                        cards.append(DetectedCard(path=ep, label=entry,
                            total_space=stats[0] if stats else None,
                            used_space=stats[1] if stats else None))
            except PermissionError: continue
        return cards

    async def watch_loop(self):
        while True:
            current = {c.path for c in self.scan()}
            for path in current - self._previous_cards:
                for cb in self._on_insert:
                    await cb(DetectedCard(path=path, label=os.path.basename(path)))
            for path in self._previous_cards - current:
                for cb in self._on_remove:
                    await cb(path)
            self._previous_cards = current
            await asyncio.sleep(self.poll_interval)
