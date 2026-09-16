from flags import _bucket, is_enabled


def test_allow_users_win_over_percentage_but_not_disabled_or_window():
    flag = {
        "key": "new-checkout",
        "enabled": True,
        "starts_at": 100,
        "ends_at": 200,
        "allow_users": ["vip"],
        "countries": ["VN"],
        "percentage": 0,
    }
    assert is_enabled(flag, {"id": "vip", "country": "VN"}, 100) is True
    assert is_enabled(flag, {"id": "vip", "country": "VN"}, 200) is True
    assert is_enabled(flag, {"id": "vip", "country": "VN"}, 99) is False
    assert is_enabled({**flag, "enabled": False}, {"id": "vip", "country": "VN"}, 150) is False


def test_country_precedes_rollout_and_bucket_is_stable():
    flag = {"key": "beta", "enabled": True, "countries": ["VN"], "percentage": 100}
    assert is_enabled(flag, {"id": "other", "country": "US"}, 150) is False
    assert is_enabled(flag, {"id": "other", "country": "VN"}, 150) is True
    assert _bucket("beta", "other") == _bucket("beta", "other")


def test_malformed_optional_values_fail_closed():
    flag = {"key": "beta", "enabled": True, "starts_at": "tomorrow", "percentage": "all"}
    assert is_enabled(flag, {"id": "u", "country": "VN"}, 150) is False
