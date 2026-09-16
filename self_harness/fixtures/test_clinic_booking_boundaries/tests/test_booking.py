import unittest

from booking import can_book


class BookingTests(unittest.TestCase):
    existing = [{"provider": "dr-lee", "start": 540, "end": 570}]

    def test_adjacent_slot_is_valid(self):
        self.assertTrue(can_book(self.existing, "dr-lee", 570, 600))

    def test_other_provider_is_independent(self):
        self.assertTrue(can_book(self.existing, "dr-khan", 550, 560))

    def test_overlap_and_empty_interval_are_rejected(self):
        self.assertFalse(can_book(self.existing, "dr-lee", 560, 580))
        with self.assertRaises(ValueError):
            can_book(self.existing, "dr-lee", 600, 600)


if __name__ == "__main__":
    unittest.main()
