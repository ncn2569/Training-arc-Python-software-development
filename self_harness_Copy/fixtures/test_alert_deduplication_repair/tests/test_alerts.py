import unittest

from alerts import should_emit


class AlertTests(unittest.TestCase):
    alert = {"service": "billing", "severity": "critical", "message": " disk   full "}

    def test_window_boundary_and_normalized_fingerprint(self):
        cache = {}
        self.assertTrue(should_emit(cache, self.alert, 100))
        self.assertFalse(should_emit(cache, {**self.alert, "message": "disk full"}, 399))
        self.assertTrue(should_emit(cache, self.alert, 400))

    def test_severity_and_clock_rollback(self):
        cache = {}
        self.assertTrue(should_emit(cache, self.alert, 1000))
        self.assertTrue(should_emit(cache, {**self.alert, "severity": "warning"}, 1001))
        self.assertTrue(should_emit(cache, self.alert, 900))


if __name__ == "__main__":
    unittest.main()
