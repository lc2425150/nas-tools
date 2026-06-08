import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.database import Base

@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite://", connect_args={"check_same_thread": False})
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session = async_sessionmaker(engine, class_=AsyncSession)()
    try: yield session
    finally: await session.close(); await engine.dispose()

@pytest.fixture
def mock_card_dir(tmp_path):
    card = tmp_path / "SDCARD"; card.mkdir()
    dcim = card / "DCIM"; dcim.mkdir()
    (dcim / "DSC_0001.ARW").write_bytes(b"mock_raw_001")
    (dcim / "DSC_0002.JPG").write_bytes(b"mock_jpg_002")
    (dcim / "DSC_0003.MP4").write_bytes(b"mock_vid_003")
    (dcim / "._DSC_0001.ARW").write_bytes(b"macos_meta")
    return str(card)
