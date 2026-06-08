import pytest
from app.services.card_detector import CardDetector

def test_scan_detects_card(mock_card_dir, tmp_path):
    d = CardDetector(scan_paths=[str(tmp_path)])
    cards = d.scan()
    assert len(cards) == 1
    assert cards[0].label == "SDCARD"

def test_scan_empty_on_nonexistent():
    assert len(CardDetector(scan_paths=["/nonexistent"]).scan()) == 0

def test_file_scanner_filters(mock_card_dir):
    from app.services.file_scanner import scan_files
    r = list(scan_files(mock_card_dir, {"photos": True, "videos": False}))
    assert len(r) == 1 and r[0]["name"] == "DSC_0002.JPG"

def test_ignored_files_skipped(mock_card_dir):
    from app.services.file_scanner import scan_files
    assert not any("._DSC" in f["name"] for f in scan_files(mock_card_dir))

def test_sanitize():
    from app.services.file_scanner import sanitize_filename
    assert sanitize_filename("a:b?.txt") == "a_b_.txt"
    assert sanitize_filename("  f.txt ") == "f.txt"
