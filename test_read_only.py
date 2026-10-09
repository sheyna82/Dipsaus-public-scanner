"""Read-only connection tests must not mutate runtime state or send alerts."""
import unittest
from unittest.mock import MagicMock, patch
import safe_runner


class ReadOnlyTests(unittest.TestCase):
    def test_prealert_read_only_does_not_save_or_notify(self):
        state_store = MagicMock()
        state_store.load.return_value = {}
        with patch("sys.argv", ["safe_runner.py", "prealert", "--read-only"]), \
             patch.object(safe_runner, "hydrate"), \
             patch.object(safe_runner, "PrivateStore", return_value=state_store), \
             patch.object(safe_runner, "run") as scan, \
             patch.object(safe_runner.Path, "read_text", return_value='{"rows": []}'), \
             patch.object(safe_runner, "notify") as notify:
            safe_runner.main()
        self.assertEqual(scan.call_count, 3)
        state_store.save.assert_not_called()
        state_store.require_exclusive_sender.assert_not_called()
        notify.assert_not_called()

    def test_read_only_rejects_live_and_other_modes_before_hydration(self):
        for args in (["prealert", "--read-only", "--live"], ["eu", "--read-only"], ["us", "--read-only"]):
            with self.subTest(args=args), \
                 patch("sys.argv", ["safe_runner.py", *args]), \
                 patch.object(safe_runner, "hydrate") as hydrate:
                with self.assertRaisesRegex(RuntimeError, "READ_ONLY_MODE_INVALID"):
                    safe_runner.main()
                hydrate.assert_not_called()


if __name__ == "__main__":
    unittest.main()
