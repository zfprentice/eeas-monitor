import re

REGION_KEYWORDS = {
    "Eastern Europe & Caucasus": [
        "ukraine",
        "russia",
        "belarus",
        "moldova",
        "georgia",
        "armenia",
        "azerbaijan",
        "caucasus",
    ],
    "Middle East & North Africa": [
        "israel",
        "gaza",
        "palestine",
        "lebanon",
        "syria",
        "iran",
        "yemen",
        "iraq",
        "libya",
        "egypt",
    ],
    "Western Balkans": [
        "kosovo",
        "serbia",
        "bosnia",
        "herzegovina",
        "montenegro",
        "albania",
        "north macedonia",
    ],
    "Indo-Pacific & Asia": [
        "china",
        "taiwan",
        "myanmar",
        "india",
        "pakistan",
        "afghanistan",
        "indo-pacific",
    ],
    "Sub-Saharan Africa": ["sudan", "sahel", "mali", "niger", "drc", "somalia", "ethiopia"],
    "Americas": ["venezuela", "cuba", "haiti", "latin america"],
}


def detect_regions(text):
    text_lower = text.lower()
    matched = []
    for region, keywords in REGION_KEYWORDS.items():
        if any(re.search(rf"\b{re.escape(k)}\b", text_lower) for k in keywords):
            matched.append(region)
    return matched if matched else ["Global / Multilateral"]
