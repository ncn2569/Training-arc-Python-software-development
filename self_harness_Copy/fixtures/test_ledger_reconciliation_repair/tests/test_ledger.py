import unittest

from ledger import reconcile


class LedgerTests(unittest.TestCase):
    def test_deduplicates_and_sorts_accounts(self):
        rows = [
            {"id": "a", "account": " travel ", "amount_cents": -125},
            {"id": "a", "account": "travel", "amount_cents": -125},
            {"id": "b", "account": "cash", "amount_cents": 500},
        ]
        self.assertEqual(reconcile(rows), {"balances": {"cash": 500, "travel": -125}, "total_cents": 375})

    def test_rejects_bad_values(self):
        with self.assertRaises(ValueError):
            reconcile([{"id": "x", "account": "   ", "amount_cents": 1}])
        with self.assertRaises(ValueError):
            reconcile([{"id": "x", "account": "cash", "amount_cents": True}])


if __name__ == "__main__":
    unittest.main()
