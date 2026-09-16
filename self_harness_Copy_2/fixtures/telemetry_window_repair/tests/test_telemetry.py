from telemetry import aggregate_readings


def test_exact_boundary_starts_a_new_window_and_result_is_sorted():
    readings = [
        {"device_id": "sensor-b", "timestamp": 61, "value": 4},
        {"device_id": "sensor-a", "timestamp": 119, "value": 11},
        {"device_id": "sensor-a", "timestamp": 61, "value": 9},
        {"device_id": "sensor-a", "timestamp": 120, "value": 20},
    ]

    assert aggregate_readings(readings) == [
        {"device_id": "sensor-a", "window_start": 60, "count": 2, "average": 10.0},
        {"device_id": "sensor-a", "window_start": 120, "count": 1, "average": 20.0},
        {"device_id": "sensor-b", "window_start": 60, "count": 1, "average": 4.0},
    ]


def test_malformed_readings_are_ignored_and_average_is_rounded():
    readings = [
        {"device_id": "sensor-a", "timestamp": 1, "value": 1},
        {"device_id": "sensor-a", "timestamp": 2, "value": 2},
        {"device_id": "sensor-a", "timestamp": 3, "value": 2},
        {"device_id": "sensor-a", "timestamp": "bad", "value": 9},
        {"device_id": "", "timestamp": 3, "value": 9},
        {"timestamp": 3, "value": 9},
    ]

    assert aggregate_readings(readings, window_seconds=10) == [
        {"device_id": "sensor-a", "window_start": 0, "count": 3, "average": 1.67}
    ]
