import unittest
from pathlib import Path

from archive_paths import archive_target


class ArchivePathTests(unittest.TestCase):
    def test_allows_nested_relative_member(self):
        self.assertEqual(archive_target("/tmp/archive", "images/icon.svg"), Path("/tmp/archive/images/icon.svg"))

    def test_rejects_escape_and_absolute_members(self):
        for member in ("../secret.txt", "/etc/passwd", "", "nested/../../secret.txt"):
            with self.assertRaises(ValueError):
                archive_target("/tmp/archive", member)


if __name__ == "__main__":
    unittest.main()
