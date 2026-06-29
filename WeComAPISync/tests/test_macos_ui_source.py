from pathlib import Path
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class MacOSUISourceTests(unittest.TestCase):
    def test_app_forces_light_appearance_for_dark_mode_readability(self):
        source = (PROJECT_ROOT / "app" / "main.m").read_text(encoding="utf-8")
        self.assertIn("NSAppearanceNameAqua", source)
        self.assertIn("setAppearance:", source)

    def test_status_bar_uses_template_icon_not_text_label(self):
        source = (PROJECT_ROOT / "app" / "main.m").read_text(encoding="utf-8")
        self.assertIn("StatusIconTemplate", source)
        self.assertIn("statusIcon.template = YES", source)
        self.assertNotIn('self.statusItem.button.title = @"IP"', source)

    def test_default_interval_is_thirty_minutes(self):
        source = (PROJECT_ROOT / "app" / "main.m").read_text(encoding="utf-8")
        self.assertIn("#define CHECK_INTERVAL    1800", source)
        config = (PROJECT_ROOT / "sync" / "config.py").read_text(encoding="utf-8")
        self.assertIn("DEFAULT_INTERVAL = 1800", config)

    def test_network_changes_trigger_debounced_sync(self):
        source = (PROJECT_ROOT / "app" / "main.m").read_text(encoding="utf-8")
        self.assertIn("#import <SystemConfiguration/SystemConfiguration.h>", source)
        self.assertIn("SCDynamicStoreCreate", source)
        self.assertIn("SCDynamicStoreSetNotificationKeys", source)
        self.assertIn("networkChangeTimer", source)
        self.assertIn("@selector(syncAfterNetworkChange)", source)


if __name__ == "__main__":
    unittest.main()
