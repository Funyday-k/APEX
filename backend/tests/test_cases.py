from extractors.cases import build_cases, normalize_case


def test_build_cases_from_semantics_legend():
    sem = {
        "legend": ["Theory", "Simulation"],
        "series_colors": {"Theory": "#00aa00", "Simulation": "#0000ff"},
    }
    cases = build_cases(sem, {}, 400, 300)
    assert len(cases) == 2
    assert cases[0]["label"] == "Theory"
    assert cases[1]["color_hex"].startswith("#")


def test_build_cases_from_vlm():
    vlm = {
        "cases": [
            {
                "label": "Sim",
                "color_hex": "#1122ff",
                "representation": "scatter",
                "sub_bbox": {"x0": 0.1, "y0": 0.2, "x1": 0.9, "y1": 0.8},
            }
        ]
    }
    cases = build_cases({}, vlm, 500, 400)
    assert len(cases) == 1
    assert cases[0]["representation"] == "scatter"
    bb = cases[0].get("sub_bbox")
    assert bb and bb["x1"] > bb["x0"]


def test_normalize_case_representation():
    c = normalize_case({"label": "x", "representation": "invalid", "color_hex": "#fff"}, 100, 100)
    assert c["representation"] == "scatter"
