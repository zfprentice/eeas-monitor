from regions import detect_regions


def test_detects_named_region():
    assert "Eastern Europe & Caucasus" in detect_regions("EU statement on Ukraine ceasefire talks")


def test_detects_multiple_regions():
    regions = detect_regions("Joint statement on Gaza and Ukraine reconstruction")
    assert "Middle East & North Africa" in regions
    assert "Eastern Europe & Caucasus" in regions


def test_falls_back_to_global():
    assert detect_regions("Speech on EU digital policy") == ["Global / Multilateral"]


def test_word_boundary_avoids_false_positive():
    # "Niger" is a keyword; "Nigeria" should not falsely match it as a substring.
    regions = detect_regions("EU cooperation with Nigeria on trade")
    assert "Sub-Saharan Africa" not in regions
