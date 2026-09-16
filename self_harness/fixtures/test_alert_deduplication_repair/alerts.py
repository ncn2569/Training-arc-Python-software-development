def should_emit(cache, alert, now_seconds, window_seconds=300):
    fingerprint = f"{alert['service']}:{alert['message']}"
    previous = cache.get(fingerprint)
    if previous and now_seconds - previous <= window_seconds:
        return False
    cache[fingerprint] = now_seconds
    return True
