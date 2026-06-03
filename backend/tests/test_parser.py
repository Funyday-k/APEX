from vlm.parser import parse_json_response


def test_parse_json_plain():
    data = parse_json_response('{"title": "Test", "legend": ["A"]}')
    assert data["title"] == "Test"
    assert data["legend"] == ["A"]


def test_parse_json_markdown_fence():
    text = '```json\n{"x_label": "Time"}\n```'
    data = parse_json_response(text)
    assert data["x_label"] == "Time"


def test_parse_region_segment_json():
    text = '{"coord_space":"pixel","regions":[{"kind":"legend","bbox":{"x0":1,"y0":2,"x1":3,"y1":4}}]}'
    data = parse_json_response(text)
    assert data["regions"][0]["kind"] == "legend"


def test_parse_point_audit_json():
    text = '{"removals":[{"series_idx":0,"point_idx":1,"reason":"legend","confidence":0.9}]}'
    data = parse_json_response(text)
    assert len(data["removals"]) == 1
