from calibration.tick_parse import parse_tick_label, resolve_tick_value


def test_parse_scientific_notation():
    assert parse_tick_label("10^{-2}") == 1e-2
    assert parse_tick_label("1e-3") == 1e-3
    assert parse_tick_label("2x10^4") == 2e4
    assert parse_tick_label("10^26") == 1e26


def test_resolve_prefers_label_when_value_wrong():
    v = resolve_tick_value(1e27, "10^26")
    assert v is not None
    assert abs(v - 1e26) < 1e20
