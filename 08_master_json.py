import json
import os
from datetime import datetime

os.makedirs("data/json", exist_ok=True)

# ── LOAD ALL JSON FILES ───────────────────────────────────────────
with open("data/json/overview.json",   "r") as f: overview   = json.load(f)
with open("data/json/production.json", "r") as f: production = json.load(f)
with open("data/json/reserves.json",   "r") as f: reserves   = json.load(f)
with open("data/json/investment.json", "r") as f: investment = json.load(f)

# ── BUILD MASTER JSON ─────────────────────────────────────────────
master = {
    "meta": {
        "title":        "Norway Oil & Gas Dashboard",
        "source":       "SODIR — Norwegian Offshore Directorate",
        "source_url":   "https://factpages.sodir.no",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "default_year": overview["present_year"],
        "available_years": [int(y) for y in sorted(overview["annual_production"].keys())],
        "partial_years":   [1971, 2026]
    },
    "overview":   overview,
    "production": production,
    "reserves":   reserves,
    "investment": investment
}

# ── EXPORT ────────────────────────────────────────────────────────
output_path = "data/json/master.json"
with open(output_path, "w") as f:
    json.dump(master, f, indent=2)

# ── SUMMARY ───────────────────────────────────────────────────────
size_kb = round(os.path.getsize(output_path) / 1024, 1)

print(f"✓ master.json generado")
print(f"  Size: {size_kb} KB")
print(f"  Sections: overview / production / reserves / investment")
print(f"  Generated: {master['meta']['generated_at']}")
print(f"  Default year: {master['meta']['default_year']}")
print(f"  Available years: {master['meta']['available_years'][0]} → {master['meta']['available_years'][-1]}")