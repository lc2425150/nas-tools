import unittest

from sync.browser_sync import merge_ip_list, trusted_ip_config_selector


class BrowserSyncHelperTests(unittest.TestCase):
    def test_trusted_ip_selector_targets_card_not_generic_config(self):
        selector = trusted_ip_config_selector()
        self.assertIn("企业可信IP", selector)
        self.assertIn("配置", selector)
        self.assertNotEqual(selector, ".apiApp_mod_card_operationLink")

    def test_merge_ip_list_appends_once_with_semicolon_separator(self):
        merged = merge_ip_list("115.210.135.188; 115.212.205.88", "115.212.205.89")
        self.assertEqual(merged, "115.210.135.188;115.212.205.88;115.212.205.89")
        self.assertEqual(merge_ip_list(merged, "115.212.205.89"), merged)


if __name__ == "__main__":
    unittest.main()
