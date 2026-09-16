"""Aggregate device readings into fixed telemetry windows."""


def aggregate_readings(readings, *, window_seconds=60):
    """Return per-device summaries for valid readings.

    Invalid records are ignored.  ``window_seconds`` must be positive.
    """
    if window_seconds <= 0:
        raise ValueError("window_seconds must be positive")

    buckets = {}
    for reading in readings:
        try:
            device_id = str(reading["device_id"])
            timestamp = int(reading["timestamp"])
            value = float(reading["value"])
        except (KeyError, TypeError, ValueError):
            continue
        if not device_id:
            continue

        # BUG: rounding makes readings near the end of a window spill into the
        # next one, and can merge data from opposite sides of a boundary.
        window_start = round(timestamp / window_seconds) * window_seconds
        bucket = buckets.setdefault((device_id, window_start), [])
        bucket.append(value)

    return [
        {
            "device_id": device_id,
            "window_start": window_start,
            "count": len(values),
            "average": round(sum(values) / len(values), 2),
        }
        for (device_id, window_start), values in sorted(buckets.items())
    ]
