from webhooks.validators import constant_time_equals

def test_constant_time_equals():
    assert constant_time_equals("abc", "abc") is True
    assert constant_time_equals("abc", "abd") is False