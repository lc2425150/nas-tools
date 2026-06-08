import pytest
from app.services.dedup import DedupService

class TestDedup:
    async def test_register_new(self, db_session):
        s = DedupService(db_session)
        r = await s.register_file("abc123", "/c/1.arw", 100, "/p/1.arw")
        assert r.file_hash == "abc123"

    async def test_detect_dup(self, db_session):
        s = DedupService(db_session)
        await s.register_file("abc123", "/c/1.arw", 100, "/p/1.arw")
        assert await s.is_duplicate("abc123") is True
        assert await s.is_duplicate("xyz") is False
