import copy
import unittest

from inventory import reserve


class InventoryTests(unittest.TestCase):
    def test_respects_prior_reservations_without_mutating_inputs(self):
        stock = {"widget": 10}
        reserved = {"widget": 8}
        before = copy.deepcopy((stock, reserved))
        with self.assertRaises(ValueError):
            reserve(stock, reserved, "widget", 3)
        self.assertEqual((stock, reserved), before)
        result = reserve(stock, reserved, "widget", 2)
        self.assertEqual(result, {"widget": 10})
        self.assertEqual((stock, reserved), before)

    def test_validates_sku_and_quantity_type(self):
        with self.assertRaises(KeyError):
            reserve({"widget": 1}, {}, "missing", 1)
        for bad in (0, -1, True, 1.5):
            with self.assertRaises(ValueError):
                reserve({"widget": 2}, {}, "widget", bad)


if __name__ == "__main__":
    unittest.main()
