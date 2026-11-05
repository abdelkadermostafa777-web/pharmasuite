"""Pharmaceutical formulation checks. Offline and simplified for teaching; confirm with references."""

# excipient key -> (role, typical min %, typical max % w/w)
EXCIPIENTS = {
    "lactose": ("diluent", 20, 90),
    "mcc": ("diluent", 20, 90),
    "sorbitol": ("diluent", 10, 60),
    "starch": ("disintegrant", 3, 15),
    "sodium_starch_glycolate": ("disintegrant", 2, 8),
    "povidone": ("binder", 1, 5),
    "hpmc": ("binder", 2, 10),
    "mg_stearate": ("lubricant", 0.5, 2),
    "talc": ("glidant", 1, 5),
    "silica": ("glidant", 0.1, 1),
    "citric_acid": ("acidulant", 0.1, 1),
    "sodium_benzoate": ("preservative", 0.05, 0.5),
}

# (API tag, excipient key, message key, severity)
RULES = [
    ("primary_amine", "lactose", "rule_maillard", "high"),
    ("ester", "mg_stearate", "rule_ester_alkaline", "medium"),
]

ADVICE = {
    "ester": "advice_ester",
    "primary_amine": "advice_amine",
    "oxidizable": "advice_oxidizable",
}


def check(api_tags, components):
    """components: list of (key, percent). Returns a dict with total, ranges, alerts and advice."""
    total = sum(p for _, p in components)
    ranges = []
    for key, pct in components:
        if key in EXCIPIENTS:
            _, lo, hi = EXCIPIENTS[key]
            status = "ok" if lo <= pct <= hi else ("low" if pct < lo else "high")
            ranges.append((key, pct, lo, hi, status))
    keys = {k for k, _ in components}
    alerts = [(sev, code, exc) for tag, exc, code, sev in RULES
              if tag in api_tags and exc in keys]
    advice = [ADVICE[t] for t in api_tags if t in ADVICE]
    return {
        "total": round(total, 4),
        "total_ok": abs(total - 100) < 0.01,
        "ranges": ranges,
        "alerts": alerts,
        "advice": advice,
    }
