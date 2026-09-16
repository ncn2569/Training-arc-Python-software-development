"""Small, dependency-free feature-flag rollout evaluator."""

import hashlib


def _bucket(key, user_id):
    digest = hashlib.sha256(f"{key}:{user_id}".encode("utf-8")).hexdigest()
    return int(digest[:8], 16) % 100


def is_enabled(flag, user, now_epoch):
    """Return whether this flag should be enabled for one user at one instant."""
    if not isinstance(flag, dict) or not isinstance(user, dict):
        return False
    if flag.get("enabled") is not True:
        return False

    # BUG: malformed window values crash, and the end boundary is accidentally
    # exclusive even though rollout windows are supposed to include both ends.
    start = flag.get("starts_at")
    end = flag.get("ends_at")
    if start is not None and now_epoch < int(start):
        return False
    if end is not None and now_epoch >= int(end):
        return False

    user_id = user.get("id")
    if user_id in flag.get("allow_users", []):
        return True

    countries = flag.get("countries")
    if countries and user.get("country") not in countries:
        return False

    percentage = flag.get("percentage", 0)
    return _bucket(flag.get("key", ""), user_id) < percentage
