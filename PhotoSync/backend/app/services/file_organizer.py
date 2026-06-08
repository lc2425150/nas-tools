import os, datetime
from typing import Optional
from app.services.file_scanner import sanitize_filename

class FileOrganizer:
    def __init__(self, destination: str, sync_mode: str = "date", custom_template: Optional[str] = None):
        self.destination = destination; self.sync_mode = sync_mode; self.custom_template = custom_template

    def get_dest_path(self, filename: str, mtime: float, exif_date: Optional[str] = None, camera_model: Optional[str] = None) -> str:
        safe = sanitize_filename(filename)
        dt = self._get_dt(mtime, exif_date)
        if self.sync_mode == "original":
            return os.path.join(self.destination, safe)
        elif self.sync_mode == "custom" and self.custom_template:
            return self._apply_template(safe, dt, camera_model)
        return os.path.join(self.destination, dt.strftime("%Y"), dt.strftime("%m"), dt.strftime("%d"), safe)

    def _get_dt(self, mtime: float, exif_date: Optional[str] = None) -> datetime.datetime:
        if exif_date:
            try: return datetime.datetime.strptime(exif_date, "%Y:%m:%d %H:%M:%S")
            except: pass
        return datetime.datetime.fromtimestamp(mtime)

    def _apply_template(self, fn: str, dt: datetime.datetime, camera: Optional[str] = None) -> str:
        t = self.custom_template or "{Date:YYYY}/{Date:MM}/{FileName}"
        m = {"{FileName}": fn, "{Camera}": camera or "Unknown",
             "{Date:YYYY}": dt.strftime("%Y"), "{Date:MM}": dt.strftime("%m"),
             "{Date:DD}": dt.strftime("%d"), "{Year}": dt.strftime("%Y"),
             "{Month}": dt.strftime("%m"), "{Day}": dt.strftime("%d")}
        for k, v in m.items(): t = t.replace(k, v)
        return os.path.join(self.destination, t)
