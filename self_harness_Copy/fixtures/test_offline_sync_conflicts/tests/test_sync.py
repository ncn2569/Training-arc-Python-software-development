import copy
import unittest

from sync import merge_notes


class SyncTests(unittest.TestCase):
    def test_revision_and_tombstone_win(self):
        local = {"n": {"revision": 2, "updated_at": "2026-09-01T09:00", "device": "z", "text": "old"}}
        remote = {"n": {"revision": 3, "updated_at": "2026-08-01T09:00", "device": "a", "deleted": True}}
        self.assertTrue(merge_notes(local, remote)["n"]["deleted"])

    def test_ties_are_deterministic_and_inputs_unchanged(self):
        local = {"n": {"revision": 4, "updated_at": "2026-09-02", "device": "tablet", "text": "L"}}
        remote = {"n": {"revision": 4, "updated_at": "2026-09-02", "device": "phone", "text": "R"}, "r": {"revision": 1, "updated_at": "x", "device": "r"}}
        before = copy.deepcopy((local, remote))
        merged = merge_notes(local, remote)
        self.assertEqual(merged["n"]["device"], "phone")
        self.assertIn("r", merged)
        self.assertEqual((local, remote), before)


if __name__ == "__main__":
    unittest.main()
