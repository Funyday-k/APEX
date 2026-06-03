from vlm.parser import parse_json_response


def test_parse_json_plain():
    data = parse_json_response('{"title": "Test", "legend": ["A"]}')
    assert data["title"] == "Test"
    assert data["legend"] == ["A"]


def test_parse_json_markdown_fence():
    text = '```json\n{"x_label": "Time"}\n```'
    data = parse_json_response(text)
    assert data["x_label"] == "Time"
