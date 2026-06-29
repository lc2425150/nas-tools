import io
import sys
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from sync import wecom_sync


class WeComSyncCLITests(unittest.TestCase):
    def test_once_does_not_force_browser_verification(self):
        captured = {}

        def fake_sync_once(force=False):
            captured["force"] = force
            return wecom_sync.result(True, "127.0.0.1", "unchanged", "unchanged", verified=True)

        with patch.object(sys, "argv", ["wecom_sync", "--once"]), patch.object(wecom_sync, "sync_once", fake_sync_once), redirect_stdout(io.StringIO()):
            self.assertEqual(wecom_sync.main(), 0)

        self.assertFalse(captured["force"])

    def test_force_flag_forces_browser_verification(self):
        captured = {}

        def fake_sync_once(force=False):
            captured["force"] = force
            return wecom_sync.result(True, "127.0.0.1", "verified", "verified", verified=True)

        with patch.object(sys, "argv", ["wecom_sync", "--once", "--force"]), patch.object(wecom_sync, "sync_once", fake_sync_once), redirect_stdout(io.StringIO()):
            self.assertEqual(wecom_sync.main(), 0)

        self.assertTrue(captured["force"])


if __name__ == "__main__":
    unittest.main()
