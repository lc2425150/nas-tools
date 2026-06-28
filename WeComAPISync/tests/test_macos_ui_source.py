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


if __name__ == "__main__":
    unittest.main()
