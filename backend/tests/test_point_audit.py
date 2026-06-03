from validation.point_audit import parse_audit_removals


def test_parse_audit_removals():
    raw = {
        "removals": [
            {
                "series_idx": 0,
                "point_idx": 3,
                "pixel_x": 100.5,
                "pixel_y": 200.0,
                "reason": "位于图例区域",
                "confidence": 0.92,
            }
        ]
    }
    items = parse_audit_removals(raw)
    assert len(items) == 1
    assert items[0].series_idx == 0
    assert items[0].point_idx == 3
    assert "图例" in items[0].reason


def test_parse_audit_empty():
    assert parse_audit_removals({}) == []
    assert parse_audit_removals({"removals": []}) == []
