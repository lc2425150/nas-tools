import pytest
from app.models import SyncProfile
from app.services.sync_engine import SyncEngine
from app.services.file_scanner import scan_files

class TestSyncEngine:
    async def test_dry_run(self, db_session, mock_card_dir):
        p = SyncProfile(name="Test", destination="/tmp/ps", sync_mode="date")
        db_session.add(p); await db_session.commit(); await db_session.refresh(p)
        r = await SyncEngine().dry_run(p, mock_card_dir)
        assert r["total_files"] > 0

    async def test_scan_files(self, mock_card_dir):
        f = list(scan_files(mock_card_dir))
        assert len(f) > 0 and all(fi['size'] > 0 for fi in f)

    async def test_sanitize(self):
        from app.services.file_scanner import sanitize_filename
        assert sanitize_filename("n.jpg") == "n.jpg"
        assert len(sanitize_filename("a"*300)) <= 255
