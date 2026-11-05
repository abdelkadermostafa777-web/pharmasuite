"""Creates pwa/data/elements.json for the offline app. Run once from the backend folder (uses RDKit)."""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from app import periodic  # noqa: E402

out = []
for z in range(1, 119):
    row, col = periodic.position(z)
    out.append({
        "z": z,
        "symbol": periodic.PT.GetElementSymbol(z),
        "row": row,
        "col": col,
        "category": periodic.category(z),
        "period": periodic.period_of(z),
        "weight": round(periodic.PT.GetAtomicWeight(z), 4),
        "valence": periodic.PT.GetDefaultValence(z),
        "outer": periodic.PT.GetNOuterElecs(z),
        "shells": periodic.shells(z),
    })

folder = os.path.join(HERE, "pwa", "data")
os.makedirs(folder, exist_ok=True)
with open(os.path.join(folder, "elements.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False)
print("elements.json written to", folder)
